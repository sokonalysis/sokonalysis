# gui/algorithms/file_crack/wifi.py
"""Wi-Fi handshake cracking: aircrack-ng."""
import os
import re
import subprocess

from ._common import has_wordlist


def crack_wifi(path, wordlist_path, progress_cb=None, cancelled_check=None):
    def log(m):
        if progress_cb:
            progress_cb(m)

    if not has_wordlist(wordlist_path):
        log("No wordlist configured")
        return None

    log(f"Analyzing capture: {os.path.basename(path)}...")
    log(f"Using wordlist: {os.path.basename(wordlist_path)}")

    try:
        r = subprocess.run(
            ['aircrack-ng', '-w', wordlist_path, path],
            capture_output=True, text=True, timeout=300
        )
        if 'KEY FOUND' in r.stdout:
            m = re.search(r'KEY FOUND!\s*\[\s*([^\]]+)\s*\]', r.stdout)
            if m:
                return m.group(1).strip()
    except FileNotFoundError:
        log("aircrack-ng not found")
        return None
    except subprocess.TimeoutExpired:
        log("aircrack-ng timed out")
        return None
    except Exception as e:
        log(f"aircrack-ng failed: {e}")
        return None

    return None