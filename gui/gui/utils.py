# gui/utils.py
"""Shared utilities for sokonalysis."""
import os, sys, platform, subprocess, base64


def get_version():
    """Read version from version.txt. Single source of truth for the whole app.

    Looked up, in order:
      1. PyInstaller onefile bundle       -> _MEIPASS/version.txt
      2. PyInstaller onedir (next to exe) -> <exe_dir>/version.txt
      3. PyInstaller onedir (internal)    -> <exe_dir>/_internal/version.txt
      4. Source tree (repo root)          -> <repo>/version.txt
      5. Installed .deb layout            -> /usr/share/sokonalysis/version.txt
      6. Current working directory        -> ./version.txt
    """
    candidates = []

    mei = getattr(sys, "_MEIPASS", None)
    if mei:
        candidates.append(os.path.join(mei, "version.txt"))

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "version.txt"))
        candidates.append(os.path.join(exe_dir, "_internal", "version.txt"))

    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(os.path.dirname(here), "version.txt"))

    candidates.append("/usr/share/sokonalysis/version.txt")
    candidates.append(os.path.join(os.getcwd(), "version.txt"))

    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                v = f.read().strip()
                if v:
                    return v
        except OSError:
            continue

    return "0.0.0"


def get_os_info():
    """Get operating system information."""
    os_name = platform.system()

    if os_name == "Linux":
        try:
            import distro
            name = distro.name(pretty=True)
            version = distro.version(pretty=True)
            if name and version:
                return f"{name} {version}"
            return name
        except Exception:
            pass

        try:
            with open('/etc/os-release', 'r') as f:
                info = {}
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        info[key] = value.strip('"')
                pretty = info.get('PRETTY_NAME', '')
                if pretty:
                    return pretty
        except Exception:
            pass

        return "Linux"

    elif os_name == "Windows":
        ver = platform.version()
        try:
            major = int(ver.split('.')[0])
            build = int(ver.split('.')[2]) if len(ver.split('.')) > 2 else 0
            if build >= 22000:
                return "Windows 11"
            elif major == 10:
                return "Windows 10"
        except Exception:
            pass
        return "Windows"

    elif os_name == "Darwin":
        mac_ver = platform.mac_ver()[0]
        return f"macOS {mac_ver}" if mac_ver else "macOS"

    return os_name


def get_python_version():
    return platform.python_version()


def get_arch():
    return platform.machine()


def find_logo():
    """Find the logo file path."""
    if hasattr(sys, '_MEIPASS'):
        for p in [os.path.join(sys._MEIPASS, 'assets', 'logo.png'),
                  os.path.join(sys._MEIPASS, 'logo.png')]:
            if os.path.exists(p):
                return p
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.png'),
        os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png'),
        os.path.join('assets', 'logo.png'),
    ]:
        if p and os.path.exists(p):
            return p
    return ""


def get_logo_base64():
    """Get logo as base64 string for HTML embedding."""
    path = find_logo()
    if path and os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            pass
    return None


def get_app_info():
    """Get all app info as a dict (for About dialog, status bar, etc.)."""
    return {
        "version": get_version(),
        "os": get_os_info(),
        "python": get_python_version(),
        "arch": get_arch(),
        "logo_path": find_logo(),
        "logo_base64": get_logo_base64(),
    }