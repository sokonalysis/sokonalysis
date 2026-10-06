# gui/algorithms/hashing/md5.py
"""MD5: generate and reverse."""
import hashlib

from ._common import reverse_auto


def generate(text: str) -> str:
    """Return the MD5 hex digest of `text`."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def reverse(hash_value: str, wordlist_path: str,
            progress_cb=None, cancelled_check=None):
    """Reverse an MD5 hash against a wordlist. Returns plaintext or None."""
    return reverse_auto(hash_value, wordlist_path,
                        progress_cb=progress_cb,
                        cancelled_check=cancelled_check)