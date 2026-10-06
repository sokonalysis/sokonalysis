# gui/algorithms/steganography.py
"""
Steganography extraction: pull hidden content from images/audio.

Separate from file_crack.py because:
  - the goal is extraction, not password recovery
  - wordlist is optional (no-password extraction works alone)
  - returns the hidden content (str), not a password
  - has its own multi-stage strategy (no-pw -> stegseek -> steghide)

Never imports Qt, never emits signals.
"""
import os
import subprocess
import tempfile


def extract(path, wordlist_path=None, progress_cb=None, cancelled_check=None):
    """
    Extract hidden content from an image/audio file.

    Strategy:
      1. steghide extract with no password
      2. stegseek (if available and wordlist provided)
      3. steghide extract with each wordlist entry

    Returns the extracted content (str) on success, or None on failure.
    """
    def log(m):
        if progress_cb:
            progress_cb(m)

    name = os.path.basename(path)
    log(f"Analyzing {name}...")

    # 1) No-password attempt
    content = _try_steghide(path, "")
    if content is not None:
        return content

    # 2 + 3) Wordlist-based attempts
    if wordlist_path and os.path.exists(wordlist_path):
        content = _try_stegseek(path, wordlist_path, log)
        if content is not None:
            return content

        log("Brute forcing with steghide...")
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if cancelled_check and cancelled_check():
                        log("Cracking cancelled.")
                        return None
                    pw = line.rstrip('\r\n')
                    if not pw:
                        continue
                    content = _try_steghide(path, pw)
                    if content is not None:
                        return content
        except Exception as e:
            log(f"Brute force failed: {e}")

    log("No hidden data found")
    return None


def _try_steghide(path, password):
    """Run steghide extract. Returns text content or None."""
    out = os.path.join(
        tempfile.gettempdir(),
        f"{os.path.basename(path)}.out.{os.getpid()}"
    )
    try:
        r = subprocess.run(
            ['steghide', 'extract', '-sf', path, '-xf', out,
             '-p', password, '-f'],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and os.path.exists(out):
            try:
                with open(out, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read().strip()
            finally:
                _safe_remove(out)
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None


def _try_stegseek(path, wordlist, log):
    """Run stegseek. Returns extracted text or None."""
    out = f"{path}.out"
    try:
        if os.path.exists(out):
            _safe_remove(out)
        log("Running stegseek...")
        subprocess.run(
            ['stegseek', '-f', path, wordlist, out],
            capture_output=True, text=True, timeout=180
        )
        if os.path.exists(out):
            try:
                with open(out, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                return content if content else None
            finally:
                _safe_remove(out)
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None


def _safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass