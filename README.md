# Adamsy Free TV

Adamsy Free TV is a standalone Windows desktop app for browsing and streaming free-to-air live TV channels with `python-vlc` and VLC media player.

## What is included

- Desktop GUI in `app/tv_gui.py`
- App entry point in `tv_main.py`
- Channel updater in `tv_updater.py`
- Starter channel catalog in `tv_channels.json`
- Windows launcher and setup scripts in `scripts/`
- PyInstaller build config in `VirtualTV.spec`
- Phase-1 web preview in `web/`
- Shared backend API in `backend/`

## Requirements

- Windows
- Python 3.11+ for source builds
- VLC media player installed from [videolan.org](https://www.videolan.org/vlc/)

## Run from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tv_main.py
```

## Start the phase-1 backend API

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tv_main.py --serve-api --host 127.0.0.1 --port 8000
```

Or on Windows:

```powershell
.\scripts\start_api.ps1
```

Then open:

```text
http://127.0.0.1:8000/
```

That root page serves the browser preview from `web/`, backed by the same channel data as the desktop app.

The web preview now includes:

- stronger browser playback handling for HLS streams
- favorites and recent-play history stored in the browser
- a lightweight admin refresh flow that can sync `tv_channels.json` from the UI

Phase 1 endpoints:

- `GET /health`
- `GET /channels`
- `GET /channels/categories`
- `GET /channels/countries`
- `GET /channels/source`
- `GET /admin/refresh`
- `POST /admin/refresh`

Example:

```text
http://127.0.0.1:8000/channels?search=news&category=News&limit=25
```

This API reuses the same `tv_channels.json` file as the desktop app, which is the first step toward a shared desktop + web architecture.

### Optional admin protection

Set `ADAMSY_ADMIN_TOKEN` before starting the API if you want the web refresh action to require a token:

```powershell
$env:ADAMSY_ADMIN_TOKEN = "choose-a-secret"
python tv_main.py --serve-api
```

## Refresh channels from source

```powershell
python tv_main.py --refresh-channels --limit 700 --verify-live
```

## Build the standalone exe

```powershell
.\scripts\build_tv_exe.ps1
```

The build output is:

- `dist\VirtualTV.exe`
- `dist\tv_channels.json`

The packaged app stores channel edits next to the executable, so the `dist` folder is the deployable desktop bundle.

## Build the Windows installer

Install Inno Setup 6 or 7 first, then run:

```powershell
.\scripts\build_windows_installer.ps1
```

The installer output is:

- `release\Adamsy-Free-TV-Setup-1.0.0.exe`

The installer:

- installs the app for the current Windows user under `LocalAppData\Programs\Adamsy Free TV`
- creates desktop and Start menu shortcuts
- registers an uninstaller in Windows
- preserves an existing `tv_channels.json` during reinstall or upgrade

## Optional Windows setup

- `start_tv_app.bat` launches the packaged exe when available, then falls back to Python.
- `stop_tv_app.bat` stops the app.
- `.\scripts\install_tv_shortcut.ps1` creates a desktop shortcut.
- `.\scripts\install_tv_stop_shortcut.ps1` creates a stop shortcut.
- `.\scripts\register_tv_weekly_update.ps1` registers a weekly channel refresh task.
- `.\scripts\repair_tv_setup.ps1` recreates shortcuts and the weekly refresh task.

## Notes

- `python-vlc` still needs the VLC desktop runtime installed on the machine.
- The in-app "Refresh Channels" action downloads channels from the public iptv-org playlist and overwrites `tv_channels.json`.
- Share the single installer file in `release\` with other Windows users; they do not need Python.

## Prepare for Vercel

The project now includes:

- `index.py` as the Vercel Python entry point
- `vercel.json` to route all web and API requests through the FastAPI app

This keeps the web preview and API together for a first deployment path.

Typical flow:

```powershell
vercel
vercel --prod
```

If you deploy with admin refresh enabled, set `ADAMSY_ADMIN_TOKEN` in the Vercel project environment variables so the sync action stays protected.
