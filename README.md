# Adamsy Free TV

Windows desktop and browser experience for free-to-air live TV — channel catalog, HTML5 streaming, favorites, and a shared FastAPI channel API.

[![Portfolio](https://img.shields.io/badge/Adamu_Abubakar-adamu.tech-0f766e?style=flat-square)](https://adamu.tech)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## Overview

Adamsy Free TV bundles a Windows IPTV client with a lightweight API for channel metadata, so users can browse and watch free-to-air streams without paid subscriptions.

## Features

- Live channel catalog and favorites
- Native desktop window (pywebview) wrapping the same modern web UI - no VLC install needed
- A separate Classic desktop app (Tkinter/VLC) for anyone who prefers the original VLC-based player
- FastAPI backend for channel data
- Browser access to the same UI, installable as a PWA

## Quick start

```bash
git clone https://github.com/adab-tech/adamsy-free-tv.git
cd adamsy-free-tv
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python tv_main.py --serve-api --host 127.0.0.1 --port 8000
```

The API and web UI then listen on http://127.0.0.1:8000/. See [TESTING.md](TESTING.md) for desktop/installer testing.

## Deploy (API)

Docker and Fly both serve with **uvicorn** on **port 8080** (not the FastAPI CLI). Set `ADAMSY_ADMIN_TOKEN` on Fly and Vercel so `POST /admin/refresh` is not left open; details are in [SECURITY.md](SECURITY.md).

```bash
docker build -t adamsy-free-tv .
docker run --rm -p 8080:8080 -e ADAMSY_ADMIN_TOKEN=change-me adamsy-free-tv
curl -s http://127.0.0.1:8080/health
```

## Desktop apps

Adamsy Free TV ships as two independent desktop apps, installed side by side:

| App | Start Menu shortcut | Launch command | Requires VLC |
|-----|----------------------|-----------------|--------------|
| Adamsy Free TV (default) | "Adamsy Free TV" | `python tv_main.py` | No |
| Adamsy Free TV (Classic) | "Adamsy Free TV (Classic)" | `python tv_main.py --classic` | Yes |

Both apps read the same `tv_channels.json` catalog and are fully functional on their own; installing or removing one does not affect the other.

## Tech stack

| Layer | Tools |
|-------|--------|
| API | Python, FastAPI |
| Desktop (default) | Python, pywebview (WebView2 on Windows) |
| Desktop (Classic) | Python, Tkinter, python-vlc |
| Web | HTML/CSS/JS, hls.js, installable PWA |

## License

MIT - see [LICENSE](LICENSE). The Windows installer is code-signed for free via [SignPath.io](https://signpath.io)'s open source program; see [SIGNING.md](SIGNING.md) for setup status.

## Author

**Adamu Abubakar** · [adamu.tech](https://adamu.tech) · [contact@adamu.tech](mailto:contact@adamu.tech)
