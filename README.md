[![Geek-MD - Advanced Downloader](https://img.shields.io/static/v1?label=Geek-MD&message=Advanced%20Downloader&color=blue&logo=github)](https://github.com/Geek-MD/Advanced_Downloader)
[![Stars](https://img.shields.io/github/stars/Geek-MD/Advanced_Downloader?style=social)](https://github.com/Geek-MD/Advanced_Downloader)
[![Forks](https://img.shields.io/github/forks/Geek-MD/Advanced_Downloader?style=social)](https://github.com/Geek-MD/Advanced_Downloader)

[![GitHub Release](https://img.shields.io/github/release/Geek-MD/Advanced_Downloader?include_prereleases&sort=semver&color=blue)](https://github.com/Geek-MD/Advanced_Downloader/releases)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/Geek-MD/Advanced_Downloader/blob/main/LICENSE)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom%20Repository-blue)](https://hacs.xyz/)

[![Ruff + Mypy + Hassfest](https://github.com/Geek-MD/Advanced_Downloader/actions/workflows/validate.yml/badge.svg)](https://github.com/Geek-MD/Advanced_Downloader/actions/workflows/validate.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

<img width="200" height="200" alt="image" src="https://github.com/Geek-MD/Advanced_Downloader/blob/main/logo.png?raw=true" />

# Advanced Downloader

**Advanced Downloader** is a custom Home Assistant integration that greatly extends file downloading capabilities beyond the built-in `downloader` integration. It downloads, normalizes, and manages media files directly from Home Assistant through simple services — and leverages [Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) as a dependency for all video processing.

> **Domain:** `advanced_downloader`  
> Advanced Downloader is a full superset of the core `downloader` integration. If you have `downloader:` in your `configuration.yaml`, a persistent notification will appear at startup reminding you to remove it. After removing it, restart Home Assistant.

---

## ✨ Features
- Download files from any URL directly into a configured folder.
- Optional subdirectories and custom filenames.
- Overwrite policy (default or per-call).
- Delete a single file or all files in a directory via services.
- **Automatic aspect ratio normalization** for downloaded videos (powered by Video Normalizer).
- **Automatic thumbnail generation and embedding** for correct video previews in Telegram and mobile players.
- Optional video resizing (width/height) if dimensions differ.
- Persistent status sensor (`sensor.advanced_downloader_status`) to track operations (`idle` / `working`).
- Event support for all processes: download, normalize, thumbnail, resize, and job completion.
- Fully compatible with automations and scripts in Home Assistant.

---

## 🧩 Dependencies
- [Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) — required for video processing (aspect normalization, thumbnail embedding, resizing). Install it via HACS before adding Advanced Downloader.

---

## 🧰 Requirements
- Home Assistant 2024.1.0 or newer.
- A valid writable directory for storing media files (e.g., `/media` or `/config/media`).
- `ffmpeg` and `ffprobe` must be installed and available in the system path.
- [Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) installed as a HACS integration.

---

## ⚙️ Installation

### Option 1: Manual Installation
1. Install [Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) first.
2. Download the latest release from [GitHub](https://github.com/Geek-MD/Advanced_Downloader/releases).
3. Copy the folder `advanced_downloader` into:
   ```
   /config/custom_components/advanced_downloader/
   ```
4. Restart Home Assistant.
5. Add the integration from **Settings → Devices & Services → Add Integration → Advanced Downloader**.

---

### Option 2: HACS Installation
1. Install [Video Normalizer](https://github.com/Geek-MD/Video_Normalizer) via HACS first.
2. Go to **HACS → Integrations → Custom Repositories**.
3. Add the repository URL:
   ```
   https://github.com/Geek-MD/Advanced_Downloader
   ```
4. Select **Integration** as category.
5. Install **Advanced Downloader** from HACS.
6. Restart Home Assistant.
7. Add the integration from **Settings → Devices & Services → Add Integration → Advanced Downloader**.

---

## ⚙️ Configuration
When adding the integration:
- **Base download directory** → Absolute path where files will be saved.
- **Overwrite** → Whether existing files should be replaced by default.
- **Default file delete path** → Optional fallback for the `delete_file` service.
- **Default directory delete path** → Optional fallback for the `delete_files_in_directory` service.

You can modify these settings later via the integration options.

---

## 🧩 Services

### 1. `advanced_downloader.download_file`
Downloads a file from a given URL.
For video files, the following steps are always performed via Video Normalizer:
1. **Aspect ratio normalization** (`setsar=1,setdar=width/height`).
2. **Thumbnail generation and embedding** (ensures correct previews in Telegram and other platforms).
3. **Optional resize** if `resize_enabled: true`.

#### Service Data
| Field | Required | Description |
|--------|-----------|-------------|
| `url` | yes | File URL to download. |
| `subdir` | no | Optional subdirectory under the base directory. |
| `filename` | no | Optional filename (auto-detected if omitted). |
| `overwrite` | no | Override default overwrite policy. |
| `timeout` | no | Timeout in seconds (default 300). |
| `resize_enabled` | no | If true, resize the video when dimensions mismatch. |
| `resize_width` | no | Target width for resize (default 640). |
| `resize_height` | no | Target height for resize (default 360). |
| `target_aspect_ratio` | no | Target display aspect ratio as decimal (e.g. `1.777` for 16:9). Passed to Video Normalizer during normalization. Omit to let Video Normalizer infer from the video's own dimensions. |

#### Example:
```yaml
- service: advanced_downloader.download_file
  data:
    url: "https://example.com/video.mp4"
    subdir: "ring"
    filename: "video.mp4"
    resize_enabled: true
    resize_width: 640
    resize_height: 360
```

---

### 2. `advanced_downloader.delete_file`
Deletes a single file.
If no `path` is provided, the default UI-configured path will be used.

| Field | Required | Description |
|--------|-----------|-------------|
| `path` | no | Absolute path of the file to delete. |

---

### 3. `advanced_downloader.delete_files_in_directory`
Deletes all files inside a directory.
If no `path` is provided, the default UI-configured directory will be used.

| Field | Required | Description |
|--------|-----------|-------------|
| `path` | no | Absolute path of the directory to clear. |

---

## 📊 Sensor

The integration provides the persistent entity:
**`sensor.advanced_downloader_status`**

### State
- `idle` → No active processes.
- `working` → At least one active process (download, normalize, thumbnail, resize, or delete).

### Attributes
| Attribute | Description |
|------------|-------------|
| `last_changed` | Datetime when state last changed. |
| `subprocess` | Current subprocess name (`downloading`, `resizing`, `file_deleting`, `dir_deleting`). |
| `active_processes` | List of all currently active subprocesses. |
| `last_job` | Outcome of the last download job: `null` (no job yet), `success`, or `failed`. |

---

## 📢 Events

| Event Name | Triggered When | Data Fields |
|-------------|----------------|--------------|
| `advanced_downloader_download_completed` | Download finished successfully. | `url`, `path` |
| `advanced_downloader_aspect_normalized` | Video aspect normalized successfully. | `path` |
| `advanced_downloader_thumbnail_embedded` | Thumbnail successfully generated and embedded. | `path` |
| `advanced_downloader_resize_completed` | Video resized successfully. | `path`, `width`, `height` |
| `advanced_downloader_resize_failed` | Resize process failed. | `path` |
| `advanced_downloader_download_failed` | Download failed. | `url`, `error` |
| `advanced_downloader_job_completed` | Entire workflow completed. | `url`, `path` |

---

## 🤖 Example Automation

```yaml
- service: advanced_downloader.download_file
  data:
    url: "https://example.com/camera/video.mp4"
    subdir: "ring"
    filename: "ring_front.mp4"
    resize_enabled: true
    resize_width: 640
    resize_height: 360

- wait_for_trigger:
    - platform: event
      event_type: advanced_downloader_job_completed
  timeout: "00:05:00"
  continue_on_timeout: true

- service: telegram_bot.send_video
  data:
    target: -123456789
    video: "{{ wait.trigger.event.data.path }}"
    caption: "New video from Ring (normalized with thumbnail)."
```

---

## 🔄 Migration Guide

### Migrating from `downloader` + `video_normalizer` automations

If you previously had automations that combined the core **Downloader** integration
(`downloader.download_file`) with the standalone **Video Normalizer** integration
(`video_normalizer.normalize_video`), follow this guide to migrate them to
**Advanced Downloader**, which performs both operations in a single service call.

#### Before (two integrations)

```yaml
# 1. Download the file using the core Downloader integration
- action: downloader.download_file
  data:
    url: "{{ url }}"
    subdir: ring
    filename: ring.mp4
    overwrite: true

# 2. Wait for the download event fired by the core Downloader
- wait_for_trigger:
    - trigger: event
      event_type: downloader_download_completed
  continue_on_timeout: false

# 3. Normalize the video using the standalone Video Normalizer integration
- action: video_normalizer.normalize_video
  data:
    overwrite: true
    normalize_aspect: true
    generate_thumbnail: true
    input_file_path: /media/ring/ring.mp4
    target_aspect_ratio: 1.777

# 4. Wait for Video Normalizer to finish (poll the sensor)
- if:
    - condition: state
      entity_id: sensor.video_normalizer_status
      state: idle
  then: []
  else:
    - wait_for_trigger:
        - trigger: state
          entity_id: sensor.video_normalizer_status
          to: idle

# 5. Act on outcome via last_job attribute
- if:
    - condition: template
      value_template: >-
        {{ state_attr('sensor.video_normalizer_status', 'last_job') in
           ['success', 'skipped'] }}
  then:
    - action: telegram_bot.send_video
      data:
        file: /media/ring/ring.mp4
        caption: Se detectó movimiento en Entrada.
  else:
    - action: telegram_bot.send_message
      data:
        message: Se detectó movimiento en Entrada.
```

#### After (Advanced Downloader only)

```yaml
# 1. Download + normalize in one call
- action: advanced_downloader.download_file
  data:
    url: "{{ url }}"
    subdir: ring
    filename: ring.mp4
    overwrite: true
    target_aspect_ratio: 1.777   # forwarded to Video Normalizer

# 2. Wait for job completion (success) or failure
- wait_for_trigger:
    - trigger: event
      event_type: advanced_downloader_job_completed
    - trigger: event
      event_type: advanced_downloader_download_failed
  continue_on_timeout: false

# 3. Act on outcome via the trigger event type
- if:
    - condition: template
      value_template: >-
        {{ wait.trigger.event.event_type ==
           'advanced_downloader_job_completed' }}
  then:
    - action: telegram_bot.send_video
      data:
        file: /media/ring/ring.mp4
        caption: Se detectó movimiento en Entrada.
  else:
    - action: telegram_bot.send_message
      data:
        message: Se detectó movimiento en Entrada.
```

Alternatively, you can check the `last_job` attribute on
`sensor.advanced_downloader_status` (values: `success` or `failed`) the same
way you previously checked `sensor.video_normalizer_status`:

```yaml
- if:
    - condition: template
      value_template: >-
        {{ state_attr('sensor.advanced_downloader_status', 'last_job') ==
           'success' }}
  then: ...
```

#### Key mapping

| Old | New |
|-----|-----|
| `downloader.download_file` | `advanced_downloader.download_file` |
| `video_normalizer.normalize_video` | *(built-in — no separate call needed)* |
| `downloader_download_completed` event + poll `sensor.video_normalizer_status` → idle | `advanced_downloader_job_completed` event (success) or `advanced_downloader_download_failed` event (failure) |
| `sensor.video_normalizer_status` state | `sensor.advanced_downloader_status` state |
| `sensor.video_normalizer_status` `last_job` | `sensor.advanced_downloader_status` `last_job` |

---

## 🧾 License
MIT License. See [LICENSE](LICENSE) for details.

---

## 📋 Changelog
See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

<div align="center">

💻 **Proudly developed with GitHub Copilot** 🚀

</div>

