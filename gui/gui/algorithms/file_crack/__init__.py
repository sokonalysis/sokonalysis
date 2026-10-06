# gui/algorithms/file_crack/__init__.py
"""
File-cracking package.

Re-exports each cracker so existing callers keep working unchanged:
    from gui.algorithms import file_crack
    file_crack.crack_zip(path, wordlist, progress_cb=..., cancelled_check=...)

Or import a specific format directly:
    from gui.algorithms.file_crack.zip import crack_zip
"""
from .zip import crack_zip
from .rar import crack_rar
from .sevenzip import crack_7z
from .pdf import crack_pdf
from .office import crack_office
from .wifi import crack_wifi

__all__ = [
    'crack_zip',
    'crack_rar',
    'crack_7z',
    'crack_pdf',
    'crack_office',
    'crack_wifi',
]