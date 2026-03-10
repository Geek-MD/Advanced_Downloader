"""Video utilities for Advanced Downloader integration."""

from __future__ import annotations

import re
from pathlib import Path
from homeassistant.exceptions import HomeAssistantError


# --------------------------------------------------------
# 🧩 Generic path and filename utilities
# --------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """Clean and sanitize a filename for safe filesystem usage."""
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|\r\n\t]", "_", name)
    return name or "downloaded_file"


def ensure_within_base(base: Path, target: Path) -> None:
    """Ensure a path is inside the allowed base directory."""
    try:
        target.relative_to(base)
    except Exception as err:
        raise HomeAssistantError(f"Path {target} is outside of base directory {base}") from err


def guess_filename_from_url(url: str) -> str:
    """Guess a safe filename from a URL."""
    tail = url.split("?")[0].rstrip("/").split("/")[-1]
    return sanitize_filename(tail or "downloaded_file")
