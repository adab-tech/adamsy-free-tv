"""Entry point for the classic Tkinter/VLC build of Adamsy Free TV.

Packaged separately (see VirtualTVClassic.spec) so the classic app
stays an independent executable from the default pywebview app built
from tv_main.py / VirtualTV.spec.
"""
from __future__ import annotations

import tv_main

if __name__ == "__main__":
    tv_main.main(["--classic"])
