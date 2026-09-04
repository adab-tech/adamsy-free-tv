# Testing Guide — Adamsy Free TV

This document shows quick ways for testers to run Adamsy Free TV on Windows.

Two recommended options:

A) Run the unsigned installer (easy for most testers)

1. Download
- Download the installer (EXE) from the GitHub Release (or from the Actions artifact link provided by the maintainers).

2. Verify checksum (recommended)
- Open PowerShell in the folder where the EXE is downloaded and run:

  Get-FileHash -Algorithm SHA256 .\Adamsy-Free-TV-Setup-1.0.0.exe

- Compare the printed SHA256 hex string with the value provided by the maintainer. If it matches, the file is authentic.

3. Run the installer
- Double-click the EXE and follow the installer steps.
- Windows SmartScreen or "Unknown publisher" warnings may appear because the installer is unsigned. To proceed:
  - Click "More info" → "Run anyway".
  - Or right-click the file → Properties → check "Unblock" (if present) → Apply → Run.

4. Launch the app
- Use the Start menu or the desktop shortcut. If the app doesn't launch, open the troubleshooting section below.


B) Run from source (for technical testers)

Requirements
- Windows 10/11
- Python 3.11
- Git

Steps
1. Clone the repo

  git clone https://github.com/adab-tech/adamsy-free-tv.git
  cd adamsy-free-tv

2. Create and activate a virtual environment

  python -m venv .venv
  .\.venv\Scripts\Activate.ps1    # PowerShell
  # or for cmd.exe: .\.venv\Scripts\activate.bat

3. Install dependencies

  python -m pip install --upgrade pip
  pip install -r requirements.txt

4. Start the app
- If the repo contains start scripts, run the one provided:

  .\start_tv_app.bat

- If not, run the backend (FastAPI) and any front-end dev server per README. Example for FastAPI (adjust if different):

  uvicorn backend.api:app --host 127.0.0.1 --port 8001

5. Open the UI
- In a browser go to http://localhost:8001 (or the address printed by the start script).


Troubleshooting
- SmartScreen blocks installer: Use "More info" → "Run anyway" or unblock via file Properties.
- Python missing modules or installation errors: paste the pip install output here and the maintainers will help.
- App fails to start with a missing dependency: ensure you installed requirements.txt into the activated virtual environment.

Security & verification
- This repo currently produces unsigned build artifacts. Expect SmartScreen/unknown publisher prompts for Windows installers until a signing certificate is used.
- Always verify the SHA256 checksum before running a downloaded installer.

Reporting issues
- Please include these fields when reporting a problem:
  - Windows version (e.g., Windows 10, 21H2)
  - Installer or source (EXE or run-from-source)
  - Steps you took
  - Any error messages or screenshots

Thank you for testing — your feedback is valuable. Please paste any issues or logs into the repository issues page: https://github.com/adab-tech/adamsy-free-tv/issues
