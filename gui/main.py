# main.py
import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QProcess
from PySide6.QtGui import QFont, QIcon

from gui.splash_screen import SplashScreen
from gui.main_window import MainWindow
from gui.theme_manager import ThemeManager
from gui.auto_font import init_auto_font  # ADD THIS LINE


def is_admin():
    """Check if the program is running with admin/root privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False


def request_admin():
    """Request admin privileges - Linux only. Windows/macOS run as normal user."""
    if is_admin():
        return True
    
    current_os = platform.system()
    
    # Windows: Run as normal user, no UAC prompt
    if current_os == "Windows":
        return True
    
    # Linux: Request admin for Wi-Fi tools and system operations
    elif current_os == "Linux":
        script_path = os.path.abspath(sys.argv[0])
        cwd = os.getcwd()
        display = os.environ.get("DISPLAY", ":0")
        xauthority = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
        
        # Try pkexec with display preserved
        try:
            process = QProcess()
            env = QProcess.systemEnvironment()
            env.append(f"DISPLAY={display}")
            env.append(f"XAUTHORITY={xauthority}")
            process.setEnvironment(env)
            process.setWorkingDirectory(cwd)
            process.startDetached("pkexec", ["env", f"DISPLAY={display}", f"XAUTHORITY={xauthority}", sys.executable, script_path])
            return False
        except:
            pass
        
        # Try sudo with display preserved
        try:
            process = QProcess()
            cmd = f"cd {cwd} && sudo DISPLAY={display} XAUTHORITY={xauthority} {sys.executable} {script_path}"
            process.startDetached("x-terminal-emulator", ["-e", "bash", "-c", cmd + "; read -p 'Press Enter to close...'"])
            return False
        except:
            pass
        
        # Fallback - run normally
        return True
    
    # macOS: Run as normal user
    elif current_os == "Darwin":
        return True
    
    return True


def _get_asset_path(filename):
    """Get asset path for both development and PyInstaller builds."""
    if hasattr(sys, '_MEIPASS'):
        paths = [
            os.path.join(sys._MEIPASS, 'assets', filename),
            os.path.join(sys._MEIPASS, filename),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', filename),
        os.path.join('assets', filename),
        f'/usr/share/sokonalysis/assets/{filename}',
        f'/usr/local/share/icons/{filename}',
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return ""


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("sokonalysis")
    app.setOrganizationName("sokonalysis-project")
    
    font = QFont("Inter", 10)
    if not font.exactMatch():
        font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    icon_path = _get_asset_path("logo.png")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize auto font - handles all font scaling automatically
    init_auto_font()  # ADD THIS LINE
    
    # Request admin privileges (Linux only for Wi-Fi/system tools)
    # Windows and macOS run as normal user without UAC prompt
    # Skip escalation when running headless/in container (pkexec/sudo not available)
    if not os.environ.get("SKIP_ADMIN_CHECK"):
        if not request_admin():
            sys.exit(0)
    
    theme_manager = ThemeManager()
    main_window = None
    
    def show_main_window():
        nonlocal main_window
        main_window = MainWindow(theme_manager)
        main_window.show()
    
    splash = SplashScreen()
    splash.loading_complete.connect(show_main_window)
    splash.start_loading()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()