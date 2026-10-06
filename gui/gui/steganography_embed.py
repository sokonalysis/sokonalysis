# gui/steganography_embed.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QFormLayout, QCheckBox, QSpinBox, QProgressBar,
    QScrollArea, QTextBrowser, QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QPixmap, QIcon, QDrag, QPainter, QColor, QFont
import os, subprocess, time, sys
from gui.layout_manager import layout_manager


class EmbedWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str)
    
    def __init__(self, command, cover_file, data_file):
        super().__init__()
        self.command = command
        self.cover_file = cover_file
        self.data_file = data_file
    
    def run(self):
        try:
            self.progress.emit("Starting embedding process...")
            self.progress_value.emit(5)
            time.sleep(0.2)
            cover_name = os.path.basename(self.cover_file)
            data_name = os.path.basename(self.data_file)
            cover_size = os.path.getsize(self.cover_file)
            data_size = os.path.getsize(self.data_file)
            self.progress.emit(f"Cover: {cover_name} ({self._fmt_size(cover_size)})")
            self.progress.emit(f"Data: {data_name} ({self._fmt_size(data_size)})")
            self.progress_value.emit(15)
            output_file = self.cover_file
            for i, arg in enumerate(self.command):
                if arg == "-sf" and i + 1 < len(self.command):
                    output_file = self.command[i + 1]
                    break
            self.progress.emit(f"Output: {os.path.basename(output_file)}")
            self.progress_value.emit(25)
            self.progress.emit("Running steghide embed...")
            self.progress_value.emit(40)
            r = subprocess.run(self.command, capture_output=True, text=True, timeout=300)
            self.progress_value.emit(80)
            if r.returncode == 0:
                self.progress.emit("Embedding completed!")
                self.progress_value.emit(100)
                self.finished.emit(True, r.stdout, output_file)
            else:
                self.progress.emit("Embedding failed!")
                self.progress_value.emit(100)
                self.finished.emit(False, r.stderr or r.stdout, "")
        except subprocess.TimeoutExpired:
            self.progress.emit("Timed out")
            self.progress_value.emit(100)
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), "")
    
    def _fmt_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


class SteganographyEmbedPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.cover_path = ""
        self.data_path = ""
        self.output_path = ""
        self.sh_ok = self._chk("steghide")
        self.worker = None
        self.last_output_file = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def _chk(self, cmd):
        try:
            return subprocess.run([cmd, "--version"], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return False
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                ext = os.path.splitext(filepath)[1].lower()
                if ext in ['.jpg', '.jpeg', '.bmp', '.wav', '.au']:
                    self.cover_path = filepath
                    self.cover_path_input.setText(filepath)
                    self._update_cover_preview()
                else:
                    self.data_path = filepath
                    self.data_path_input.setText(filepath)
                    self._update_data_preview()
                self.execute_btn.setEnabled(self.sh_ok and bool(self.cover_path) and bool(self.data_path))
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
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
        
        title = QLabel("Embed Data into File")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        sh_container = QHBoxLayout()
        sh_container.setSpacing(4)
        self.sh_icon = QLabel()
        self.sh_icon.setFixedSize(18, 18)
        self.sh_icon.setStyleSheet("background:transparent;")
        self.tool_badge = QLabel()
        self._update_tool_badge()
        sh_container.addWidget(self.sh_icon)
        sh_container.addWidget(self.tool_badge)
        header.addLayout(sh_container)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_requirements_tab(), "Requirements")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _update_tool_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.sh_ok:
            self.tool_badge.setText("Steghide Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "steghide.png")
        else:
            self.tool_badge.setText("Steghide Missing")
            c = t['error']
            icon_path = os.path.join(icons_dir, "no.png")
        self.tool_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'sh_icon'):
            self.sh_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Cover file
        self.cover_group = QGroupBox("1. Cover File (Image/Audio)")
        cover_layout = QVBoxLayout()
        self.cover_preview = QLabel()
        self.cover_preview.setFixedHeight(100)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setText("Drag & drop or click Browse\nto select an image or audio file")
        cover_layout.addWidget(self.cover_preview)
        cover_row = QHBoxLayout()
        self.cover_path_input = QLineEdit()
        self.cover_path_input.setReadOnly(True)
        self.cover_path_input.setPlaceholderText("Select cover file (jpg, bmp, wav, au)...")
        cover_btn = QPushButton("Browse")
        cover_btn.setObjectName("actionButton")
        cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cover_btn.clicked.connect(lambda: self._browse_file("cover"))
        cover_row.addWidget(self.cover_path_input, 1)
        cover_row.addWidget(cover_btn)
        cover_layout.addLayout(cover_row)
        self.cover_info = QLabel("")
        cover_layout.addWidget(self.cover_info)
        self.cover_group.setLayout(cover_layout)
        layout.addWidget(self.cover_group)
        
        # Data file
        self.data_group = QGroupBox("2. Data File to Hide")
        data_layout = QVBoxLayout()
        self.data_preview = QLabel()
        self.data_preview.setFixedHeight(80)
        self.data_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.data_preview.setText("Drag & drop or click Browse\nto select the file to hide")
        data_layout.addWidget(self.data_preview)
        data_row = QHBoxLayout()
        self.data_path_input = QLineEdit()
        self.data_path_input.setReadOnly(True)
        self.data_path_input.setPlaceholderText("Select data file to embed...")
        data_btn = QPushButton("Browse")
        data_btn.setObjectName("actionButton")
        data_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        data_btn.clicked.connect(lambda: self._browse_file("data"))
        data_row.addWidget(self.data_path_input, 1)
        data_row.addWidget(data_btn)
        data_layout.addLayout(data_row)
        self.data_info = QLabel("")
        data_layout.addWidget(self.data_info)
        self.data_group.setLayout(data_layout)
        layout.addWidget(self.data_group)
        
        # Options
        self.options_group = QGroupBox("3. Options")
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        
        pass_row = QHBoxLayout()
        pass_label = QLabel("Password:")
        pass_label.setMinimumWidth(80)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Optional - encrypt with password")
        pass_paste = QPushButton("Paste")
        pass_paste.setObjectName("actionButton")
        pass_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        pass_paste.clicked.connect(lambda: self._paste_to(self.password_input))
        pass_clear = QPushButton("Clear")
        pass_clear.setObjectName("dangerButton")
        pass_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        pass_clear.clicked.connect(self.password_input.clear)
        pass_row.addWidget(pass_label)
        pass_row.addWidget(self.password_input, 1)
        pass_row.addWidget(pass_paste)
        pass_row.addWidget(pass_clear)
        options_layout.addLayout(pass_row)
        
        self.show_pass = QCheckBox("Show password")
        self.show_pass.stateChanged.connect(
            lambda s: self.password_input.setEchoMode(
                QLineEdit.EchoMode.Normal if s == Qt.CheckState.Checked.value
                else QLineEdit.EchoMode.Password
            )
        )
        options_layout.addWidget(self.show_pass)
        
        self.use_custom_output = QCheckBox("Create separate output file (recommended)")
        self.use_custom_output.stateChanged.connect(self._toggle_output)
        options_layout.addWidget(self.use_custom_output)
        
        output_row = QHBoxLayout()
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("stego_output.jpg")
        self.output_input.setEnabled(False)
        output_row.addWidget(self.output_input, 1)
        self.output_browse_btn = QPushButton("Browse")
        self.output_browse_btn.setObjectName("actionButton")
        self.output_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_browse_btn.clicked.connect(lambda: self._browse_file("output"))
        self.output_browse_btn.setEnabled(False)
        output_row.addWidget(self.output_browse_btn)
        options_layout.addLayout(output_row)
        
        self.use_compression = QCheckBox("Use compression")
        self.use_compression.stateChanged.connect(self._toggle_compression)
        options_layout.addWidget(self.use_compression)
        
        comp_row = QHBoxLayout()
        comp_label = QLabel("Compression level:")
        comp_label.setMinimumWidth(120)
        self.compression_level = QSpinBox()
        self.compression_level.setRange(1, 9)
        self.compression_level.setValue(9)
        self.compression_level.setEnabled(False)
        self.compression_level.setMinimumWidth(90)
        self.compression_level.setMaximumWidth(120)
        self.compression_level.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compression_level.setFixedHeight(36)
        comp_row.addWidget(comp_label)
        comp_row.addWidget(self.compression_level)
        comp_row.addStretch()
        options_layout.addLayout(comp_row)
        
        self.options_group.setLayout(options_layout)
        layout.addWidget(self.options_group)
        
        self.execute_btn = QPushButton("Embed Data")
        self.execute_btn.setObjectName("actionButton")
        # Don't set a hardcoded height here; let _apply_theme() size it from font_scale()
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute_embed)
        self.execute_btn.setEnabled(self.sh_ok and bool(self.cover_path) and bool(self.data_path))
        layout.addWidget(self.execute_btn)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        self.embed_progress = QProgressBar()
        self.embed_progress.setRange(0, 100)
        self.embed_progress.setValue(0)
        self.embed_progress.setTextVisible(True)
        self.embed_progress.setFormat("%p%")
        self.embed_progress.setMinimumHeight(28)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        layout.addWidget(self.embed_progress)
        layout.addWidget(self.status_output)
        return widget
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.res_grp = QGroupBox("Result")
        rl = QVBoxLayout()
        rl.setSpacing(12)
        
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Stego File:"))
        rh.addStretch()
        self.export_btn = QPushButton("Export File")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_result)
        rh.addWidget(self.export_btn)
        rl.addLayout(rh)
        
        self.result_preview = QLabel()
        self.result_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_preview.setMinimumHeight(220)
        self.result_preview.setText("No results yet")
        rl.addWidget(self.result_preview, 1)
        
        self.result_info = QLabel("")
        self.result_info.setWordWrap(True)
        self.result_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self.result_info)
        
        self.res_grp.setLayout(rl)
        layout.addWidget(self.res_grp, 1)
        return widget
    
    def _create_requirements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)
        
        self.req_group = QGroupBox("Required Tools")
        req_layout = QVBoxLayout()
        req_layout.setSpacing(10)
        
        self.req_output = QTextBrowser()
        self.req_output.setOpenExternalLinks(False)
        req_layout.addWidget(self.req_output)
        
        self.install_btn = QPushButton("Install Steghide")
        self.install_btn.setObjectName("actionButton")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._install_steghide)
        req_layout.addWidget(self.install_btn)
        
        self.install_status = QLabel("")
        req_layout.addWidget(self.install_status)
        
        self.req_group.setLayout(req_layout)
        layout.addWidget(self.req_group)
        layout.addStretch()
        self._update_requirements_display()
        return widget
    
    def _update_requirements_display(self):
        t = self.theme.current
        if self.sh_ok:
            self.req_output.setHtml(
                f"<h3 style='color:{t['success']};'>steghide</h3>"
                f"<p>Status: <span style='color:{t['success']};'>Installed</span></p>"
            )
            self.install_btn.setEnabled(False)
            self.install_btn.setText("Installed")
        else:
            self.req_output.setHtml(
                f"<h3 style='color:{t['error']};'>steghide</h3>"
                f"<p>Status: <span style='color:{t['error']};'>Not Installed</span></p>"
                f"<p>Run: <code>sudo apt install steghide</code></p>"
            )
            self.install_btn.setEnabled(True)
            self.install_btn.setText("Install Steghide")
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['cover_group', 'data_group', 'options_group', 'req_group', 'res_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        # Explicitly scale the primary action button so its text never clips
        if hasattr(self, 'execute_btn') and self.execute_btn is not None:
            min_h = max(48, int(56 * scale))
            self.execute_btn.setMinimumHeight(min_h)
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['cover_path_input', 'data_path_input', 'password_input', 'output_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(
                f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
            )
        
        if hasattr(self, 'req_output') and self.req_output is not None:
            self.req_output.setStyleSheet(
                f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-size:{int(12 * scale)}px;}}"
            )
        
        if hasattr(self, 'embed_progress') and self.embed_progress is not None:
            self.embed_progress.setStyleSheet(
                f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'cover_preview') and self.cover_preview is not None:
            self.cover_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        if hasattr(self, 'data_preview') and self.data_preview is not None:
            self.data_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        if hasattr(self, 'result_preview') and self.result_preview is not None:
            self.result_preview.setStyleSheet(
                f"border:2px solid {t['border']};border-radius:8px;background-color:{t['crust']};"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        
        cb_style = (
            f"QCheckBox{{color:{t['text']};font-size:{int(12 * scale)}px;}} "
            f"QCheckBox::indicator{{width:16px;height:16px;border:2px solid {t['border']};"
            f"border-radius:3px;background:{t['crust']};}} "
            f"QCheckBox::indicator:checked{{background:{t['accent']};border-color:{t['accent']};}}"
        )
        for attr in ['show_pass', 'use_custom_output', 'use_compression']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(cb_style)
                except RuntimeError:
                    pass
        
        # Compression level spinbox: centered digit + visible CSS-triangle arrows
        if hasattr(self, 'compression_level') and self.compression_level is not None:
            sp_font = max(12, int(13 * scale))
            arrow_w = max(18, int(20 * scale))
            self.compression_level.setFixedHeight(max(32, int(36 * scale)))
            self.compression_level.setStyleSheet(
                f"QSpinBox{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;"
                f"padding:0px 10px;"
                f"font-size:{sp_font}px;}} "
                f"QSpinBox::up-button {{"
                f"  subcontrol-origin: border;"
                f"  subcontrol-position: top right;"
                f"  width:{arrow_w}px;"
                f"  background:{t['surface0']};"
                f"  border-left:1px solid {t['border']};"
                f"  border-top-right-radius:6px;"
                f"  border-bottom:1px solid {t['border']};"
                f"}} "
                f"QSpinBox::down-button {{"
                f"  subcontrol-origin: border;"
                f"  subcontrol-position: bottom right;"
                f"  width:{arrow_w}px;"
                f"  background:{t['surface0']};"
                f"  border-left:1px solid {t['border']};"
                f"  border-bottom-right-radius:6px;"
                f"}} "
                f"QSpinBox::up-arrow {{"
                f"  width:0; height:0;"
                f"  border-left:4px solid transparent;"
                f"  border-right:4px solid transparent;"
                f"  border-bottom:5px solid {t['text']};"
                f"}} "
                f"QSpinBox::down-arrow {{"
                f"  width:0; height:0;"
                f"  border-left:4px solid transparent;"
                f"  border-right:4px solid transparent;"
                f"  border-top:5px solid {t['text']};"
                f"}}"
            )
        
        info_style = f"color:{t['text_tertiary']};font-size:{int(11 * scale)}px;background:transparent;"
        for attr in ['cover_info', 'data_info']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(info_style)
                except RuntimeError:
                    pass
        if hasattr(self, 'result_info') and self.result_info is not None:
            self.result_info.setStyleSheet(
                f"color:{t['text']};font-size:{int(13 * scale)}px;background:transparent;"
            )
        
        self._update_tool_badge()
        if hasattr(self, 'req_output'):
            self._update_requirements_display()
    
    def _toggle_output(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.output_input.setEnabled(enabled)
        self.output_browse_btn.setEnabled(enabled)
    
    def _toggle_compression(self, state):
        self.compression_level.setEnabled(state == Qt.CheckState.Checked.value)
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setText(clipboard)
    
    def _browse_file(self, file_type):
        if file_type == "cover":
            fp, _ = QFileDialog.getOpenFileName(
                self, "Select Cover File", "",
                "Image/Audio Files (*.jpg *.jpeg *.bmp *.wav *.au);;All Files (*)"
            )
            if fp:
                self.cover_path = fp
                self.cover_path_input.setText(fp)
                self._update_cover_preview()
        elif file_type == "data":
            fp, _ = QFileDialog.getOpenFileName(self, "Select Data File to Hide", "", "All Files (*)")
            if fp:
                self.data_path = fp
                self.data_path_input.setText(fp)
                self._update_data_preview()
        elif file_type == "output":
            fp, _ = QFileDialog.getSaveFileName(
                self, "Select Output File", "",
                "Image/Audio Files (*.jpg *.jpeg *.bmp *.wav *.au);;All Files (*)"
            )
            if fp:
                self.output_input.setText(fp)
        self.execute_btn.setEnabled(self.sh_ok and bool(self.cover_path) and bool(self.data_path))
    
    def _update_cover_preview(self):
        if not self.cover_path or not os.path.exists(self.cover_path):
            self.cover_preview.setText("Drag & drop or click Browse\nto select an image or audio file")
            self.cover_info.setText("")
            return
        filename = os.path.basename(self.cover_path)
        size = os.path.getsize(self.cover_path)
        ext = os.path.splitext(self.cover_path)[1].lower()
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        if ext in ['.jpg', '.jpeg', '.bmp']:
            pixmap = QPixmap(self.cover_path)
            if not pixmap.isNull():
                scaled = pixmap.scaledToHeight(90, Qt.TransformationMode.SmoothTransformation)
                self.cover_preview.setPixmap(scaled)
            else:
                self.cover_preview.setText(f"Image File\n{filename}")
        elif ext == '.wav':
            self.cover_preview.setText(f"Audio File (WAV)\n{filename}")
        elif ext == '.au':
            self.cover_preview.setText(f"Audio File (AU)\n{filename}")
        else:
            self.cover_preview.setText(f"File\n{filename}")
        self.cover_info.setText(f"Size: {size_str} | Format: {ext.upper().replace('.', '')}")
    
    def _update_data_preview(self):
        if not self.data_path or not os.path.exists(self.data_path):
            self.data_preview.setText("Drag & drop or click Browse\nto select the file to hide")
            self.data_info.setText("")
            return
        filename = os.path.basename(self.data_path)
        size = os.path.getsize(self.data_path)
        ext = os.path.splitext(self.data_path)[1].lower()
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        if ext == '.txt':
            try:
                with open(self.data_path, 'r', encoding='utf-8', errors='ignore') as f:
                    preview = f.read(150)
                self.data_preview.setText(f"Text File\n{preview}")
            except:
                self.data_preview.setText(f"File\n{filename}")
        else:
            self.data_preview.setText(f"File\n{filename}")
        self.data_info.setText(f"Size: {size_str} | Type: {ext if ext else 'unknown'}")
    
    def _install_steghide(self):
        reply = QMessageBox.question(
            self, "Install Steghide",
            "Install steghide?\n\nsudo apt install -y steghide",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Installing...")
        self.install_status.setText("Running: sudo apt install -y steghide")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "steghide"], capture_output=True, text=True, timeout=120)
            self.sh_ok = self._chk("steghide")
            self.install_status.setText("Done!" if self.sh_ok else "Failed")
        except Exception as e:
            self.install_status.setText(f"Error: {str(e)}")
        self._update_tool_badge()
        self._update_requirements_display()
        self.execute_btn.setEnabled(self.sh_ok and bool(self.cover_path) and bool(self.data_path))
    
    def _execute_embed(self):
        if not self.cover_path or not self.data_path:
            QMessageBox.warning(self, "Missing Files", "Please select both files")
            return
        cmd = ["steghide", "embed", "-ef", self.data_path, "-cf", self.cover_path, "-f"]
        if self.use_custom_output.isChecked() and self.output_input.text():
            cmd.extend(["-sf", self.output_input.text()])
            self.output_path = self.output_input.text()
        else:
            self.output_path = self.cover_path
        if self.password_input.text():
            cmd.extend(["-p", self.password_input.text()])
        if self.use_compression.isChecked():
            cmd.extend(["-z", str(self.compression_level.value())])
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.embed_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        self.worker = EmbedWorker(cmd, self.cover_path, self.data_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.embed_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, message):
        self.status_output.append(message)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, message, output_file):
        self.execute_btn.setEnabled(True)
        self.last_output_file = output_file
        if success:
            self.status_output.append("SUCCESS!")
            self.embed_progress.setValue(100)
            self._update_result_preview(output_file)
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                self.result_info.setText(
                    f"Output: {os.path.basename(output_file)}\nSize: {size_str}"
                )
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR:\n{message}")
            self.embed_progress.setValue(100)
    
    def _update_result_preview(self, output_file):
        if not output_file or not os.path.exists(output_file):
            self.result_preview.setText("No output file")
            return
        ext = os.path.splitext(output_file)[1].lower()
        if ext in ['.jpg', '.jpeg', '.bmp']:
            pixmap = QPixmap(output_file)
            if not pixmap.isNull():
                scaled = pixmap.scaledToHeight(200, Qt.TransformationMode.SmoothTransformation)
                self.result_preview.setPixmap(scaled)
            else:
                self.result_preview.setText(f"Image: {os.path.basename(output_file)}")
        else:
            self.result_preview.setText(f"File: {os.path.basename(output_file)}")
    
    def _export_result(self):
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            QMessageBox.warning(self, "No File", "No result file to export. Run embedding first.")
            return
        export_path, _ = QFileDialog.getSaveFileName(
            self, "Export Stego File", os.path.basename(self.last_output_file),
            "Image/Audio Files (*.jpg *.jpeg *.bmp *.wav *.au);;All Files (*)"
        )
        if export_path:
            try:
                import shutil
                shutil.copy2(self.last_output_file, export_path)
                QMessageBox.information(self, "Exported", f"File saved to:\n{export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
    
    def set_wordlist_config(self, wp, sp):
        pass
    
    def refresh_theme(self):
        self._apply_theme()