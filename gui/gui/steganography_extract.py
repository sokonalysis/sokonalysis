# gui/steganography_extract.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QCheckBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
import os, subprocess, time, re, shutil
from datetime import datetime
import sys
from gui.layout_manager import layout_manager


class ExtractWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str)
    
    def __init__(self, stego_file, output_file, password=""):
        super().__init__()
        self.stego_file = stego_file
        self.output_file = output_file
        self.password = password
    
    def run(self):
        try:
            self.progress.emit("Starting extraction...")
            self.progress_value.emit(10)
            time.sleep(0.2)
            self.progress.emit(f"Stego file: {os.path.basename(self.stego_file)}")
            if self.password:
                self.progress.emit(f"Password: {self.password}")
            else:
                self.progress.emit("No password (extracting without passphrase)")
            self.progress_value.emit(25)
            self.progress.emit("Running steghide extract...")
            self.progress_value.emit(40)
            cmd = ["steghide", "extract", "-sf", self.stego_file, "-xf", self.output_file, "-f"]
            if self.password:
                cmd.extend(["-p", self.password])
            else:
                cmd.extend(["-p", ""])
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            self.progress_value.emit(80)
            if r.returncode == 0:
                self.progress.emit("Extraction completed!")
                self.progress_value.emit(100)
                content = ""
                if os.path.exists(self.output_file):
                    try:
                        with open(self.output_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except:
                        content = "BINARY"
                self.finished.emit(True, content, self.output_file)
            else:
                error = r.stderr.strip() if r.stderr else r.stdout.strip()
                self.progress.emit(f"Extraction failed: {error}")
                self.progress_value.emit(100)
                self.finished.emit(False, error, "")
        except subprocess.TimeoutExpired:
            self.progress.emit("Timed out")
            self.progress_value.emit(100)
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), "")


class StegseekWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str, str)
    
    def __init__(self, stego_file, wordlist):
        super().__init__()
        self.stego_file = stego_file
        self.wordlist = wordlist
    
    def _count_words(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def run(self):
        try:
            word_count = self._count_words(self.wordlist)
            self.progress.emit(f"Wordlist: {word_count:,} words")
            self.progress.emit(f"Stego file: {os.path.basename(self.stego_file)}")
            self.progress_value.emit(15)
            self.progress.emit("Running stegseek...")
            self.progress_value.emit(25)
            process = subprocess.Popen(
                ["stegseek", self.stego_file, self.wordlist],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            password_found = None
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line:
                    if "overwrite ?" in line.lower():
                        try:
                            process.stdin.write('y\n')
                            process.stdin.flush()
                        except:
                            pass
                        continue
                    self.progress.emit(line)
                    if "found passphrase:" in line.lower():
                        match = re.search(r'found passphrase:?\s*["\']?([^"\'\n]+)["\']?', line, re.IGNORECASE)
                        if match:
                            password_found = match.group(1).strip()
            process.wait()
            self.progress_value.emit(90)
            stegseek_output = f"{self.stego_file}.out"
            if os.path.exists(stegseek_output):
                self.progress_value.emit(100)
                if password_found:
                    self.progress.emit(f"Password found: {password_found}")
                    content = ""
                    try:
                        with open(stegseek_output, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().strip()
                    except:
                        content = "BINARY"
                    self.progress.emit("Match found!")
                    self.finished.emit(True, content, stegseek_output, password_found)
                else:
                    try:
                        os.remove(stegseek_output)
                    except:
                        pass
                    self.progress.emit("No match found")
                    self.finished.emit(True, "No match found", "", "")
            elif password_found:
                self.progress_value.emit(100)
                self.progress.emit(f"Password found: {password_found}")
                self.finished.emit(True, f"Password: {password_found}", "", password_found)
            else:
                self.progress_value.emit(100)
                self.progress.emit("No match found")
                self.finished.emit(True, "No match found", "", "")
        except FileNotFoundError:
            self.progress.emit("Stegseek not found")
            self.progress_value.emit(100)
            self.finished.emit(False, "Stegseek not found", "", "")
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), "", "")


class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(140, int(180 * scale))
        h = max(56, int(70 * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(40 * scale), h + int(20 * scale))
    
    def _build(self, name):
        t = self.colors
        scale = layout_manager.font_scale()
        # Clear existing layout
        if self.layout() is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(
                int(14 * scale), int(12 * scale),
                int(14 * scale), int(12 * scale)
            )
            layout.setSpacing(int(4 * scale))
            self.name_label = QLabel(name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            layout.addWidget(self.name_label)
        else:
            if self.name_label is not None:
                self.name_label.setText(name)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(13 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._apply_scaled_size()
        self._build(self.mode_name)
        self.update()
        self.repaint()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self._placeholder = "Drag operation here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(200, text_w)
        max_w = min_w + int(80 * scale)
        h = max(72, int(90 * scale))
        self.setMinimumSize(min_w, h)
        self.setMaximumSize(max_w, h + int(20 * scale))
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}"
        )
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}"
        )
    
    def is_filled(self):
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        try:
            mode_id, mode_name = data.split(':', 1)
            self.mode_id = int(mode_id)
            self.mode_name = mode_name
            self._style_filled()
            self.update()
            self.repaint()
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, SteganographyExtractPage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(11, int(13 * scale))
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size, QFont.Weight.Bold))
            text = self.mode_name
        else:
            font_size = max(9, int(10 * scale))
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size))
            text = self._placeholder
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = painter.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, SteganographyExtractPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class SteganographyExtractPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.stego_path = ""
        self.sh_ok = self._chk("steghide")
        self.ss_ok = self._chk_stegseek()
        self.worker = None
        self.mode_cards = []
        self.last_output_file = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def _chk(self, cmd):
        try:
            return subprocess.run([cmd, "--version"], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return False
    
    def _chk_stegseek(self):
        try:
            return subprocess.run(["stegseek", "--version"], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return shutil.which("stegseek") is not None
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                self.stego_path = filepath
                self.stego_path_input.setText(filepath)
                self._update_stego_preview()
                hw = bool(self.wordlist_path and os.path.exists(self.wordlist_path))
                self.execute_btn.setEnabled(
                    self.mode_slot.is_filled() and self.sh_ok and
                    (self.mode_slot.mode_id != 3 or hw)
                )
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
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
        
        title = QLabel("Extract Data from File")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        wl_container = QHBoxLayout()
        wl_container.setSpacing(4)
        self.wl_icon = QLabel()
        self.wl_icon.setFixedSize(18, 18)
        self.wl_icon.setStyleSheet("background:transparent;")
        self.wordlist_badge = QLabel()
        self._update_wordlist_badge()
        wl_container.addWidget(self.wl_icon)
        wl_container.addWidget(self.wordlist_badge)
        header.addLayout(wl_container)
        
        tools_container = QHBoxLayout()
        tools_container.setSpacing(4)
        self.tools_icon = QLabel()
        self.tools_icon.setFixedSize(18, 18)
        self.tools_icon.setStyleSheet("background:transparent;")
        self.tool_badge = QLabel()
        self._update_tool_badge()
        tools_container.addWidget(self.tools_icon)
        tools_container.addWidget(self.tool_badge)
        header.addLayout(tools_container)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_requirements_tab(), "Requirements")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _update_wordlist_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.wordlist_path and os.path.exists(self.wordlist_path):
            self.wordlist_badge.setText("Wordlist Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.wordlist_badge.setText("No Wordlist")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        self.wordlist_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'wl_icon'):
            self.wl_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _update_tool_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        tools_ok = self.sh_ok and self.ss_ok
        if tools_ok:
            self.tool_badge.setText("Tools Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "tools.png")
        else:
            self.tool_badge.setText("Missing Tools")
            c = t['error']
            icon_path = os.path.join(icons_dir, "no.png")
        self.tool_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'tools_icon'):
            self.tools_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        self.stego_group = QGroupBox("1. Stego File (Image/Audio)")
        stego_layout = QVBoxLayout()
        self.stego_preview = QLabel()
        self.stego_preview.setFixedHeight(120)
        self.stego_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stego_preview.setText("Drag & drop or click Browse\nto select an image or audio file")
        stego_layout.addWidget(self.stego_preview)
        stego_row = QHBoxLayout()
        self.stego_path_input = QLineEdit()
        self.stego_path_input.setReadOnly(True)
        self.stego_path_input.setPlaceholderText("Select stego file (jpg, bmp, wav, au)...")
        stego_btn = QPushButton("Browse")
        stego_btn.setObjectName("actionButton")
        stego_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stego_btn.clicked.connect(self._browse_file)
        stego_row.addWidget(self.stego_path_input, 1)
        stego_row.addWidget(stego_btn)
        stego_layout.addLayout(stego_row)
        self.stego_info = QLabel("")
        stego_layout.addWidget(self.stego_info)
        self.stego_group.setLayout(stego_layout)
        layout.addWidget(self.stego_group)
        
        self.mode_group = QGroupBox("2. Operation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        t = self.theme.current
        for mode_id, name in [(1, "No Password"), (2, "Known Password"), (3, "Brute Force")]:
            card = DraggableModeCard(mode_id, name, t)
            self.mode_cards.append(card)
            cards_row.addWidget(card)
        cards_row.addStretch()
        mode_layout.addLayout(cards_row)
        drop_row = QHBoxLayout()
        self.mode_slot = ModeDropSlot(t)
        drop_row.addWidget(self.mode_slot)
        drop_row.addStretch()
        mode_layout.addLayout(drop_row)
        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)
        
        self.options_group = QGroupBox("3. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
        # Height will be set in _apply_theme() based on font_scale
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        self.execute_btn.setEnabled(False)
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
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        layout.addWidget(self.status_progress)
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
        rh.addWidget(QLabel("Output:"))
        rh.addStretch()
        self.export_btn = QPushButton("Export File")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_result)
        self.export_btn.hide()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        rh.addWidget(self.export_btn)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        
        self.result_preview = QLabel()
        self.result_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_preview.setMinimumHeight(200)
        self.result_preview.hide()
        rl.addWidget(self.result_preview)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Result will appear here...")
        rl.addWidget(self.results_output, 1)
        
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
        self.install_btn = QPushButton("Install Requirements")
        self.install_btn.setObjectName("actionButton")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._install_tools)
        req_layout.addWidget(self.install_btn)
        self.install_status = QLabel("")
        req_layout.addWidget(self.install_status)
        self.req_group.setLayout(req_layout)
        layout.addWidget(self.req_group)
        layout.addStretch()
        self._update_requirements()
        return widget
    
    def _update_requirements(self):
        t = self.theme.current
        html = ""
        for name, ok in [("steghide", self.sh_ok), ("stegseek", self.ss_ok)]:
            c = t['success'] if ok else t['error']
            html += f"<h3 style='color:{c};'>{name}</h3>"
        html += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install steghide stegseek</p>"
        self.req_output.setHtml(html)
        all_ok = self.sh_ok and self.ss_ok
        self.install_btn.setEnabled(not all_ok)
        self.install_btn.setText("All Tools Installed" if all_ok else "Install Requirements")
    
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
        for attr in ['stego_group', 'mode_group', 'options_group', 'req_group', 'res_grp']:
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
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        if hasattr(self, 'stego_path_input') and self.stego_path_input is not None:
            self.stego_path_input.setStyleSheet(input_style)
        if hasattr(self, 'password_input') and self.password_input is not None:
            try:
                self.password_input.setStyleSheet(input_style)
            except RuntimeError:
                pass
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(ts)
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setStyleSheet(
                f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
            )
        if hasattr(self, 'req_output') and self.req_output is not None:
            self.req_output.setStyleSheet(
                f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-size:{int(12 * scale)}px;}}"
            )
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
            )
        if hasattr(self, 'stego_preview') and self.stego_preview is not None:
            self.stego_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        if hasattr(self, 'result_preview') and self.result_preview is not None:
            self.result_preview.setStyleSheet("background:transparent;")
        
        if hasattr(self, 'show_pass') and self.show_pass is not None:
            try:
                self.show_pass.setStyleSheet(
                    f"QCheckBox{{color:{t['text']};font-size:{int(12 * scale)}px;}} "
                    f"QCheckBox::indicator{{width:16px;height:16px;border:2px solid {t['border']};"
                    f"border-radius:3px;background:{t['crust']};}} "
                    f"QCheckBox::indicator:checked{{background:{t['accent']};border-color:{t['accent']};}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            self.mode_slot.update_colors(t)
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        info_style = f"color:{t['text_tertiary']};font-size:{int(11 * scale)}px;background:transparent;"
        if hasattr(self, 'stego_info') and self.stego_info is not None:
            self.stego_info.setStyleSheet(info_style)
        if hasattr(self, 'wordlist_status_label') and self.wordlist_status_label is not None:
            try:
                self.wordlist_status_label.setStyleSheet(
                    f"color:{t['text_secondary']};background:transparent;font-size:{int(12 * scale)}px;"
                )
            except RuntimeError:
                pass
        
        self._update_wordlist_badge()
        self._update_tool_badge()
        if hasattr(self, 'req_output'):
            self._update_requirements()
    
    def _on_mode_dropped(self):
        mode_id = self.mode_slot.mode_id
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        if hasattr(self, 'password_input'):
            delattr(self, 'password_input')
        if hasattr(self, 'show_pass'):
            delattr(self, 'show_pass')
        if hasattr(self, 'wordlist_status_label'):
            delattr(self, 'wordlist_status_label')
        
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        if mode_id == 1:  # No Password
            self.options_group.setVisible(True)
            info_lbl = QLabel("No password will be used for extraction.")
            info_lbl.setStyleSheet(f"color:{t['text_secondary']};background:transparent;")
            self.options_layout.addWidget(info_lbl)
            self.execute_btn.setText("Extract (No Password)")
            self.execute_btn.setEnabled(bool(self.stego_path) and self.sh_ok)
        
        elif mode_id == 2:  # Known Password
            self.options_group.setVisible(True)
            pr = QHBoxLayout()
            pl = QLabel("Password:")
            pl.setMinimumWidth(int(80 * scale))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_input.setPlaceholderText("Enter password for extraction")
            paste_btn = QPushButton("Paste")
            paste_btn.setObjectName("actionButton")
            paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            paste_btn.clicked.connect(lambda: self._paste_to(self.password_input))
            clear_btn = QPushButton("Clear")
            clear_btn.setObjectName("dangerButton")
            clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_btn.clicked.connect(self.password_input.clear)
            pr.addWidget(pl)
            pr.addWidget(self.password_input, 1)
            pr.addWidget(paste_btn)
            pr.addWidget(clear_btn)
            self.options_layout.addLayout(pr)
            
            self.show_pass = QCheckBox("Show password")
            self.show_pass.stateChanged.connect(
                lambda s: self.password_input.setEchoMode(
                    QLineEdit.EchoMode.Normal if s == Qt.CheckState.Checked.value else QLineEdit.EchoMode.Password
                )
            )
            self.options_layout.addWidget(self.show_pass)
            self.execute_btn.setText("Extract with Password")
            self.execute_btn.setEnabled(bool(self.stego_path) and self.sh_ok)
        
        elif mode_id == 3:  # Brute Force
            self.options_group.setVisible(True)
            ws = QHBoxLayout()
            wl = QLabel("Wordlist:")
            wl.setMinimumWidth(int(80 * scale))
            wt = os.path.basename(self.wordlist_path) if (self.wordlist_path and os.path.exists(self.wordlist_path)) else "No wordlist configured"
            self.wordlist_status_label = QLabel(wt)
            self.wordlist_status_label.setWordWrap(True)
            self.wordlist_status_label.setStyleSheet(
                f"color:{t['text_secondary']};background:transparent;font-size:{int(12 * scale)}px;"
            )
            ws.addWidget(wl)
            ws.addWidget(self.wordlist_status_label, 1)
            self.options_layout.addLayout(ws)
            hw = bool(self.wordlist_path and os.path.exists(self.wordlist_path))
            self.execute_btn.setText("Start Brute Force")
            self.execute_btn.setEnabled(bool(self.stego_path) and self.sh_ok and self.ss_ok and hw)
        
        self._apply_theme()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setText(clipboard)
    
    def _on_mode_cleared(self):
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        if hasattr(self, 'password_input'):
            delattr(self, 'password_input')
        if hasattr(self, 'show_pass'):
            delattr(self, 'show_pass')
        if hasattr(self, 'wordlist_status_label'):
            delattr(self, 'wordlist_status_label')
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _browse_file(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "Select Stego File", "",
            "Image/Audio Files (*.jpg *.jpeg *.bmp *.wav *.au);;All Files (*)"
        )
        if fp:
            self.stego_path = fp
            self.stego_path_input.setText(fp)
            self._update_stego_preview()
            hw = bool(self.wordlist_path and os.path.exists(self.wordlist_path))
            self.execute_btn.setEnabled(
                self.mode_slot.is_filled() and self.sh_ok and
                (self.mode_slot.mode_id != 3 or hw)
            )
    
    def _update_stego_preview(self):
        if not self.stego_path or not os.path.exists(self.stego_path):
            self.stego_preview.setText("Drag & drop or click Browse\nto select an image or audio file")
            self.stego_info.setText("")
            return
        fn = os.path.basename(self.stego_path)
        sz = os.path.getsize(self.stego_path)
        ext = os.path.splitext(self.stego_path)[1].lower()
        ss = f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
        if ext in ['.jpg', '.jpeg', '.bmp']:
            pm = QPixmap(self.stego_path)
            if not pm.isNull():
                self.stego_preview.setPixmap(pm.scaledToHeight(110, Qt.TransformationMode.SmoothTransformation))
            else:
                self.stego_preview.setText(f"Image File\n{fn}")
        elif ext == '.wav':
            self.stego_preview.setText(f"Audio (WAV)\n{fn}")
        elif ext == '.au':
            self.stego_preview.setText(f"Audio (AU)\n{fn}")
        else:
            self.stego_preview.setText(f"File\n{fn}")
        self.stego_info.setText(f"Size: {ss} | Format: {ext.upper().replace('.','')}")
    
    def _install_tools(self):
        if QMessageBox.question(
            self, "Install Tools",
            "Install steghide and stegseek?\n\nsudo apt install -y steghide stegseek",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Installing...")
        self.install_status.setText("Running: sudo apt install -y steghide stegseek")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "steghide", "stegseek"], capture_output=True, text=True, timeout=120)
            self.sh_ok = self._chk("steghide")
            self.ss_ok = self._chk_stegseek()
            self.install_status.setText("Done!" if (self.sh_ok and self.ss_ok) else "Failed")
        except Exception as e:
            self.install_status.setText(f"Error: {e}")
        self._update_tool_badge()
        self._update_requirements()
        hw = bool(self.wordlist_path and os.path.exists(self.wordlist_path))
        self.execute_btn.setEnabled(
            self.mode_slot.is_filled() and self.sh_ok and bool(self.stego_path) and
            (self.mode_slot.mode_id != 3 or hw)
        )
    
    def _execute(self):
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        if not self.stego_path:
            QMessageBox.warning(self, "Missing File", "Select a stego file")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.result_preview.hide()
        self.export_btn.hide()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        
        mode_id = self.mode_slot.mode_id
        if mode_id == 1:
            self._execute_extract_no_password()
        elif mode_id == 2:
            self._execute_extract()
        else:
            self._execute_bruteforce()
    
    def _execute_extract_no_password(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = f"extracted_{ts}.txt"
        self.worker = ExtractWorker(self.stego_path, out, "")
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_extract_finished)
        self.worker.start()
    
    def _execute_extract(self):
        pw = self.password_input.text() if hasattr(self, 'password_input') else ""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = f"extracted_{ts}.txt"
        self.worker = ExtractWorker(self.stego_path, out, pw)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_extract_finished)
        self.worker.start()
    
    def _execute_bruteforce(self):
        if not self.wordlist_path or not os.path.exists(self.wordlist_path):
            QMessageBox.warning(self, "No Wordlist", "Configure a wordlist")
            self.execute_btn.setEnabled(True)
            return
        self.worker = StegseekWorker(self.stego_path, self.wordlist_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_bruteforce_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_extract_finished(self, ok, msg, of):
        self.execute_btn.setEnabled(True)
        if ok:
            self.status_output.append("SUCCESS!")
            self.status_progress.setValue(100)
            
            if msg == "BINARY" or (of and os.path.exists(of)):
                pm = QPixmap(of)
                if not pm.isNull():
                    self.result_preview.setPixmap(
                        pm.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    )
                    self.result_preview.show()
                    self.last_output_file = of
                    self.export_btn.show()
                    self.results_output.setText(f"File extracted: {os.path.basename(of)}")
                else:
                    self.results_output.setText(msg)
            else:
                self.results_output.setText(msg)
            
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR:\n{msg}")
            self.status_progress.setValue(100)
    
    def _on_bruteforce_finished(self, ok, msg, of, pw):
        self.execute_btn.setEnabled(True)
        if ok:
            if pw:
                self.status_output.append("Match found!")
                self.status_progress.setValue(100)
                self.results_output.setText(msg if msg else f"Password: {pw}")
                self.tabs.setCurrentIndex(2)
            elif msg == "No match found":
                self.status_output.append("No match found")
                self.results_output.setText("No match found in wordlist")
                self.tabs.setCurrentIndex(2)
            else:
                self.status_output.append("SUCCESS!")
                self.status_progress.setValue(100)
                self.results_output.setText(msg)
                self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR:\n{msg}")
            self.status_progress.setValue(100)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _export_result(self):
        if not self.last_output_file or not os.path.exists(self.last_output_file):
            QMessageBox.warning(self, "No File", "Nothing to export.")
            return
        fn = os.path.basename(self.last_output_file)
        fp, _ = QFileDialog.getSaveFileName(self, "Export Extracted File", fn, "All Files (*)")
        if fp:
            try:
                shutil.copy2(self.last_output_file, fp)
                QMessageBox.information(self, "Exported", f"Saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def set_wordlist_config(self, wp, sp):
        self.wordlist_path = wp
        self.split_parts = sp
        self._update_wordlist_badge()
        if hasattr(self, 'wordlist_status_label') and self.mode_slot.is_filled() and self.mode_slot.mode_id == 3:
            self.wordlist_status_label.setText(
                os.path.basename(wp) if (wp and os.path.exists(wp)) else "No wordlist configured"
            )
            hw = bool(wp and os.path.exists(wp))
            self.execute_btn.setEnabled(bool(self.stego_path) and self.sh_ok and self.ss_ok and hw)
    
    def refresh_theme(self):
        self._apply_theme()