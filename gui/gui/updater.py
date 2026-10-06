# gui/updater.py
import json
import urllib.request
import os
import sys
import platform
import subprocess
import tempfile
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PySide6.QtCore import QThread, Signal

GITHUB_API = "https://api.github.com/repos/sokonalysis/sokonalysis/releases"


class UpdateChecker(QThread):
    
    progress = Signal(str)
    finished = Signal(bool, str, str, str)
    
    def __init__(self, current_version, current_build_time=None):
        super().__init__()
        self.current_version = current_version
        self.current_build_time = current_build_time
    
    def _get_current_build_time(self):
        if self.current_build_time:
            return self.current_build_time
        
        version_file = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.', 'version.txt'
        )
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                content = f.read().strip()
                for line in content.split('\n'):
                    if 'built:' in line.lower():
                        return line.split(':', 1)[1].strip()
        
        try:
            exe_path = sys.executable if hasattr(sys, '_MEIPASS') else __file__
            mtime = os.path.getmtime(exe_path)
            return datetime.fromtimestamp(mtime).isoformat()
        except:
            return None
    
    def run(self):
        try:
            current_time = self._get_current_build_time()
            
            req = urllib.request.Request(
                GITHUB_API,
                headers={
                    'User-Agent': 'sokonalysis-updater',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                releases = json.loads(response.read().decode())
            
            if not releases:
                self.finished.emit(False, "No releases found.", "", "")
                return
            
            latest = None
            for release in releases:
                if not release.get('draft', False):
                    latest = release
                    break
            
            if not latest:
                self.finished.emit(False, "No stable releases found.", "", "")
                return
            
            release_version = latest.get('tag_name', '').lstrip('v')
            release_time = latest.get('published_at', '') or latest.get('created_at', '')
            
            if current_time and release_time:
                try:
                    current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
                    release_dt = datetime.fromisoformat(release_time.replace('Z', '+00:00'))
                    
                    if release_dt <= current_dt:
                        self.finished.emit(
                            False,
                            f"You are up to date!\n\n"
                            f"Current: v{self.current_version}\n"
                            f"Latest: v{release_version}\n"
                            f"Released: {release_dt.strftime('%Y-%m-%d %H:%M')}",
                            "", ""
                        )
                        return
                except (ValueError, TypeError):
                    pass
            
            assets = latest.get('assets', [])
            download_url = ""
            filename = ""
            
            system = platform.system()
            
            if system == "Linux":
                for asset in assets:
                    name = asset.get('name', '')
                    if name.endswith('.deb'):
                        download_url = asset.get('browser_download_url', '')
                        filename = name
                        break
            elif system == "Windows":
                for asset in assets:
                    name = asset.get('name', '')
                    if name.endswith('.exe'):
                        download_url = asset.get('browser_download_url', '')
                        filename = name
                        break
            
            if not download_url:
                self.finished.emit(
                    False,
                    f"No installer found for {system}.\n"
                    f"Please download manually.",
                    "", ""
                )
                return
            
            release_dt_str = ""
            try:
                release_dt = datetime.fromisoformat(release_time.replace('Z', '+00:00'))
                release_dt_str = release_dt.strftime('%Y-%m-%d %H:%M UTC')
            except:
                release_dt_str = release_time
            
            self.finished.emit(
                True,
                f"Update available!\n\n"
                f"Current: v{self.current_version}\n"
                f"Latest: v{release_version}\n"
                f"Released: {release_dt_str}\n\n"
                f"File: {filename}",
                download_url,
                filename
            )
            
        except urllib.error.URLError as e:
            self.finished.emit(False, f"Network error: {str(e)}", "", "")
        except Exception as e:
            self.finished.emit(False, f"Update check failed: {str(e)}", "", "")


class UpdateDownloader(QThread):
    
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, download_url, filename):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
        self._is_running = True
    
    def stop(self):
        self._is_running = False
    
    def run(self):
        try:
            temp_dir = tempfile.mkdtemp(prefix="sokonalysis_update_")
            filepath = os.path.join(temp_dir, self.filename)
            
            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': 'sokonalysis-updater'}
            )
            
            with urllib.request.urlopen(req, timeout=300) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(filepath, 'wb') as f:
                    while self._is_running:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
            
            if self._is_running:
                self.progress.emit(100)
                self.finished.emit(True, filepath)
            
        except Exception as e:
            if self._is_running:
                self.finished.emit(False, str(e))


def check_for_updates(parent_widget):
    """Check for updates - called from main_window menu."""
    current_version = "3.5.0"
    
    current_build_time = None
    version_file = os.path.join(
        sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.', 'version.txt'
    )
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if 'built:' in line.lower():
                    current_build_time = line.split(':', 1)[1].strip()
                    break
    
    # Keep reference to prevent garbage collection
    parent_widget._update_checker = UpdateChecker(current_version, current_build_time)
    
    def on_finished(update_available, message, download_url, filename):
        if update_available:
            reply = QMessageBox.question(
                parent_widget,
                "Update Available",
                message + "\n\nDownload and install now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                _download_and_install(parent_widget, download_url, filename)
        else:
            QMessageBox.information(parent_widget, "Update Check", message)
    
    parent_widget._update_checker.finished.connect(on_finished)
    parent_widget._update_checker.start()


def _download_and_install(parent_widget, download_url, filename):
    """Download and install update."""
    progress = QProgressDialog(
        "Downloading update...", "Cancel", 0, 100, parent_widget
    )
    progress.setWindowTitle("Downloading")
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.setAutoClose(False)
    
    # Keep reference
    parent_widget._update_downloader = UpdateDownloader(download_url, filename)
    
    def on_progress(percent):
        progress.setValue(percent)
        if progress.wasCanceled():
            parent_widget._update_downloader.stop()
    
    def on_finished(success, filepath):
        progress.close()
        
        if success:
            system = platform.system()
            
            if system == "Linux":
                reply = QMessageBox.question(
                    parent_widget,
                    "Install Update",
                    f"Download complete: {filename}\n\n"
                    "Install the .deb package now?\n"
                    "(Requires sudo privileges)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        subprocess.run(
                            ['pkexec', 'dpkg', '-i', filepath],
                            check=True
                        )
                        QMessageBox.information(
                            parent_widget, "Success",
                            "Update installed successfully!\nPlease restart the application."
                        )
                    except:
                        try:
                            subprocess.run(
                                ['sudo', 'dpkg', '-i', filepath],
                                check=True
                            )
                            QMessageBox.information(
                                parent_widget, "Success",
                                "Update installed successfully!\nPlease restart the application."
                            )
                        except:
                            QMessageBox.warning(
                                parent_widget, "Manual Install",
                                f"Please install manually:\nsudo dpkg -i {filepath}"
                            )
            
            elif system == "Windows":
                reply = QMessageBox.question(
                    parent_widget,
                    "Install Update",
                    f"Download complete: {filename}\n\nRun the installer now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        os.startfile(filepath)
                        QMessageBox.information(
                            parent_widget, "Installer Started",
                            "The installer has been launched."
                        )
                    except Exception as e:
                        QMessageBox.warning(
                            parent_widget, "Error",
                            f"Could not start installer:\n{str(e)}\n\nFile: {filepath}"
                        )
        else:
            QMessageBox.warning(
                parent_widget, "Download Failed",
                f"Could not download update:\n{filepath}"
            )
    
    parent_widget._update_downloader.progress.connect(on_progress)
    parent_widget._update_downloader.finished.connect(on_finished)
    parent_widget._update_downloader.start()