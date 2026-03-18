"""Main logic for Advanced Downloader integration."""

from __future__ import annotations

import os
import sys
import aiofiles
import aiohttp
import logging
from pathlib import Path
from typing import Optional

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import aiohttp_client, config_validation as cv
from homeassistant.helpers.start import async_at_start
from homeassistant.exceptions import HomeAssistantError

# Handle asyncio.timeout availability (Python 3.11+)
if sys.version_info >= (3, 11):
    from asyncio import timeout as asyncio_timeout
else:
    from async_timeout import timeout as asyncio_timeout  # type: ignore[import-not-found]

from .const import (
    DOMAIN,
    CONF_DOWNLOAD_DIR,
    CONF_OVERWRITE,
    CONF_DELETE_FILE_PATH,
    CONF_DELETE_DIR_PATH,
    DEFAULT_OVERWRITE,
    SERVICE_DOWNLOAD_FILE,
    SERVICE_DELETE_FILE,
    SERVICE_DELETE_DIRECTORY,
    ATTR_URL,
    ATTR_SUBDIR,
    ATTR_FILENAME,
    ATTR_OVERWRITE,
    ATTR_TIMEOUT,
    ATTR_PATH,
    ATTR_RESIZE_ENABLED,
    ATTR_RESIZE_WIDTH,
    ATTR_RESIZE_HEIGHT,
    ATTR_TARGET_ASPECT_RATIO,
    PROCESS_DOWNLOADING,
    PROCESS_RESIZING,
    PROCESS_FILE_DELETING,
    PROCESS_DIR_DELETING,
)

from .video_utils import (
    sanitize_filename,
    guess_filename_from_url,
    ensure_within_base,
)

from custom_components.video_tools.video_processor import VideoProcessor

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor"]

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Advanced Downloader from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )

    from homeassistant.components import persistent_notification as _pn  # noqa: PLC0415

    # Warn if the core "downloader" integration is loaded (configured via
    # configuration.yaml). Advanced Downloader is a full superset of its
    # functionality; having both active serves no purpose and may cause confusion.
    #
    # The check is deferred until HA has fully started so that all YAML-configured
    # integrations have had a chance to register their services. We test for a
    # registered service rather than inspecting hass.config.components, because
    # hass.config.components may contain "downloader" even when the integration is
    # not explicitly configured (e.g. available built-in integrations are scanned
    # at boot). A service is only registered after a successful async_setup(), so
    # this is a reliable indicator that downloader: is present in configuration.yaml.
    @callback
    def _check_downloader_conflict(_: HomeAssistant) -> None:
        if "downloader" in hass.services.async_services():
            _LOGGER.warning(
                "The built-in 'downloader' integration is active alongside Advanced "
                "Downloader. Remove 'downloader:' from your configuration.yaml and "
                "restart Home Assistant to avoid redundancy."
            )
            _pn.async_create(
                hass,
                (
                    "The built-in **Downloader** integration is loaded in your "
                    "configuration. **Advanced Downloader** provides a full superset of "
                    "its functionality.\n\n"
                    "To avoid redundancy, remove `downloader:` from your "
                    "`configuration.yaml` and restart Home Assistant."
                ),
                title="Advanced Downloader: Remove core Downloader integration",
                notification_id="advanced_downloader_core_downloader_conflict",
            )

    async_at_start(hass, _check_downloader_conflict)

    # Warn if Video Tools is also configured as a standalone integration.
    # Its code must remain installed (Advanced Downloader imports from it), but
    # the standalone config entry should be removed to avoid duplicate processing.
    if hass.config_entries.async_entries("video_tools"):
        _LOGGER.warning(
            "Video Tools is configured as a standalone integration alongside "
            "Advanced Downloader. Remove its config entry from Settings → Devices & "
            "Services to avoid duplicate video processing. Keep the HACS package "
            "installed — Advanced Downloader still requires its code."
        )
        _pn.async_create(
            hass,
            (
                "**Video Tools** is installed as a standalone integration, but it "
                "is now used as a dependency by **Advanced Downloader**.\n\n"
                "To avoid duplicate video processing, please remove the Video Tools "
                "configuration entry:\n"
                "**Settings → Devices & Services → Video Tools → Delete**\n\n"
                "⚠️ Do **not** uninstall the HACS package — Advanced Downloader still "
                "requires its code."
            ),
            title="Advanced Downloader: Remove standalone Video Tools",
            notification_id="advanced_downloader_video_tools_conflict",
        )

    video_processor = VideoProcessor()

    @callback
    def _get_config() -> tuple[Path, bool]:
        download_dir = Path(
            entry.options.get(CONF_DOWNLOAD_DIR, entry.data.get(CONF_DOWNLOAD_DIR))
        )
        overwrite = bool(
            entry.options.get(CONF_OVERWRITE, entry.data.get(CONF_OVERWRITE, DEFAULT_OVERWRITE))
        )
        return (download_dir, overwrite)

    # ----------------------------------------------------------
    # 📥 Download file
    # ----------------------------------------------------------

    async def _async_download(call: ServiceCall) -> None:
        url: str = call.data[ATTR_URL]
        subdir: Optional[str] = call.data.get(ATTR_SUBDIR)
        filename: Optional[str] = call.data.get(ATTR_FILENAME)
        overwrite: Optional[bool] = call.data.get(ATTR_OVERWRITE)
        timeout_sec: int = int(call.data.get(ATTR_TIMEOUT, 300))

        resize_enabled: bool = call.data.get(ATTR_RESIZE_ENABLED, False)
        resize_width: int = int(call.data.get(ATTR_RESIZE_WIDTH, 640))
        resize_height: int = int(call.data.get(ATTR_RESIZE_HEIGHT, 360))
        target_aspect_ratio: Optional[float] = call.data.get(ATTR_TARGET_ASPECT_RATIO)

        base_dir, default_overwrite = _get_config()
        base_dir = base_dir.resolve()

        dest_dir = base_dir / sanitize_filename(subdir or "")
        ensure_within_base(base_dir, dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        final_name = sanitize_filename(filename) if filename else guess_filename_from_url(url)
        dest_path = (dest_dir / final_name).resolve()
        ensure_within_base(base_dir, dest_path)

        do_overwrite = default_overwrite if overwrite is None else bool(overwrite)

        sensor = hass.data[DOMAIN]["status_sensor"]
        sensor.start_process(PROCESS_DOWNLOADING)

        session: aiohttp.ClientSession = aiohttp_client.async_get_clientsession(hass)
        tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")

        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

        try:
            async with asyncio_timeout(timeout_sec):
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"HTTP error {resp.status}: {url}")
                    async with aiofiles.open(tmp_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(1024 * 64):
                            if chunk:
                                await f.write(chunk)

            if dest_path.exists() and not do_overwrite:
                raise HomeAssistantError(f"File exists and overwrite is False: {dest_path}")

            os.replace(tmp_path, dest_path)

            hass.bus.async_fire("advanced_downloader_download_completed", {
                "url": url, "path": str(dest_path)
            })

            # Delegate video processing (aspect normalization, thumbnail embedding,
            # optional resize) to Video Tools
            if dest_path.suffix.lower() in VIDEO_EXTENSIONS:
                if resize_enabled:
                    sensor.start_process(PROCESS_RESIZING)
                try:
                    process_kwargs: dict = {
                        "video_path": str(dest_path),
                        "overwrite": True,
                        "normalize_aspect": True,
                        "generate_thumbnail": True,
                        "resize_width": resize_width if resize_enabled else None,
                        "resize_height": resize_height if resize_enabled else None,
                    }
                    if target_aspect_ratio is not None:
                        process_kwargs["target_aspect_ratio"] = target_aspect_ratio
                    process_result = await video_processor.process_video(**process_kwargs)
                    operations = process_result.get("operations", {})

                    if operations.get("normalize_aspect"):
                        hass.bus.async_fire("advanced_downloader_aspect_normalized", {
                            "path": str(dest_path)
                        })

                    if operations.get("embed_thumbnail"):
                        hass.bus.async_fire("advanced_downloader_thumbnail_embedded", {
                            "path": str(dest_path)
                        })

                    if resize_enabled:
                        if operations.get("resize"):
                            hass.bus.async_fire("advanced_downloader_resize_completed", {
                                "path": str(dest_path),
                                "width": resize_width,
                                "height": resize_height,
                            })
                        elif "resize" in operations and not operations["resize"]:
                            hass.bus.async_fire("advanced_downloader_resize_failed", {
                                "path": str(dest_path)
                            })

                    temp_files = process_result.get("temp_files", [])
                    if temp_files:
                        await video_processor.cleanup_temp_files(temp_files)
                finally:
                    if resize_enabled:
                        sensor.end_process(PROCESS_RESIZING)

            sensor.set_last_job("success")
            hass.bus.async_fire("advanced_downloader_job_completed", {
                "url": url, "path": str(dest_path)
            })

        except Exception as err:
            _LOGGER.error("Download failed: %s", err)
            sensor.set_last_job("failed")
            hass.bus.async_fire("advanced_downloader_download_failed", {
                "url": url, "error": str(err)
            })
        finally:
            sensor.end_process(PROCESS_DOWNLOADING)

    # ----------------------------------------------------------
    # 🗑️ Delete file / directory
    # ----------------------------------------------------------

    async def _async_delete_file(call: ServiceCall) -> None:
        path_str: str | None = call.data.get(ATTR_PATH)
        if not path_str:
            path_str = entry.options.get(CONF_DELETE_FILE_PATH, "")
        if not path_str:
            raise HomeAssistantError("No path provided")

        path = Path(path_str).resolve()
        base_dir, _ = _get_config()
        ensure_within_base(base_dir, path)

        sensor = hass.data[DOMAIN]["status_sensor"]
        sensor.start_process(PROCESS_FILE_DELETING)
        try:
            if path.is_file():
                path.unlink()
        finally:
            sensor.end_process(PROCESS_FILE_DELETING)

    async def _async_delete_directory(call: ServiceCall) -> None:
        dir_str: str | None = call.data.get(ATTR_PATH)
        if not dir_str:
            dir_str = entry.options.get(CONF_DELETE_DIR_PATH, "")
        if not dir_str:
            raise HomeAssistantError("No path provided")

        dir_path = Path(dir_str).resolve()
        base_dir, _ = _get_config()
        ensure_within_base(base_dir, dir_path)

        sensor = hass.data[DOMAIN]["status_sensor"]
        sensor.start_process(PROCESS_DIR_DELETING)
        try:
            if dir_path.is_dir():
                for file in dir_path.iterdir():
                    if file.is_file():
                        file.unlink()
        finally:
            sensor.end_process(PROCESS_DIR_DELETING)

    # ----------------------------------------------------------
    # 🔧 Register services
    # ----------------------------------------------------------

    hass.services.async_register(
        DOMAIN,
        SERVICE_DOWNLOAD_FILE,
        _async_download,
        schema=vol.Schema({
            vol.Required(ATTR_URL): cv.url,
            vol.Optional(ATTR_SUBDIR): cv.string,
            vol.Optional(ATTR_FILENAME): cv.string,
            vol.Optional(ATTR_OVERWRITE): cv.boolean,
            vol.Optional(ATTR_TIMEOUT): vol.Coerce(int),
            vol.Optional(ATTR_RESIZE_ENABLED): cv.boolean,
            vol.Optional(ATTR_RESIZE_WIDTH): vol.Coerce(int),
            vol.Optional(ATTR_RESIZE_HEIGHT): vol.Coerce(int),
            vol.Optional(ATTR_TARGET_ASPECT_RATIO): vol.Coerce(float),
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_FILE,
        _async_delete_file,
        schema=vol.Schema({vol.Optional(ATTR_PATH): cv.string}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_DIRECTORY,
        _async_delete_directory,
        schema=vol.Schema({vol.Optional(ATTR_PATH): cv.string}),
    )

    return True
