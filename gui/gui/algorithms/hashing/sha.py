# gui/algorithms/hashing/sha.py
"""SHA family: generate and reverse (SHA-1, SHA-224, SHA-256, SHA-384, SHA-512)."""
import hashlib

from ._common import reverse_auto


_SHA_HASHERS = {
    'SHA-1':   hashlib.sha1,
    'SHA-224': hashlib.sha224,
    'SHA-256': hashlib.sha256,
    'SHA-384': hashlib.sha384,
    'SHA-512': hashlib.sha512,
}


def generate(text: str, algo: str = 'SHA-256') -> str:
    """Return the hex digest of `text` using the given SHA variant."""
    h = _SHA_HASHERS.get(algo)
    if h is None:
        raise ValueError(f"Unsupported SHA variant: {algo}")
    return h(text.encode('utf-8')).hexdigest()


def reverse(hash_value: str, wordlist_path: str, algo: str = 'SHA-256',
            progress_cb=None, cancelled_check=None):
    """Reverse a SHA hash against a wordlist. Returns plaintext or None."""
    if algo not in _SHA_HASHERS:
        return None
    return reverse_auto(hash_value, wordlist_path,
                        progress_cb=progress_cb,
                        cancelled_check=cancelled_check)