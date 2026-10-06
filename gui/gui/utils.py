# gui/utils.py
"""Shared utilities for sokonalysis."""
import os, sys, platform, subprocess, base64


def get_version():
    """Read version from version.txt file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    version_path = os.path.join(base_dir, 'version.txt')
    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except:
        return "3.5.0"


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
        except:
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
        except:
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
        except:
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
        for p in [os.path.join(sys._MEIPASS, 'assets', 'logo.png'), os.path.join(sys._MEIPASS, 'logo.png')]:
            if os.path.exists(p): return p
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.png'),
        os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png'),
        os.path.join('assets', 'logo.png'),
    ]:
        if p and os.path.exists(p): return p
    return ""


def get_logo_base64():
    """Get logo as base64 string for HTML embedding."""
    path = find_logo()
    if path and os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except:
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