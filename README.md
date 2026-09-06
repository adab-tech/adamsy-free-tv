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
# See repository docs for API + desktop setup
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
