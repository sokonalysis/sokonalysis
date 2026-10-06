# gui/splash_screen.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont, QMovie
import os
import sys

class SplashScreen(QWidget):
    """Splash screen: animated GIF logo, then static logo with loading progress."""
    
    loading_complete = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 200)
        
        # Center
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 300) // 2
        y = (screen.height() - 200) // 2
        self.setGeometry(x, y, 300, 200)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 30, 60, 40)
        layout.setSpacing(20)
        
        # Logo container with fixed size
        self.logo_container = QWidget()
        self.logo_container.setFixedSize(90, 90)
        self.logo_container.setStyleSheet("background: transparent;")
        
        # Logo label inside container
        self.logo = QLabel(self.logo_container)
        self.logo.setStyleSheet("background: transparent;")
        self.logo.setGeometry(0, 0, 90, 90)
        
        # Thin green progress bar (initially hidden)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #34d399;
                border-radius: 1px;
            }
        """)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()  # Hidden until GIF finishes
        
        # Center the logo container horizontally
        logo_wrapper = QHBoxLayout()
        logo_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_wrapper.addWidget(self.logo_container)
        
        layout.addStretch()
        layout.addLayout(logo_wrapper)
        layout.addWidget(self.progress)
        layout.addStretch()
        
        # Store paths
        self.gif_path = self._get_gif_path()
        self.png_path = self._get_png_path()
        
        # Flag to prevent double transitions
        self._transitioned = False
    
    def _get_gif_path(self):
        """Find GIF logo in multiple possible locations."""
        # PyInstaller extracts files to sys._MEIPASS
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
            paths = [
                os.path.join(base_path, 'assets', 'logo.gif'),
                os.path.join(base_path, 'logo.gif'),
            ]
            for p in paths:
                if os.path.exists(p):
                    return p
        
        # Development paths
        paths = [
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.gif'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.gif'),
            os.path.join('assets', 'logo.gif'),
            os.path.join(os.path.expanduser('~'), '.sokonalysis', 'logo.gif'),
        ]
        for p in paths:
            if p and os.path.exists(p):
                return p
        return ""
    
    def _get_png_path(self):
        """Find PNG logo in multiple possible locations."""
        # PyInstaller extracts files to sys._MEIPASS
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
            paths = [
                os.path.join(base_path, 'assets', 'logo.png'),
                os.path.join(base_path, 'logo.png'),
            ]
            for p in paths:
                if os.path.exists(p):
                    return p
        
        # Development paths
        paths = [
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.png'),
            os.path.join('assets', 'logo.png'),
            os.path.join(os.path.expanduser('~'), '.sokonalysis', 'logo.png'),
            '/usr/local/share/icons/sokonalysis.png',
        ]
        for p in paths:
            if p and os.path.exists(p):
                return p
        
        # Generate placeholder if nothing found
        return self._generate_placeholder()
    
    def _generate_placeholder(self):
        """Generate a placeholder logo."""
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        placeholder = os.path.join(assets_dir, 'logo.png')
        
        pixmap = QPixmap(128, 128)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, 128, 128)
        gradient.setColorAt(0, QColor("#34d399"))
        gradient.setColorAt(1, QColor("#6ee7b7"))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(8, 8, 112, 112, 24, 24)
        
        painter.setPen(QColor("#0f1117"))
        font = QFont("Inter", 42, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(8, 8, 112, 112, Qt.AlignmentFlag.AlignCenter, "sk")
        painter.end()
        
        pixmap.save(placeholder, "PNG")
        return placeholder
    
    def start_loading(self):
        """Start the splash screen sequence."""
        self.show()
        
        # Start with GIF animation
        if self.gif_path:
            self._play_gif()
        else:
            # No GIF found, go straight to static logo with loading
            self._show_static_logo()
            self._start_progress()
    
    def _play_gif(self):
        """Play the GIF animation first."""
        self.movie = QMovie(self.gif_path)
        
        # Scale to original 90x90 size
        self.movie.setScaledSize(self.movie.currentPixmap().size().scaled(
            90, 90,
            Qt.AspectRatioMode.KeepAspectRatio
        ))
        
        self.movie.setSpeed(100)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setMovie(self.movie)
        self.movie.start()
        
        # Force transition after 3 seconds (adjust as needed)
        QTimer.singleShot(3000, self._on_gif_finished)
    
    def _on_gif_finished(self):
        """Called when GIF animation completes or timer expires."""
        # Prevent double transition
        if self._transitioned:
            return
        self._transitioned = True
        
        # Stop and clean up movie
        if hasattr(self, 'movie'):
            self.movie.stop()
            self.logo.setMovie(None)
            self.movie.deleteLater()
        
        # Show static logo
        self._show_static_logo()
        
        # Start loading progress
        self._start_progress()
    
    def _show_static_logo(self):
        """Display the static PNG logo centered with loading state."""
        if self.png_path and os.path.exists(self.png_path):
            pixmap = QPixmap(self.png_path)
            if not pixmap.isNull():
                # Scale to 90x90 while maintaining aspect ratio
                scaled = pixmap.scaled(
                    90, 90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo.setPixmap(scaled)
                # Center the PNG specifically for loading state
                self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Ensure label fills container
                self.logo.setGeometry(0, 0, 90, 90)
    
    def _start_progress(self):
        """Start the loading progress bar."""
        self.progress.show()
        self._value = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(25)
    
    def _tick(self):
        self._value += 1
        self.progress.setValue(self._value)
        if self._value >= 100:
            self._timer.stop()
            QTimer.singleShot(200, self._finish)
    
    def _finish(self):
        self.loading_complete.emit()
        self.close()