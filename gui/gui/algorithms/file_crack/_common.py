# gui/algorithms/file_crack/_common.py
"""
Shared helpers for the file-cracking modules.

No format-specific logic here - just the plumbing every format needs:
tool discovery, running *2john, running john, temp file handling.
"""
import os
import shutil
import subprocess
import sys
import tempfile


def find_tool(name: str):
    """
    Locate a john helper (zip2john, rar2john, pdf2john, office2john,
    7z2john, hccap2john, john) cross-platform.
    Returns the path/name, or None if not found.
    """
    # 1) Bundled JtR (frozen Windows build)
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', '')
        for sub in ('JtR/run', 'JtR/run/bin'):
            cand = os.path.join(base, sub, f"{name}.exe")
            if os.path.exists(cand):
                return cand

    # 2) Local JtR folder next to the project (dev on Windows)
    if sys.platform == "win32":
        base = os.path.join(os.path.dirname(__file__), '..', '..', '..')
        for sub in ('JtR/run', 'JtR/run/bin'):
            cand = os.path.join(base, sub, f"{name}.exe")
            if os.path.exists(cand):
                return cand

    # 3) PATH
    exe = f"{name}.exe" if sys.platform == "win32" else name
    which = shutil.which(exe)
    if which:
        return which

    # 4) Standard john install locations (Linux/macOS)
    if sys.platform != "win32":
        for path in (
            f"/usr/share/john/{name}.py",
            f"/usr/bin/{name}",
            f"/usr/sbin/{name}",
            f"/usr/local/bin/{name}",
            f"/usr/local/sbin/{name}",
            f"/snap/bin/{name}",
        ):
            if os.path.exists(path):
                return path
    return None


def run_2john(tool_path: str, target: str, marker: str, timeout: int = 30):
    """
    Run <tool> target, collect lines containing `marker` (e.g. '$pkzip$'),
    return joined hash lines or None.
    """
    try:
        if tool_path.endswith('.py'):
            cmd = [sys.executable, tool_path, target]
        else:
            cmd = [tool_path, target]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout + r.stderr
        lines = [l.strip() for l in out.splitlines()
                 if l.strip() and marker in l]
        return '\n'.join(lines) if lines else None
    except Exception:
        return None


def john_show(hash_file: str, fmt: str = None):
    """Run john --show and return the cracked password, or None."""
    try:
        cmd = ['john', '--show', hash_file]
        if fmt:
            cmd.insert(1, f'--format={fmt}')
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith('0 password'):
                continue
            if ':' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    pwd = parts[1].strip()
                    if pwd and not pwd.startswith('$'):
                        return pwd
    except Exception:
        pass
    return None


def john_crack(hash_file: str, wordlist: str, fmt: str = None,
               timeout: int = 120, progress_cb=None):
    """Run john --wordlist=... against hash_file. No return value."""
    try:
        cmd = ['john']
        if fmt:
            cmd.append(f'--format={fmt}')
        cmd.extend(['--wordlist=' + wordlist, hash_file])
        if progress_cb:
            progress_cb("Running john...")
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        if progress_cb:
            progress_cb("john not found")
    except subprocess.TimeoutExpired:
        if progress_cb:
            progress_cb("john timed out")
    except Exception as e:
        if progress_cb:
            progress_cb(f"john error: {e}")


def temp_hashfile(suffix: str = '.hash'):
    fd, path = tempfile.mkstemp(prefix='sokonalysis_', suffix=suffix)
    os.close(fd)
    return path


def safe_remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def has_wordlist(wordlist_path):
    return bool(wordlist_path) and os.path.exists(wordlist_path)