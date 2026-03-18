# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.6] - 2026-03-18

### Fixed
- **Blocking `open()` call inside the event loop:** replaced the synchronous `open(tmp_path, "wb")` used during chunk-writing with `aiofiles.open()` so that file I/O is no longer performed on the event-loop thread. This resolves the `homeassistant.util.loop` warning *"Detected blocking call to open … inside the event loop"*. `aiofiles>=23.1.0` has been added as a runtime requirement.

---

## [1.2.5] - 2026-03-11

### Changed
- **Rebranding: "Video Normalizer" renamed to "Video Tools".** All references to the `video_normalizer` integration (dependency declaration, import path, conflict-detection logic, persistent notification messages, and documentation) have been updated to `video_tools`.

---

## [1.2.4] - 2026-03-11

### Fixed
- **`AttributeError: 'HomeAssistant' object has no attribute 'async_at_start'`:** replaced the invalid `hass.async_at_start()` call with the correct `homeassistant.helpers.start.async_at_start(hass, callback)` helper. This caused the entire integration setup to fail, making all services (`advanced_downloader.download_file`, etc.) unavailable.

---

## [1.2.3] - 2026-03-11

### Fixed
- **False-positive core Downloader conflict notification:** the check that detects whether the built-in `downloader` integration is active was incorrectly using `hass.config.components`, which can contain `"downloader"` even when `downloader:` is not present in `configuration.yaml` (HA may register available built-in integrations at boot). The check now inspects `hass.services.async_services()` instead, which only lists domains with registered services — a reliable indicator that `async_setup()` was actually called for that integration. Additionally, the check is now deferred until after HA has fully started (via `hass.async_at_start()`) to guarantee all YAML-configured integrations have had a chance to register their services before the conflict detection runs.

---

## [1.2.2] - 2026-03-10

### Fixed
- Renamed brand images directory from `custom_components/advanced_downloader/brands/` to `custom_components/advanced_downloader/brand/` to match the standard Home Assistant brands directory name.

### Removed
- Automatic release GitHub Action (`.github/workflows/release.yml`). Releases are now created manually.

---

## [1.2.1] - 2026-03-10

### Added
- **Core `downloader` integration conflict detection:** if the built-in `downloader` integration is loaded (i.e. `downloader:` is present in `configuration.yaml`), a persistent notification now appears at startup. The notification explains that Advanced Downloader is a full superset and guides the user to remove `downloader:` from `configuration.yaml` and restart Home Assistant.
- **`target_aspect_ratio` parameter for `download_file`:** the service now accepts an optional `target_aspect_ratio` (float, e.g. `1.777` for 16:9) that is forwarded to Video Normalizer's `VideoProcessor.process_video` during aspect normalisation. This replaces the equivalent parameter that was previously only available via the standalone `video_normalizer.normalize_video` service.
- **`last_job` attribute on `sensor.advanced_downloader_status`:** the sensor now exposes a `last_job` attribute (`null`, `success`, or `failed`) that reflects the outcome of the most recent download job, providing parity with the `last_job` attribute previously available on `sensor.video_normalizer_status`.
- **Automation migration guide** added to README, showing step-by-step how to replace automations that combined the core `downloader` integration with the standalone Video Normalizer integration.

### Fixed
- The Video Normalizer conflict notification import (`persistent_notification`) is now hoisted and shared between both conflict checks, removing a redundant in-block import.

---

## [1.2.0] - 2026-03-10

> ⚠️ **Breaking change:** The integration domain has changed from `media_downloader` to `advanced_downloader`. Update any automations, scripts, or templates that reference `media_downloader.*` services or `media_downloader_*` events.

### Added
- **[Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) is now a required dependency.** All video post-processing (aspect ratio normalization, thumbnail generation/embedding, and optional resizing) is delegated to Video Normalizer's `VideoProcessor`, eliminating duplicated logic.
- **Startup conflict detection:** if Video Normalizer is also configured as a standalone integration, a persistent Home Assistant notification is created to guide the user to remove that config entry (while keeping the HACS package installed, since Advanced Downloader still requires its code).
- `issue_tracker` field added to `manifest.json`.
- Brand images (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`) added to `custom_components/advanced_downloader/brand/`.

### Changed
- **Integration renamed** from *Media Downloader* to *Advanced Downloader*.
- **Domain changed** from `media_downloader` to `advanced_downloader`.
  - Integration folder: `custom_components/advanced_downloader/`
  - All service names: `advanced_downloader.download_file`, `advanced_downloader.delete_file`, `advanced_downloader.delete_files_in_directory`
  - All event names: `advanced_downloader_download_completed`, `advanced_downloader_download_failed`, `advanced_downloader_aspect_normalized`, `advanced_downloader_thumbnail_embedded`, `advanced_downloader_resize_completed`, `advanced_downloader_resize_failed`, `advanced_downloader_job_completed`
  - Status sensor entity: `sensor.advanced_downloader_status`
- `video_utils.py` simplified to path/filename utilities only (`sanitize_filename`, `ensure_within_base`, `guess_filename_from_url`). All video-processing functions removed in favour of the Video Normalizer dependency.

---

## [1.1.6] - 2025-12-XX

### Fixed
- Improved error logging for subprocess failures.
- Fixed shell escaping issues in ffmpeg/ffprobe command calls.
- Fixed subprocess timeout handling to prevent hanging processes.

---

## [1.1.5] - 2025-12-06

### Fixed
- **Fixed `async_timeout` deprecation warning:** added Python 3.11+ compatibility with automatic fallback to `async_timeout` for older versions, ensuring compatibility across different Home Assistant installations.
- **Fixed `UnboundLocalError` in `normalize_video_aspect()`:** resolved potential crash where `tmp_file` variable could be referenced before assignment in the exception handler.
- **Fixed `UnboundLocalError` in `embed_thumbnail()`:** improved exception handling to properly define temporary file paths before cleanup operations.

---

## [1.1.4] - 2025-11-20

### Improved
- All blocking post-processing (normalization, thumbnail embedding, resize, and dimension detection) now runs in an executor via `hass.async_add_executor_job` to avoid blocking the Home Assistant event loop.
- Status sensor lifecycle hardened: the sensor now properly subscribes and unsubscribes to bus events and is guaranteed to be registered in `hass.data` before services are called.
- `async_will_remove_from_hass` removes bus listeners to avoid callback leaks on unload.

---

## [1.1.3] - 2025-11-15

### Added
- Integration option to configure the global default download timeout via the UI. The global `download_timeout` is overridable per-service-call with the `timeout` parameter.
- New namespaced event `media_downloader_job_interrupted` emitted alongside the existing `job_interrupted` event for clearer integration-scoped event naming.
- Unit tests covering timeout behaviour and the `sensor.media_downloader_status` `last_job` attribute added to CI.

### Improved
- Blocking post-processing steps (normalization, thumbnail, resize) now run in a thread executor to avoid blocking the event loop.

---

## [1.1.2] - 2025-11-14

### Added
- Configurable timeout for the download workflow: `media_downloader.download_file` accepts a `timeout` field (seconds, default 300). The timeout applies to the entire workflow (download + post-processing + move/replace).
- New event `job_interrupted` emitted when a job does not complete within the configured timeout. Payload: `{ "job": { "url": <url>, "path": <path> } }`.
- Sensor enhancement: `sensor.media_downloader_status` now exposes a new attribute `last_job` with values `null`, `"done"`, or `"interrupted"`.

---

## [1.1.1] - 2025-10-14

### Added
- New logo and icon images.

---

## [1.1.0] - 2025-10-04

### Added
- New video post-processing pipeline for Telegram compatibility:
  - Automatic **aspect ratio normalization** using `setsar=1,setdar=width/height`.
  - Automatic **thumbnail generation and embedding** for all downloaded videos.
  - New helper module `video_utils.py` with `normalize_video_aspect()`, `embed_thumbnail()`, `resize_video()`, and `get_video_dimensions()`.
- New events: `media_downloader_aspect_normalized`, `media_downloader_thumbnail_embedded`.

---

## [1.0.10] - 2025-09-30

### Added
- Automatic thumbnail embedding for all downloaded videos using `ffmpeg`. Runs regardless of whether resizing is enabled.

### Fixed
- Prevents Telegram and other clients from generating square or distorted thumbnails by always embedding a correct thumbnail.

---

## [1.0.9] - 2025-09-25

### Fixed
- Corrected an issue where some videos appeared square in Telegram despite having correct pixel dimensions. The resize process now explicitly forces `scale=width:height`, `setsar=1`, and `setdar=width/height` to preserve the correct display aspect ratio.

---

## [1.0.8] - 2025-09-24

### Changed
- Improved robustness of video dimension detection: now uses `ffprobe` with JSON output as the primary method, with `ffmpeg -i` as a fallback. Added logging for troubleshooting when detection fails.

---

## [1.0.7] - 2025-09-19

### Added
- New event `media_downloader_job_completed` fired when a full job (download + optional resize) has finished successfully. Fields: `url`, `path`, `resized` (boolean).

---

## [1.0.6] - 2025-09-12

### Added
- New events: `media_downloader_download_completed` (fields: `url`, `path`, `resized`), `media_downloader_download_failed` (fields: `url`, `error`), `media_downloader_resize_completed` (fields: `path`, `width`, `height`), `media_downloader_resize_failed` (fields: `path`, `width`, `height`).
- Added `icon.png` and `logo.png`.

---

## [1.0.5] - 2025-09-06

### Added
- Persistent sensor `sensor.media_downloader_status` via `sensor.py`.
  - State: `idle` or `working`.
  - Attributes: `last_changed`, `subprocess`, `active_processes`.
  - Supports chained processes: remains `working` until all subprocesses complete.

### Removed
- Event-based status notifications replaced by the persistent sensor.

---

## [1.0.4] - 2025-09-03

### Added
- New service fields for `media_downloader.download_file`: `resize_enabled` (boolean), `resize_width` (int), `resize_height` (int).
- Downloaded videos are resized if `resize_enabled` is true and dimensions differ from the target.
- `media_downloader_download_completed` event now includes a `resized` boolean field.

---

## [1.0.3] - 2025-09-03

### Added
- Enhanced `services.yaml` with `name` and `description` metadata for all service fields, improving the Home Assistant automation editor UI.

### Fixed
- Resolved issue where `delete_file` and `delete_files_in_directory` services did not respond correctly when no `path` field was provided.

---

## [1.0.2] - 2025-08-23

### Added
- New service `media_downloader.delete_file`: deletes a specific file by `path` or a default path configured in the UI.
- New service `media_downloader.delete_files_in_directory`: deletes all files inside a directory by `path` or a default path configured in the UI.
- New events: `media_downloader_delete_completed`, `media_downloader_delete_directory_completed`.
- UI OptionsFlow support: configure default file path and directory path for delete services.

---

## [1.0.1] - 2025-08-23

### Added
- New service `media_downloader.delete_file` (path-based deletion).
- New service `media_downloader.delete_files_in_directory`.
- Events: `media_downloader_delete_completed`, `media_downloader_delete_directory_completed`.

---

## [1.0.0] - 2025-08-22

### Added
- Initial release of **Media Downloader** as a custom Home Assistant integration.
- UI-based configuration: base download directory and overwrite policy.
- Service `media_downloader.download_file` with optional subdirectories, custom filenames, overwrite control, and per-download timeout.
- Events: `media_downloader_download_started`, `media_downloader_download_completed` (with `success` and `error` fields).

[1.2.6]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.6...v1.2.0
[1.1.6]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.10...v1.1.0
[1.0.10]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Geek-MD/Advanced_Downloader/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Geek-MD/Advanced_Downloader/releases/tag/v1.0.0
