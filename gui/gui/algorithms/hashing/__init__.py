# gui/algorithms/hashing/__init__.py
"""
Hashing package.

Public API:
    generate_md5, reverse_md5          (MD5 only)
    generate_sha, reverse_sha          (SHA family only)
    reverse_auto                       (any john-supported format)

reverse_auto covers the same 100+ formats as HashingPage:
bcrypt, sha512crypt, md5crypt, NTLM, Kerberos, WPA, ZIP, RAR, 7z, PDF,
Office, LUKS, Bitcoin, Electrum, GPG, KeePass, PuTTY, and the raw-hex
MD5/SHA-* family.

Callers can use either:
    from gui.algorithms import hashing
    hashing.reverse_auto(h, wl)

or import a specific function:
    from gui.algorithms.hashing.md5 import reverse as reverse_md5
"""
from .md5 import generate as generate_md5, reverse as reverse_md5
from .sha import generate as generate_sha, reverse as reverse_sha
from ._common import (
    find_hash_in_text,
    detect_hash_type,
    detect_format_info,
    reverse_auto,
    HASH_LENGTHS,
    HASH_REGEX,
)

__all__ = [
    'generate_md5', 'reverse_md5',
    'generate_sha', 'reverse_sha',
    'reverse_auto',
    'find_hash_in_text',
    'detect_hash_type',
    'detect_format_info',
    'HASH_LENGTHS', 'HASH_REGEX',
]