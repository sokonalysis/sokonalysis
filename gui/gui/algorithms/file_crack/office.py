# gui/algorithms/file_crack/office.py
"""Office document cracking: office2john + john."""
import os

from ._common import (
    find_tool, run_2john, john_crack, john_show,
    temp_hashfile, safe_remove, has_wordlist,
)


def crack_office(path, wordlist_path, progress_cb=None, cancelled_check=None):
    def log(m):
        if progress_cb:
            progress_cb(m)

    if not has_wordlist(wordlist_path):
        log("No wordlist configured")
        return None

    log(f"Cracking {os.path.basename(path)}...")
    log(f"Using wordlist: {os.path.basename(wordlist_path)}")

    tool = find_tool('office2john')
    if not tool:
        log("office2john not found")
        return None

    hash_text = None
    for marker in ('$office$', '$oldoffice$', '$MSO$'):
        hash_text = run_2john(tool, path, marker=marker)
        if hash_text:
            break
    if not hash_text:
        log("No hash extracted from Office document")
        return None

    hash_file = temp_hashfile('.office.hash')
    try:
        with open(hash_file, 'w') as f:
            f.write(hash_text + '\n')
        log("Hash extracted")
        log("Note: Office 2013+ hashes are very slow")
        john_crack(hash_file, wordlist_path, timeout=300,
                   progress_cb=progress_cb)
        pwd = john_show(hash_file)
        if pwd:
            return pwd
    finally:
        safe_remove(hash_file)

    return None