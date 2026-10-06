# sokonalysis

A comprehensive cryptographic toolkit GUI application for students, CTF competitors, and organizations. Provides encryption, decryption, hashing, and cryptanalysis operations across various algorithms.

## Tech Stack

- **Language**: Python 3.12
- **GUI Framework**: PySide6 (Qt for Python)
- **Crypto**: pycryptodome, gmpy2
- **Visualization**: matplotlib
- **Other**: PyMuPDF, requests

## Running the App

The app runs as a desktop GUI using a virtual framebuffer (Xvfb) with VNC output in Replit.

```bash
bash start.sh
```

The `SKIP_ADMIN_CHECK=1` environment variable bypasses the Linux privilege escalation (pkexec/sudo) which is not needed in this container environment.

## Project Structure

- `main.py` — Entry point, sets up Qt app and splash screen
- `cli.py` — CLI for install/update/uninstall operations
- `gui/` — All GUI modules (pages, windows, managers)
- `assets/` — Icons, logos, documentation PDFs
- `JtR/` — John the Ripper jumbo integration

## User Preferences

(none yet)
