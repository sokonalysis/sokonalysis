"""
Cross-platform John the Ripper management with comprehensive Windows detection
"""
import os
import sys
import subprocess
import platform
import requests
import zipfile
import tarfile
import tempfile
import shutil
import winreg
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class JohnManager:
    """Cross-platform John the Ripper detection and management"""
    
    def __init__(self):
        self.system = platform.system()
        self.john_path = None
        self.john_dir = None
        
    def find_john_comprehensive(self):
        """
        Comprehensive search for John the Ripper on any system.
        Uses multiple strategies to find the installation.
        """
        if self.system == "Windows":
            return self._find_john_windows()
        else:
            return self._find_john_unix()
    
    def _find_john_windows(self):
        """Windows-specific comprehensive search"""
        
        # Strategy 1: Check PATH first
        john_in_path = shutil.which('john.exe')
        if john_in_path and self._verify_john(john_in_path):
            self.john_path = john_in_path
            self.john_dir = str(Path(john_in_path).parent)
            return True
        
        # Strategy 2: Search common installation directories
        common_dirs = [
            # Default installation locations
            "C:\\john\\run",
            "C:\\john-1.9.0-jumbo-1\\run",
            "C:\\john-the-ripper\\run",
            "C:\\JtR\\run",
            "C:\\Program Files\\john\\run",
            "C:\\Program Files (x86)\\john\\run",
            "C:\\Program Files\\John the Ripper\\run",
            "C:\\Program Files (x86)\\John the Ripper\\run",
            
            # User directories
            os.path.expandvars("%LOCALAPPDATA%\\john\\run"),
            os.path.expandvars("%APPDATA%\\john\\run"),
            os.path.expandvars("%USERPROFILE%\\john\\run"),
            os.path.expandvars("%USERPROFILE%\\john-the-ripper\\run"),
            os.path.expandvars("%USERPROFILE%\\JtR\\run"),
            
            # Tools directories
            "C:\\tools\\john\\run",
            "C:\\security\\john\\run",
            "C:\\pentest\\john\\run",
            "D:\\tools\\john\\run",
            "D:\\security\\john\\run",
        ]
        
        for directory in common_dirs:
            john_exe = os.path.join(directory, "john.exe")
            if os.path.exists(john_exe) and self._verify_john(john_exe):
                self.john_path = john_exe
                self.john_dir = directory
                return True
        
        # Strategy 3: Search entire Downloads folder recursively
        if self._search_downloads_folder():
            return True
        
        # Strategy 4: Search Desktop
        if self._search_desktop():
            return True
        
        # Strategy 5: Search entire C: drive (with limits to avoid taking too long)
        if self._search_drive_smart():
            return True
        
        # Strategy 6: Check Windows Registry
        if self._check_registry():
            return True
        
        return False
    
    def _verify_john(self, john_path):
        """Verify that a john executable actually works"""
        try:
            result = subprocess.run(
                [john_path], 
                capture_output=True, 
                text=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if self.system == "Windows" else 0
            )
            # John returns 0 or 1 when run without arguments
            if result.returncode in [0, 1]:
                # Check if output contains "John the Ripper"
                output = result.stderr + result.stdout
                if 'john' in output.lower() or 'password' in output.lower():
                    return True
        except:
            pass
        return False
    
    def _search_downloads_folder(self):
        """Search the Downloads folder recursively for john.exe"""
        downloads = Path(os.path.expanduser("~")) / "Downloads"
        if not downloads.exists():
            return False
        
        # Search up to 3 levels deep in Downloads
        return self._search_directory(downloads, max_depth=3)
    
    def _search_desktop(self):
        """Search the Desktop for john.exe"""
        desktop = Path(os.path.expanduser("~")) / "Desktop"
        if not desktop.exists():
            return False
        
        return self._search_directory(desktop, max_depth=2)
    
    def _search_drive_smart(self):
        """Smart search of C: drive, focusing on likely locations"""
        # Search these directories first (faster than full drive scan)
        priority_dirs = [
            "C:\\",
            "C:\\Users",
            "C:\\tools",
            "C:\\security",
            "C:\\pentest",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]
        
        for directory in priority_dirs:
            if not os.path.exists(directory):
                continue
            
            # Search only 2 levels deep for performance
            try:
                for root, dirs, files in os.walk(directory):
                    # Calculate depth
                    depth = root[len(directory):].count(os.sep)
                    if depth > 2:
                        dirs.clear()  # Don't go deeper
                        continue
                    
                    if 'john.exe' in files:
                        john_path = os.path.join(root, 'john.exe')
                        if self._verify_john(john_path):
                            self.john_path = john_path
                            self.john_dir = root
                            return True
                    
                    # Skip system directories for speed
                    dirs[:] = [d for d in dirs if not d.startswith('.') and 
                              d not in ['Windows', 'System32', 'SysWOW64', '$Recycle.Bin']]
            except (PermissionError, OSError):
                continue
        
        return False
    
    def _search_directory(self, directory, max_depth=3):
        """Search a directory recursively for john.exe"""
        try:
            for root, dirs, files in os.walk(str(directory)):
                depth = root[len(str(directory)):].count(os.sep)
                if depth > max_depth:
                    dirs.clear()
                    continue
                
                if 'john.exe' in files:
                    john_path = os.path.join(root, 'john.exe')
                    if self._verify_john(john_path):
                        self.john_path = john_path
                        self.john_dir = root
                        return True
        except (PermissionError, OSError):
            pass
        return False
    
    def _check_registry(self):
        """Check Windows Registry for John the Ripper installation"""
        try:
            # Check uninstall registry keys
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in reg_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if "john" in display_name.lower():
                                    # Try to get install location
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        john_path = os.path.join(install_location, "run", "john.exe")
                                        if os.path.exists(john_path) and self._verify_john(john_path):
                                            self.john_path = john_path
                                            self.john_dir = os.path.dirname(john_path)
                                            return True
                                    except:
                                        pass
                            except:
                                continue
                            finally:
                                winreg.CloseKey(subkey)
                        except:
                            continue
                    winreg.CloseKey(key)
                except:
                    continue
            
            # Check App Paths registry
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\john.exe")
                john_path = winreg.QueryValueEx(key, "")[0]
                winreg.CloseKey(key)
                
                if os.path.exists(john_path) and self._verify_john(john_path):
                    self.john_path = john_path
                    self.john_dir = os.path.dirname(john_path)
                    return True
            except:
                pass
            
            # Check user registry
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                    r"Software\John the Ripper")
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                winreg.CloseKey(key)
                
                john_path = os.path.join(install_path, "run", "john.exe")
                if os.path.exists(john_path) and self._verify_john(john_path):
                    self.john_path = john_path
                    self.john_dir = os.path.dirname(john_path)
                    return True
            except:
                pass
                
        except Exception:
            pass
        
        return False
    
    def _find_john_unix(self):
        """Unix-like systems search"""
        # Check common paths
        common_paths = [
            "/usr/bin/john",
            "/usr/sbin/john",
            "/usr/local/bin/john",
            "/usr/local/sbin/john",
            "/snap/bin/john",
            "/opt/john/run/john",
            "/opt/john-the-ripper/run/john",
            os.path.expanduser("~/john/run/john"),
            os.path.expanduser("~/.local/bin/john"),
        ]
        
        for path in common_paths:
            if os.path.exists(path) and self._verify_john(path):
                self.john_path = path
                self.john_dir = os.path.dirname(path)
                return True
        
        # Check PATH
        which_john = shutil.which('john')
        if which_john and self._verify_john(which_john):
            self.john_path = which_john
            self.john_dir = os.path.dirname(which_john)
            return True
        
        return False
    
    def get_version(self):
        """Get John the Ripper version"""
        if not self.john_path:
            if not self.find_john_comprehensive():
                return "Not installed"
        
        try:
            result = subprocess.run(
                [self.john_path], 
                capture_output=True, 
                text=True, 
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if self.system == "Windows" else 0
            )
            output = result.stderr if result.stderr else result.stdout
            for line in output.split('\n'):
                if 'John the Ripper' in line:
                    return line.strip()
                if 'version' in line.lower():
                    return line.strip()
            return "Unknown version"
        except:
            return "Unknown"
    
    def get_search_report(self):
        """Generate a report of where John was found or searched"""
        if self.john_path:
            return f"""
            <div style="color: #4CAF50;">
                <h3>✓ John the Ripper Found!</h3>
                <p><b>Location:</b> {self.john_path}</p>
                <p><b>Directory:</b> {self.john_dir}</p>
                <p><b>Version:</b> {self.get_version()}</p>
            </div>
            """
        else:
            return """
            <div style="color: #f44336;">
                <h3>✗ John the Ripper Not Found</h3>
                <p>Searched locations:</p>
                <ul>
                    <li>System PATH</li>
                    <li>C:\\Program Files</li>
                    <li>C:\\Program Files (x86)</li>
                    <li>Downloads folder</li>
                    <li>Desktop</li>
                    <li>C:\\ drive (common locations)</li>
                    <li>Windows Registry</li>
                </ul>
                <p><b>Recommendation:</b> Download John the Ripper from:</p>
                <p><a href="https://github.com/openwall/john-packages/releases">https://github.com/openwall/john-packages/releases</a></p>
                <p>Extract it anywhere and sokonalysis will find it automatically.</p>
            </div>
            """

class JohnSearchWorker(QThread):
    """Background thread for searching John the Ripper"""
    progress = Signal(str)
    found = Signal(str)  # Emits path when found
    finished = Signal(bool, str)  # Success, message
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    def run(self):
        self.progress.emit("Searching for John the Ripper...")
        self.progress.emit("Checking PATH...")
        
        # Quick PATH check first
        if shutil.which('john.exe' if self.manager.system == "Windows" else 'john'):
            path = shutil.which('john.exe' if self.manager.system == "Windows" else 'john')
            if self.manager._verify_john(path):
                self.found.emit(path)
                self.finished.emit(True, f"Found in PATH: {path}")
                return
        
        self.progress.emit("Searching common locations...")
        
        # Full search
        if self.manager.find_john_comprehensive():
            self.found.emit(self.manager.john_path)
            self.finished.emit(True, f"Found: {self.manager.john_path}")
        else:
            self.finished.emit(False, "John the Ripper not found on this system")