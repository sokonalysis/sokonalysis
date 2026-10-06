# gui/algorithms/file_crack/zip.py
"""ZIP cracking: zip2john + john, with a pure-Python zipfile fallback."""
import os
import zipfile

from ._common import (
    find_tool, run_2john, john_crack, john_show,
    temp_hashfile, safe_remove, has_wordlist,
)


def crack_zip(path, wordlist_path, progress_cb=None, cancelled_check=None):
    def log(m):
        if progress_cb:
            progress_cb(m)

    if not has_wordlist(wordlist_path):
        log("No wordlist configured")
        return None

    log(f"Cracking {os.path.basename(path)}...")
    log(f"Using wordlist: {os.path.basename(wordlist_path)}")

    tool = find_tool('zip2john')
    if tool:
        hash_text = run_2john(tool, path, marker='$')
        if hash_text:
            hash_file = temp_hashfile('.zip.hash')
            try:
                with open(hash_file, 'w') as f:
                    f.write(hash_text + '\n')
                log("Hash extracted")
                john_crack(hash_file, wordlist_path, timeout=120,
                           progress_cb=progress_cb)
                pwd = john_show(hash_file)
                if pwd:
                    return pwd
            finally:
                safe_remove(hash_file)

    log("Trying direct wordlist pass...")
    try:
        with zipfile.ZipFile(path) as zf:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if cancelled_check and cancelled_check():
                        log("Cracking cancelled.")
                        return None
                    pw = line.rstrip('\r\n')
                    if not pw:
                        continue
                    try:
                        zf.extractall(pwd=pw.encode())
                        return pw
                    except Exception:
                        continue
    except Exception as e:
        log(f"ZIP fallback failed: {e}")

    return None