# gui/user_guide_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QPixmap, QImage, QDesktopServices
import os, sys, fitz, subprocess, platform, shutil


class UserGuidePage(QWidget):
    """User guide page with embedded PDF viewer and external open option."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._rendered = False
        self._init_ui()
    
    def _get_guide_path(self):
        """Get the path to the user guide PDF."""
        base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..')
        paths = [
            os.path.join(base, 'assets', 'docs', 'guide.pdf'),
            os.path.join(base, 'assets', 'guide.pdf'),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
    
    def _get_clean_env(self):
        """Environment to use when launching an external process.

        When frozen with PyInstaller, the bootloader points LD_LIBRARY_PATH
        (and sometimes PYTHONHOME/PYTHONPATH) at the bundled libs so *this*
        app's own Python/Qt/etc. resolve correctly. subprocess.Popen()
        inherits that environment by default, so an external viewer like
        evince/firefox/xdg-open ends up trying to load our bundled shared
        libraries instead of its own system ones — which is why "Open"
        works from a plain `python main.py` venv but silently fails (or
        crashes) once the app is compiled. PyInstaller's bootloader backs up
        the original value in *_ORIG variables specifically so subprocesses
        can be restored to a normal environment; if those aren't present we
        just strip the bundled path instead of passing it through.
        """
        env = dict(os.environ)
        if hasattr(sys, '_MEIPASS'):
            for var, orig_var in (
                ('LD_LIBRARY_PATH', 'LD_LIBRARY_PATH_ORIG'),
                ('PYTHONHOME', 'PYTHONHOME_ORIG'),
                ('PYTHONPATH', 'PYTHONPATH_ORIG'),
            ):
                orig_value = env.get(orig_var)
                if orig_value is not None:
                    env[var] = orig_value
                else:
                    env.pop(var, None)
        return env
    
    def _open_externally(self):
        """Open the PDF in the system's default PDF viewer."""
        guide_path = self._get_guide_path()
        if not guide_path:
            QMessageBox.warning(self, "Not Found", "User guide PDF not found.")
            return
        
        viewers = [
            ['atril', guide_path], ['evince', guide_path], ['okular', guide_path],
            ['qpdfview', guide_path], ['firefox', guide_path], ['chromium', guide_path],
            ['google-chrome', guide_path], ['gio', 'open', guide_path],
            ['gvfs-open', guide_path], ['gnome-open', guide_path], ['xdg-open', guide_path],
        ]
        
        clean_env = self._get_clean_env()
        
        for cmd in viewers:
            if shutil.which(cmd[0]):
                try:
                    with open(os.devnull, 'w') as devnull:
                        proc = subprocess.Popen(
                            cmd, stdout=devnull, stderr=devnull, env=clean_env
                        )
                    # A leaked bundled LD_LIBRARY_PATH tends to make the
                    # child crash almost immediately rather than hang.
                    # Give it a brief moment; if it already died, treat this
                    # viewer as failed and fall through to the next one
                    # instead of silently assuming success.
                    QApplication.processEvents()
                    if proc.poll() is not None and proc.returncode != 0:
                        continue
                    return
                except Exception:
                    continue
        
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))
        except:
            QMessageBox.warning(
                self, "Error",
                "Could not find a PDF viewer.\n\n"
                f"Guide location:\n{guide_path}"
            )
    
    def _get_page_width(self):
        w = self.width()
        if w > 100:
            return min(w - 60, 1200)
        return 900
    
    def _render_pages(self):
        guide_path = self._get_guide_path()
        if not guide_path:
            return
        
        t = self.theme.current
        page_width = self._get_page_width()
        
        # Clear existing
        while self.pages_layout.count():
            item = self.pages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # guide.pdf's tagged-accessibility structure tree is malformed
        # ("No common ancestor in structure tree"), which is harmless for
        # plain page rendering but otherwise spams stderr once per page.
        # Silence MuPDF's own error/warning output for the duration of the
        # render and restore it afterwards.
        fitz.TOOLS.mupdf_display_errors(False)
        try:
            doc = fitz.open(guide_path)
            
            # Ultra-high DPI for sharp images/screenshots
            dpi = 450
            zoom = dpi / 72
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                
                # Scale to exact page width with high-quality transformation
                scaled = pixmap.scaledToWidth(
                    page_width,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                page_label = QLabel()
                page_label.setPixmap(scaled)
                page_label.setFixedSize(scaled.size())
                page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                page_label.setStyleSheet("background: white; border: none;")
                self.pages_layout.addWidget(page_label)
                
                num_label = QLabel(f"{page_num + 1} / {len(doc)}")
                num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                num_label.setStyleSheet(
                    f"color:{t['text_tertiary']};font-size:10px;background:transparent;padding:2px;"
                )
                self.pages_layout.addWidget(num_label)
            
            doc.close()
            
        except Exception as e:
            error_label = QLabel(f"Error loading guide: {e}")
            error_label.setStyleSheet(
                f"color:{t['error']};font-size:14px;background:transparent;padding:20px;"
            )
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setWordWrap(True)
            self.pages_layout.addWidget(error_label)
        finally:
            fitz.TOOLS.mupdf_display_errors(True)
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)
        
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("User Guide")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setObjectName("actionButton")
        open_btn.setMaximumWidth(80)
        open_btn.clicked.connect(self._open_externally)
        
        # Fix: Add stretch on both sides of title to center it
        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(open_btn)
        
        layout.addLayout(header)
        
        guide_path = self._get_guide_path()
        t = self.theme.current
        
        # Pre-create scroll area and layout immediately
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ 
                border: none; 
                background: {t['crust']}; 
            }}
            QScrollBar:vertical {{
                background: {t['crust']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {t['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t['text_tertiary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.pages_widget = QWidget()
        self.pages_widget.setStyleSheet("background: transparent;")
        self.pages_layout = QVBoxLayout(self.pages_widget)
        self.pages_layout.setSpacing(8)
        self.pages_layout.setContentsMargins(20, 16, 20, 30)
        self.pages_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.scroll.setWidget(self.pages_widget)
        layout.addWidget(self.scroll)
        
        if guide_path:
            # Render immediately — no "loading" text
            self._do_initial_render()
        else:
            info = QLabel("User guide not found")
            info.setStyleSheet(f"color:{t['error']};font-size:14px;font-weight:600;background:transparent;padding:10px;")
            self.pages_layout.addWidget(info)
            
            hint = QLabel("Place guide.pdf in assets/docs/ directory")
            hint.setStyleSheet(f"color:{t['text_tertiary']};font-size:12px;background:transparent;padding:10px;")
            self.pages_layout.addWidget(hint)
            self.pages_layout.addStretch()
        
        self._apply_theme()
    
    def _do_initial_render(self):
        """Render pages instantly at the correct size."""
        self._render_pages()
        self._rendered = True
        self._last_width = self._get_page_width()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._rendered:
            new_width = self._get_page_width()
            old_width = getattr(self, '_last_width', 0)
            if abs(new_width - old_width) > 50:
                self._last_width = new_width
                self._render_pages()
    
    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"background-color:{t['base']};")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()