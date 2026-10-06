# gui/zlib_compression_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
import zlib
import os
import sys
import base64


class CompressWorker(QThread):
    """Worker thread for zlib compression."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, bytes, dict)
    
    def __init__(self, text_data=None, file_path=None, level=6):
        super().__init__()
        self.text_data = text_data
        self.file_path = file_path
        self.level = level
    
    def run(self):
        try:
            self.progress.emit("Starting compression...")
            self.progress_value.emit(10)
            
            data = None
            
            if self.file_path:
                self.progress.emit(f"Reading file: {os.path.basename(self.file_path)}")
                with open(self.file_path, 'rb') as f:
                    data = f.read()
                self.progress_value.emit(30)
            elif self.text_data:
                self.progress.emit("Encoding text data...")
                data = self.text_data.encode('utf-8')
                self.progress_value.emit(30)
            
            if not data:
                self.finished.emit(False, b"No data to compress", {})
                return
            
            info = {}
            info['original_size'] = len(data)
            self.progress.emit(f"Original size: {len(data):,} bytes")
            
            self.progress.emit(f"Compressing with level {self.level}...")
            self.progress_value.emit(50)
            
            compressed = zlib.compress(data, self.level)
            info['compressed_size'] = len(compressed)
            self.progress_value.emit(80)
            
            if len(compressed) >= 2:
                cmf = compressed[0]
                flg = compressed[1]
                cm = cmf & 0x0f
                cinfo = (cmf >> 4) & 0x0f
                flevel = (flg >> 6) & 0x03
                
                info['compression_method'] = cm
                info['window_size'] = 2 ** (cinfo + 8)
                info['compression_level'] = flevel
                info['cmf'] = f"0x{cmf:02x}"
                info['flg'] = f"0x{flg:02x}"
            
            self.progress.emit("Compression successful!")
            self.progress_value.emit(100)
            self.finished.emit(True, compressed, info)
                    
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e).encode(), {})


class DraggableModeCard(QFrame):
    """Draggable card for operation modes (Text Input / File Input)."""
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self.setFixedSize(180, 70)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _build(self, name):
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self.name_label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        """Update the card's theme colors."""
        self.colors = theme_colors
        t = self.colors
        if self.name_label:
            self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 13px; font-weight: 600; background: transparent;")
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
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
    """Drop slot for operation mode."""
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self.setFixedSize(240, 90)
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}")
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}")
    
    def is_filled(self):
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
    
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
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, ZlibCompressionPage):
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
        if self.is_filled():
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 13, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.mode_name)
        else:
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Drag operation here")
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, ZlibCompressionPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()


class ZlibCompressionPage(QWidget):
    """Zlib Compression page with drag-and-drop operation selection."""
    
    OUTPUT_FORMATS = [
        ("utf8", "String (UTF-8)"),
        ("latin1", "String (Latin-1)"),
        ("hex_", "Hexadecimal (with spaces)"),
        ("hex", "Hexadecimal (no spaces)"),
        ("dec_", "Decimal (spaced)"),
        ("oct_", "Octal (spaced)"),
        ("bin_", "Binary 8-bit (spaced)"),
        ("bin8", "Binary 8-bit (no spaces)"),
        ("base64", "Base64"),
        ("file", "Save as File"),
    ]
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.text_data = ""
        self.file_path = ""
        self.worker = None
        self.mode_cards = []
        self.compressed_data = None
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                self.file_path = filepath
                self.file_path_input.setText(filepath)
                self._update_file_preview()
                self.execute_btn.setEnabled(self.mode_slot.is_filled())
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Zlib Compression")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_info_tab(), "Header Info")
        self.tabs.addTab(self._create_help_tab(), "Help")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Step 1: Operation Mode
        self.mode_group = QGroupBox("1. Operation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        t = self.theme.current
        for mode_id, name in [(1, "Text Input"), (2, "File Input")]:
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
        
        # Step 2: Options (dynamically changed)
        self.options_group = QGroupBox("2. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        # Compression level
        self.level_group = QGroupBox("3. Compression Level")
        level_layout = QVBoxLayout()
        level_layout.setSpacing(8)
        level_row = QHBoxLayout()
        level_label = QLabel("Level (1-9):")
        self.level_spin = QSpinBox()
        self.level_spin.setMinimum(1)
        self.level_spin.setMaximum(9)
        self.level_spin.setValue(6)
        self.level_spin.setToolTip("1 = Fastest, 9 = Best compression, 6 = Default")
        self.level_spin.setMinimumWidth(80)
        level_row.addWidget(level_label)
        level_row.addWidget(self.level_spin)
        level_row.addStretch()
        level_layout.addLayout(level_row)
        self.level_info = QLabel("Level 6: Default balance between speed and compression")
        level_layout.addWidget(self.level_info)
        self.level_group.setLayout(level_layout)
        layout.addWidget(self.level_group)
        
        # Output format selector
        self.format_group = QGroupBox("4. Output Format")
        format_layout = QVBoxLayout()
        format_layout.setSpacing(8)
        format_row = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.setMaxVisibleItems(6)
        self.format_combo.setMinimumWidth(180)
        for fmt_id, fmt_name in self.OUTPUT_FORMATS:
            self.format_combo.addItem(fmt_name, fmt_id)
        format_row.addWidget(format_label)
        format_row.addWidget(self.format_combo, 1)
        format_row.addStretch()
        format_layout.addLayout(format_row)
        self.format_group.setLayout(format_layout)
        layout.addWidget(self.format_group)
        
        # Execute button
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setMinimumHeight(48)
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
        
        results_header = QHBoxLayout()
        results_label = QLabel("Compressed Output:")
        
        self.format_label = QLabel("")
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        
        save_btn = QPushButton("Save to File")
        save_btn.setObjectName("actionButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_to_file)
        
        results_header.addWidget(results_label)
        results_header.addWidget(self.format_label)
        results_header.addStretch()
        results_header.addWidget(save_btn)
        results_header.addWidget(copy_btn)
        layout.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Compressed result will appear here...")
        self.results_output.setMinimumHeight(200)
        layout.addWidget(self.results_output)
        
        self.results_stats = QLabel("")
        layout.addWidget(self.results_stats)
        layout.addStretch()
        return widget
    
    def _create_info_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.info_group = QGroupBox("Zlib Header Information")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        self.info_output = QTextBrowser()
        self.info_output.setOpenExternalLinks(False)
        self.info_output.setPlaceholderText("Header information will appear here after compression...")
        info_layout.addWidget(self.info_output)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        return widget
    
    def _create_help_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.help_group = QGroupBox("Zlib Compression Help")
        help_layout = QVBoxLayout()
        help_layout.setSpacing(10)
        
        help_text = QTextBrowser()
        help_text.setOpenExternalLinks(False)
        help_text.setHtml("""
            <h3>What is Zlib Compression?</h3>
            <p>Zlib compression uses the Deflate algorithm (RFC 1951) wrapped in a 
            lightweight container (RFC 1950) with a 2-byte header and 4-byte Adler-32 checksum.</p>
            
            <h3>Compression Levels</h3>
            <table style="width:100%; margin: 8px 0;">
                <tr><td><b>1</b></td><td>Fastest speed, least compression</td></tr>
                <tr><td><b>6</b></td><td>Default balance (recommended)</td></tr>
                <tr><td><b>9</b></td><td>Best compression, slowest speed</td></tr>
            </table>
            
            <h3>How it Works</h3>
            <ul>
                <li><b>LZ77:</b> Identifies repeated byte sequences</li>
                <li><b>Huffman Coding:</b> Encodes frequent symbols with fewer bits</li>
                <li><b>Zlib Wrapper:</b> Adds CMF+FLG header and Adler-32 checksum</li>
            </ul>
            
            <h3>Usage Tips</h3>
            <ul>
                <li><b>Text Input:</b> Type or paste text to compress</li>
                <li><b>File Input:</b> Drop a file or use Browse to compress any file</li>
                <li>Drag an operation card to the drop slot to select mode</li>
                <li>Double-click the drop slot to clear and switch modes</li>
                <li>Use hex format for raw compressed data output</li>
            </ul>
        """)
        help_layout.addWidget(help_text)
        
        self.help_group.setLayout(help_layout)
        layout.addWidget(self.help_group)
        return widget
    
    def _on_mode_dropped(self):
        """Handle when a mode card is dropped into the slot."""
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
        
        if hasattr(self, 'text_input'):
            delattr(self, 'text_input')
        if hasattr(self, 'file_preview'):
            delattr(self, 'file_preview')
        if hasattr(self, 'file_path_input'):
            delattr(self, 'file_path_input')
        if hasattr(self, 'file_info'):
            delattr(self, 'file_info')
        
        if mode_id == 1:  # Text Input
            self.options_group.setVisible(True)
            self.options_group.setTitle("2. Text Data Input")
            
            self.text_input = QTextEdit()
            self.text_input.setPlaceholderText(
                "Enter text to compress here...\n"
                "Example: Hello World! This text will be compressed using Zlib."
            )
            self.text_input.setMinimumHeight(140)
            self.options_layout.addWidget(self.text_input)
            
            text_btn_row = QHBoxLayout()
            text_paste_btn = QPushButton("Paste from Clipboard")
            text_paste_btn.setObjectName("actionButton")
            text_paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            text_paste_btn.clicked.connect(self._paste_text)
            text_clear_btn = QPushButton("Clear")
            text_clear_btn.setObjectName("dangerButton")
            text_clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            text_clear_btn.clicked.connect(lambda: self.text_input.clear() if hasattr(self, 'text_input') else None)
            text_btn_row.addWidget(text_paste_btn)
            text_btn_row.addWidget(text_clear_btn)
            text_btn_row.addStretch()
            self.options_layout.addLayout(text_btn_row)
            
            self.execute_btn.setText("Compress Text")
            self.execute_btn.setEnabled(True)
            
        elif mode_id == 2:  # File Input
            self.options_group.setVisible(True)
            self.options_group.setTitle("2. File Input")
            
            self.file_preview = QLabel()
            self.file_preview.setFixedHeight(80)
            self.file_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_preview.setText("Drag & drop a file here\nor click Browse to select")
            self.options_layout.addWidget(self.file_preview)
            
            file_row = QHBoxLayout()
            self.file_path_input = QLineEdit()
            self.file_path_input.setReadOnly(True)
            self.file_path_input.setPlaceholderText("Select a file to compress...")
            file_btn = QPushButton("Browse")
            file_btn.setObjectName("actionButton")
            file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            file_btn.clicked.connect(self._browse_file)
            file_row.addWidget(self.file_path_input, 1)
            file_row.addWidget(file_btn)
            self.options_layout.addLayout(file_row)
            
            self.file_info = QLabel("")
            self.options_layout.addWidget(self.file_info)
            
            self.execute_btn.setText("Compress File")
            self.execute_btn.setEnabled(bool(self.file_path))
        
        self._apply_theme()
    
    def _on_mode_cleared(self):
        """Handle when the mode slot is cleared."""
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
        
        if hasattr(self, 'text_input'):
            delattr(self, 'text_input')
        if hasattr(self, 'file_preview'):
            delattr(self, 'file_preview')
        if hasattr(self, 'file_path_input'):
            delattr(self, 'file_path_input')
        if hasattr(self, 'file_info'):
            delattr(self, 'file_info')
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _paste_text(self):
        clipboard = QApplication.clipboard().text()
        if clipboard and hasattr(self, 'text_input'):
            self.text_input.setPlainText(clipboard)
    
    def _browse_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select File to Compress", "", "All Files (*.*)")
        if fp:
            self.file_path = fp
            if hasattr(self, 'file_path_input'):
                self.file_path_input.setText(fp)
            self._update_file_preview()
            self.execute_btn.setEnabled(True)
    
    def _update_file_preview(self):
        if not self.file_path or not os.path.exists(self.file_path):
            return
        
        fn = os.path.basename(self.file_path)
        sz = os.path.getsize(self.file_path)
        ss = f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
        
        if hasattr(self, 'file_preview'):
            self.file_preview.setText(f"File Selected\n{fn}")
        if hasattr(self, 'file_info'):
            self.file_info.setText(f"Size: {ss}")
    
    def _format_output(self, data):
        """Format compressed data according to selected format."""
        fmt = self.format_combo.currentData()
        
        if fmt == "utf8":
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data.decode('utf-8', errors='replace')
        elif fmt == "latin1":
            return data.decode('latin-1', errors='replace')
        elif fmt == "hex_":
            return ' '.join(f"{b:02x}" for b in data)
        elif fmt == "hex":
            return data.hex()
        elif fmt == "dec_":
            return ' '.join(str(b) for b in data)
        elif fmt == "oct_":
            return ' '.join(f"{b:03o}" for b in data)
        elif fmt == "bin_":
            return ' '.join(f"{b:08b}" for b in data)
        elif fmt == "bin8":
            return ''.join(f"{b:08b}" for b in data)
        elif fmt == "base64":
            return base64.b64encode(data).decode('ascii')
        elif fmt == "file":
            return data
        return data.hex()
    
    def _execute(self):
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.info_output.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        self.compressed_data = None
        
        level = self.level_spin.value()
        self.level_info.setText(f"Level {level}: " + {
            1: "Fastest speed, least compression",
            2: "Very fast, low compression",
            3: "Fast, moderate compression",
            4: "Medium speed, decent compression",
            5: "Balanced speed, good compression",
            6: "Default balance between speed and compression",
            7: "Slower, better compression",
            8: "Very slow, high compression",
            9: "Slowest, maximum compression"
        }.get(level, ""))
        
        if self.mode_slot.mode_id == 1:
            if not hasattr(self, 'text_input') or not self.text_input.toPlainText().strip():
                QMessageBox.warning(self, "No Input", "Please enter text to compress.")
                self.execute_btn.setEnabled(True)
                return
            text = self.text_input.toPlainText()
            self.worker = CompressWorker(text_data=text, level=level)
        elif self.mode_slot.mode_id == 2:
            if not self.file_path:
                QMessageBox.warning(self, "No File", "Please select a file.")
                self.execute_btn.setEnabled(True)
                return
            self.worker = CompressWorker(file_path=self.file_path, level=level)
        else:
            self.execute_btn.setEnabled(True)
            return
        
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, data, info):
        self.execute_btn.setEnabled(True)
        
        if success:
            self.status_output.append("\u2713 COMPRESSION SUCCESSFUL!")
            self.status_progress.setValue(100)
            
            self.compressed_data = data
            
            fmt = self.format_combo.currentData()
            if fmt == "file":
                self._save_to_file()
                self.results_output.setText(f"[Compressed file saved - {len(data):,} bytes]\n\nUse the 'Save to File' button to export again.")
            else:
                formatted = self._format_output(data)
                self.results_output.setText(formatted)
            
            fmt_name = self.format_combo.currentText()
            self.format_label.setText(f"({fmt_name})")
            
            stats_parts = []
            if 'original_size' in info:
                stats_parts.append(f"Original: {info['original_size']:,} bytes")
            if 'compressed_size' in info:
                stats_parts.append(f"Compressed: {info['compressed_size']:,} bytes")
                if info['original_size'] > 0:
                    ratio = info['compressed_size'] / info['original_size'] * 100
                    saved = (1 - info['compressed_size'] / info['original_size']) * 100
                    stats_parts.append(f"Ratio: {ratio:.1f}%")
                    stats_parts.append(f"Space saved: {saved:.1f}%")
            
            self.results_stats.setText(" | ".join(stats_parts))
            
            if info:
                t = self.theme.current
                html = "<table style='width:100%; border-spacing: 0;'>"
                rows = [
                    ("Header Bytes", f"{info.get('cmf', 'N/A')} {info.get('flg', 'N/A')}", "CMF + FLG"),
                    ("Compression Method", "Deflate (8)" if info.get('compression_method') == 8 else str(info.get('compression_method', 'N/A')), "8 = deflate"),
                    ("Window Size", f"{info.get('window_size', 0):,} bytes" if 'window_size' in info else "N/A", "32KB default"),
                ]
                
                if 'compression_level' in info:
                    levels = {0: "Level 1-2 (Fastest)", 1: "Level 3-4 (Fast)", 2: "Level 5-6 (Default)", 3: "Level 7-9 (Best)"}
                    rows.append(("Level Indicator", levels.get(info['compression_level'], str(info['compression_level'])), "From FLG bits"))
                
                rows.extend([
                    ("Output Format", self.format_combo.currentText(), ""),
                    ("Original Size", f"{info.get('original_size', 0):,} bytes", ""),
                    ("Compressed Size", f"{info.get('compressed_size', 0):,} bytes", ""),
                ])
                
                for label, value, desc in rows:
                    html += f"""
                        <tr>
                            <td style='padding: 6px 10px; font-weight: 600; white-space: nowrap;'>{label}</td>
                            <td style='padding: 6px 10px; color: {t['accent']}; font-weight: 600;'>{value}</td>
                            <td style='padding: 6px 10px; color: {t['text_tertiary']}; font-size: 11px;'>{desc}</td>
                        </tr>
                    """
                html += "</table>"
                self.info_output.setHtml(html)
            
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append("\u2717 COMPRESSION FAILED")
            error_msg = data.decode('utf-8', errors='replace') if isinstance(data, bytes) else str(data)
            self.status_output.append(f"Error: {error_msg}")
            self.status_progress.setValue(100)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied to clipboard!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy.")
    
    def _save_to_file(self):
        """Save compressed data to a file."""
        if self.compressed_data is None:
            QMessageBox.warning(self, "No Data", "No compressed data to save. Run compression first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed Data", "compressed_output.zlib",
            "All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(self.compressed_data)
                QMessageBox.information(self, "Saved", f"File saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")
    
    def _apply_theme(self):
        t = self.theme.current
        
        # Tab widget
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                background-color: {t['base']};
            }}
            QTabBar::tab {{
                background-color: {t['crust']};
                color: {t['text_secondary']};
                border: 1px solid {t['border']};
                padding: 10px 28px;
                margin-right: 2px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {t['base']};
                color: {t['text']};
                border-bottom-color: transparent;
            }}
        """)
        
        # Group boxes
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['mode_group', 'options_group', 'level_group', 'format_group', 'info_group', 'help_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        # Apply button styling
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['text']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: 14px;
                            font-weight: 700;
                            font-size: 15px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                    """)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['error']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: 14px;
                            font-weight: 700;
                            font-size: 15px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                    """)
            except RuntimeError:
                pass
        
        # Combo box
        if hasattr(self, 'format_combo') and self.format_combo is not None:
            try:
                self.format_combo.setStyleSheet(f"""
                    QComboBox {{
                        background-color: {t['crust']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 8px 28px 8px 14px;
                        font-size: 13px;
                        font-weight: 500;
                    }}
                    QComboBox:hover {{
                        border-color: {t['border_focus']};
                    }}
                    QComboBox::drop-down {{
                        border: none;
                        width: 24px;
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                    }}
                    QComboBox::down-arrow {{
                        width: 12px;
                        height: 12px;
                    }}
                    QComboBox QAbstractItemView {{
                        background-color: {t['base']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 8px;
                        selection-background-color: {t['hover']};
                        selection-color: {t['text']};
                        outline: none;
                    }}
                    QComboBox QAbstractItemView::item {{
                        color: {t['text']};
                        background-color: transparent;
                        padding: 8px 16px;
                        border-radius: 4px;
                        min-height: 24px;
                    }}
                    QComboBox QAbstractItemView::item:hover {{
                        background-color: {t['hover']};
                        color: {t['text']};
                    }}
                    QComboBox QAbstractItemView::item:selected {{
                        background-color: {t['hover']};
                        color: {t['text']};
                    }}
                """)
            except RuntimeError:
                pass
        
        # Spin box
        if hasattr(self, 'level_spin') and self.level_spin is not None:
            try:
                self.level_spin.setStyleSheet(f"""
                    QSpinBox {{
                        background-color: {t['crust']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    QSpinBox:focus {{
                        border-color: {t['border_focus']};
                    }}
                    QSpinBox::up-button, QSpinBox::down-button {{
                        background-color: {t['surface0']};
                        border: none;
                        border-radius: 3px;
                        width: 20px;
                    }}
                    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                        background-color: {t['hover']};
                    }}
                """)
            except RuntimeError:
                pass
        
        # Text edits - only if they exist
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        if hasattr(self, 'text_input') and self.text_input is not None:
            try:
                self.text_input.setStyleSheet(ts)
            except RuntimeError:
                pass
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(ts)
            except RuntimeError:
                pass
        
        # Results output
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;}}")
            except RuntimeError:
                pass
        
        # Info/Help browsers
        browser_style = f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:12px;font-size:12px;}}"
        if hasattr(self, 'info_output') and self.info_output is not None:
            try:
                self.info_output.setStyleSheet(browser_style)
            except RuntimeError:
                pass
        
        # Input fields
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        if hasattr(self, 'file_path_input') and self.file_path_input is not None:
            try:
                self.file_path_input.setStyleSheet(input_style)
            except RuntimeError:
                pass
        
        # Progress bar
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}")
            except RuntimeError:
                pass
        
        # File preview
        if hasattr(self, 'file_preview') and self.file_preview is not None:
            try:
                self.file_preview.setStyleSheet(f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;")
            except RuntimeError:
                pass
        
        # Info labels
        info_label_style = f"color:{t['text_tertiary']};font-size:11px;background:transparent;"
        for attr in ['file_info', 'format_label', 'level_info', 'results_stats']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    if attr == 'results_stats':
                        getattr(self, attr).setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
                    elif attr == 'level_info':
                        getattr(self, attr).setStyleSheet(f"color:{t['text_tertiary']};font-size:11px;font-style:italic;background:transparent;")
                    else:
                        getattr(self, attr).setStyleSheet(info_label_style)
                except RuntimeError:
                    pass
        
        # Mode slot
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            try:
                self.mode_slot.colors = t
                if self.mode_slot.is_filled():
                    self.mode_slot._style_filled()
                else:
                    self.mode_slot._style_empty()
                self.mode_slot.update()
            except RuntimeError:
                pass
        
        # Mode cards
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()