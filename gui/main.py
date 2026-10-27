# main.py
import sys
import os
import platform
import shutil
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QProcess
from PySide6.QtGui import QFont, QIcon

from gui.splash_screen import SplashScreen
from gui.main_window import MainWindow
from gui.theme_manager import ThemeManager
from gui.auto_font import init_auto_font


def is_admin():
    """Check if the program is running with admin/root privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def _relaunch_command():
    """The program (and args) that re-runs this app.

    Installed build (PyInstaller): just the binary, e.g. /usr/local/bin/sokonalysis.
    That exact path matches the polkit policy, so the password dialog says
    "Authentication is required to run sokonalysis" instead of the full command.

    Dev run (python main.py): the interpreter + script; polkit falls back to
    its default message, which is fine for development.
    """
    if getattr(sys, "frozen", False):
        return os.path.realpath(sys.executable), []
    return sys.executable, [os.path.abspath(sys.argv[0])]


def request_admin():
    """Request admin privileges - Linux only. Windows/macOS run as normal user.

    Returns True if this process should carry on, False if a privileged copy
    was launched and this one should exit.
    """
    if is_admin():
        return True

    current_os = platform.system()

    # Windows / macOS: run as normal user, no prompt
    if current_os != "Linux":
        return True

    program, args = _relaunch_command()
    cwd = os.getcwd()

    # 1) pkexec - the policy file (org.sokonalysis.policy) sets allow_gui, so
    #    DISPLAY/XAUTHORITY are kept without wrapping the command in `env`.
    if shutil.which("pkexec"):
        ok = QProcess.startDetached("pkexec", [program] + args, cwd)
        ok = ok[0] if isinstance(ok, tuple) else ok
        if ok:
            return False

    # 2) sudo in a terminal, display preserved
    terminal = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal")
    if terminal and shutil.which("sudo"):
        display = os.environ.get("DISPLAY", ":0")
        xauthority = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
        quoted = " ".join(f"'{a}'" for a in [program] + args)
        cmd = (f"cd '{cwd}' && sudo DISPLAY={display} XAUTHORITY='{xauthority}' "
               f"QT_QPA_PLATFORMTHEME=generic {quoted}; read -p 'Press Enter to close...'")
        ok = QProcess.startDetached(terminal, ["-e", "bash", "-c", cmd], cwd)
        ok = ok[0] if isinstance(ok, tuple) else ok
        if ok:
            return False

    # 3) Fallback - run normally (admin-only tools will be limited)
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
    # Running as root on Linux there is no user D-Bus session, so Qt's GNOME
    # theme plugin waits ~2 min for the desktop portal and then times out.
    # Skip the portal; sokonalysis has its own light/dark theme anyway.
    if platform.system() == "Linux" and is_admin():
        os.environ.setdefault("QT_QPA_PLATFORMTHEME", "generic")

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
    init_auto_font()

    # Request admin privileges (Linux only for Wi-Fi/system tools)
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