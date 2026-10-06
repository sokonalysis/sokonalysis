# gui/adfgvx_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
import os
import sys
import random
import string


class ADFGVXDecryptWorker(QThread):
    """Worker thread for ADFGVX decryption - Wikipedia/WWI accurate."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, dict)
    
    def __init__(self, ciphertext, keyword="", use_transposition=True, grid_data=None, use_v=False):
        super().__init__()
        self.ciphertext = ciphertext
        self.keyword = keyword
        self.use_transposition = use_transposition
        self.grid_data = grid_data
        self.use_v = use_v
    
    def _reverse_transposition(self, ciphertext, keyword):
        """Reverse columnar transposition - Wikipedia/WWI accurate."""
        keyword = keyword.upper()
        key_length = len(keyword)
        
        pairs = [ciphertext[i:i+2] for i in range(0, len(ciphertext), 2)]
        total_pairs = len(pairs)
        
        num_rows = (total_pairs + key_length - 1) // key_length
        short_cols = (key_length - (total_pairs % key_length)) % key_length
        
        columns = list(range(key_length))
        columns.sort(key=lambda i: (keyword[i], i))
        
        col_heights = {}
        for col in range(key_length):
            if short_cols > 0 and col >= key_length - short_cols:
                col_heights[col] = num_rows - 1
            else:
                col_heights[col] = num_rows
        
        col_data = {}
        pos = 0
        for col_idx in columns:
            height = col_heights[col_idx]
            col_data[col_idx] = pairs[pos:pos + height]
            pos += height
        
        result = []
        for row in range(num_rows):
            for col in range(key_length):
                if row < len(col_data[col]):
                    result.append(col_data[col][row])
        
        return ''.join(result)
    
    def run(self):
        try:
            self.progress.emit("Analyzing ciphertext...")
            self.progress_value.emit(10)
            
            ciphertext = self.ciphertext.upper().replace(' ', '').replace('\n', '')
            rows = ['A', 'D', 'F', 'G', 'V', 'X'] if self.use_v else ['A', 'D', 'F', 'G', 'X']
            grid_name = "ADFGVX (6x6)" if self.use_v else "ADFGX (5x5)"
            
            self.progress.emit(f"Using: {grid_name}")
            self.progress_value.emit(30)
            
            # Build grid lookup
            grid = {}
            for r in range(len(rows)):
                grid[rows[r]] = {}
                for c in range(len(rows)):
                    if r < len(self.grid_data) and c < len(self.grid_data[r]):
                        grid[rows[r]][rows[c]] = self.grid_data[r][c]
            
            self.progress_value.emit(50)
            
            if self.use_transposition and self.keyword:
                self.progress.emit(f"Reversing transposition with keyword: {self.keyword.upper()}")
                pair_string = self._reverse_transposition(ciphertext, self.keyword)
            else:
                pair_string = ciphertext
            
            self.progress.emit(f"Bigram string: {pair_string}")
            self.progress.emit("Decoding Polybius pairs...")
            
            plaintext = []
            for i in range(0, len(pair_string), 2):
                if i + 1 < len(pair_string):
                    row_key = pair_string[i]
                    col_key = pair_string[i+1]
                    if row_key in grid and col_key in grid[row_key]:
                        plaintext.append(grid[row_key][col_key])
                    else:
                        plaintext.append('?')
            
            plaintext_str = ''.join(plaintext)
            # Remove padding (trailing X's that look like padding)
            
            self.progress_value.emit(90)
            
            info = {
                'grid_type': grid_name,
                'keyword': self.keyword if self.use_transposition else 'None',
                'mode': 'With transposition' if self.use_transposition else 'Polybius only',
                'cipher_length': len(ciphertext)
            }
            
            self.progress.emit("Decryption complete!")
            self.progress_value.emit(100)
            self.finished.emit(True, plaintext_str, info)
            
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), {})


class DraggableModeCard(QFrame):
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
            while p and not isinstance(p, ADFGVXDecryptPage):
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
            while p and not isinstance(p, ADFGVXDecryptPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()


class ADFGVXDecryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.mode_cards = []
        self.current_use_v = False
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
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
        
        title = QLabel("ADFGVX Decrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
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
        for mode_id, name in [(1, "Simple Decrypt"), (2, "Full Decrypt")]:
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
        
        # Step 2: Grid Type
        self.grid_type_group = QGroupBox("2. Grid Type")
        grid_type_layout = QVBoxLayout()
        grid_type_layout.setSpacing(8)
        grid_row = QHBoxLayout()
        grid_label = QLabel("Select grid:")
        self.grid_combo = QComboBox()
        self.grid_combo.addItem("ADFGX (5x5) - Letters A-Z, I=J", "adfgx")
        self.grid_combo.addItem("ADFGVX (6x6) - Letters + Digits 0-9", "adfgvx")
        self.grid_combo.addItem("Auto-Detect", "auto")
        self.grid_combo.setMinimumWidth(250)
        self.grid_combo.currentIndexChanged.connect(self._on_grid_type_changed)
        grid_row.addWidget(grid_label)
        grid_row.addWidget(self.grid_combo, 1)
        grid_row.addStretch()
        grid_type_layout.addLayout(grid_row)
        self.grid_type_group.setLayout(grid_type_layout)
        layout.addWidget(self.grid_type_group)
        
        # Step 3: Polybius Square
        self.polybius_group = QGroupBox("3. Polybius Square")
        polybius_layout = QVBoxLayout()
        polybius_layout.setSpacing(8)
        
        kw_row = QHBoxLayout()
        kw_label = QLabel("Grid Keyword:")
        self.grid_keyword_input = QLineEdit()
        self.grid_keyword_input.setPlaceholderText("Keyword used to create the grid (leave empty for standard A-Z)...")
        self.grid_keyword_input.textChanged.connect(self._update_grid_display)
        
        self.auto_generate_btn = QPushButton("Auto-Generate")
        self.auto_generate_btn.setObjectName("actionButton")
        self.auto_generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_generate_btn.clicked.connect(self._auto_generate_keyword)
        self.auto_generate_btn.setMaximumWidth(140)
        
        self.shuffle_btn = QPushButton("Shuffle Grid")
        self.shuffle_btn.setObjectName("actionButton")
        self.shuffle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.shuffle_btn.clicked.connect(self._shuffle_grid)
        self.shuffle_btn.setMaximumWidth(120)
        
        self.reset_grid_btn = QPushButton("Reset")
        self.reset_grid_btn.setObjectName("dangerButton")
        self.reset_grid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_grid_btn.clicked.connect(self._reset_grid)
        self.reset_grid_btn.setMaximumWidth(80)
        
        kw_row.addWidget(kw_label)
        kw_row.addWidget(self.grid_keyword_input, 1)
        kw_row.addWidget(self.auto_generate_btn)
        kw_row.addWidget(self.shuffle_btn)
        kw_row.addWidget(self.reset_grid_btn)
        polybius_layout.addLayout(kw_row)
        
        self.grid_table = QTableWidget()
        self.grid_table.setMinimumHeight(200)
        self.grid_table.setMaximumHeight(300)
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        polybius_layout.addWidget(self.grid_table)
        
        self.polybius_group.setLayout(polybius_layout)
        layout.addWidget(self.polybius_group)
        
        # Step 4: Options
        self.options_group = QGroupBox("4. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
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
        
        self._update_grid_display()
        return widget
    
    def _auto_generate_keyword(self):
        length = random.randint(6, 12)
        keyword = ''.join(random.choices(string.ascii_uppercase, k=length))
        self.grid_keyword_input.setText(keyword)
    
    def _shuffle_grid(self):
        rows = self.grid_table.rowCount()
        cols = self.grid_table.columnCount()
        chars = []
        for r in range(rows):
            for c in range(cols):
                item = self.grid_table.item(r, c)
                if item:
                    chars.append(item.text())
        random.shuffle(chars)
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx < len(chars):
                    item = QTableWidgetItem(chars[idx])
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    font = QFont("JetBrains Mono, Consolas, monospace", 13)
                    font.setBold(True)
                    item.setFont(font)
                    self.grid_table.setItem(r, c, item)
                    idx += 1
        self.grid_keyword_input.clear()
        self._style_grid()
    
    def _reset_grid(self):
        self.grid_keyword_input.clear()
        self._update_grid_display()
    
    def _on_grid_type_changed(self):
        self._update_grid_display()
    
    def _update_grid_display(self):
        grid_type = self.grid_combo.currentData()
        if grid_type == "adfgvx":
            use_v = True
        else:
            use_v = False
        
        self.current_use_v = use_v
        
        if use_v:
            rows = ['A', 'D', 'F', 'G', 'V', 'X']
            size = 6
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        else:
            rows = ['A', 'D', 'F', 'G', 'X']
            size = 5
            alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
        
        grid_keyword = self.grid_keyword_input.text().strip() if hasattr(self, 'grid_keyword_input') else ""
        
        if grid_keyword:
            seen = set()
            chars = []
            for c in grid_keyword.upper():
                if use_v:
                    if c == 'J':
                        continue
                else:
                    if c == 'J':
                        c = 'I'
                if c not in seen and c in alphabet:
                    seen.add(c)
                    chars.append(c)
            for c in alphabet:
                if c not in seen:
                    chars.append(c)
        else:
            chars = list(alphabet)
        
        self.grid_table.setRowCount(size)
        self.grid_table.setColumnCount(size)
        self.grid_table.setHorizontalHeaderLabels(rows)
        self.grid_table.setVerticalHeaderLabels(rows)
        
        idx = 0
        for r in range(size):
            for c in range(size):
                if idx < len(chars):
                    item = QTableWidgetItem(chars[idx])
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    font = QFont("JetBrains Mono, Consolas, monospace", 13)
                    font.setBold(True)
                    item.setFont(font)
                    self.grid_table.setItem(r, c, item)
                    idx += 1
        
        self._style_grid()
    
    def _style_grid(self):
        t = self.theme.current
        self.grid_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                gridline-color: {t['border']};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {t['accent']}44;
                color: {t['text']};
            }}
            QHeaderView::section {{
                background-color: {t['surface0']};
                color: {t['text']};
                border: 1px solid {t['border']};
                padding: 6px;
                font-weight: 700;
                font-size: 14px;
            }}
        """)
    
    def _get_grid_data(self):
        rows = self.grid_table.rowCount()
        cols = self.grid_table.columnCount()
        data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = self.grid_table.item(r, c)
                row.append(item.text() if item else '?')
            data.append(row)
        return data
    
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
        
        if hasattr(self, 'ciphertext_input'):
            delattr(self, 'ciphertext_input')
        if hasattr(self, 'keyword_input'):
            delattr(self, 'keyword_input')
        
        cipher_label = QLabel("Ciphertext:")
        self.ciphertext_input = QTextEdit()
        self.ciphertext_input.setPlaceholderText("Enter ADFGVX/ADFGX ciphertext...\nExample: AD FG VX AD FG VX ...")
        self.ciphertext_input.setMinimumHeight(100)
        self.options_layout.addWidget(cipher_label)
        self.options_layout.addWidget(self.ciphertext_input)
        
        cipher_btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_ciphertext)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.ciphertext_input.clear() if hasattr(self, 'ciphertext_input') else None)
        cipher_btn_row.addWidget(paste_btn)
        cipher_btn_row.addWidget(clear_btn)
        cipher_btn_row.addStretch()
        self.options_layout.addLayout(cipher_btn_row)
        
        if mode_id == 2:
            kw_label = QLabel("Transposition Keyword:")
            self.keyword_input = QLineEdit()
            self.keyword_input.setPlaceholderText("Enter the transposition keyword (e.g., GERMAN)...")
            self.options_layout.addWidget(kw_label)
            self.options_layout.addWidget(self.keyword_input)
            self.execute_btn.setText("Full Decrypt")
        else:
            self.execute_btn.setText("Simple Decrypt")
        
        self.options_group.setVisible(True)
        self.execute_btn.setEnabled(True)
        self._apply_theme()
    
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
        
        if hasattr(self, 'ciphertext_input'):
            delattr(self, 'ciphertext_input')
        if hasattr(self, 'keyword_input'):
            delattr(self, 'keyword_input')
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _paste_ciphertext(self):
        clipboard = QApplication.clipboard().text()
        if clipboard and hasattr(self, 'ciphertext_input'):
            self.ciphertext_input.setPlainText(clipboard)
    
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
        results_label = QLabel("Decrypted Text:")
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        layout.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Decrypted text will appear here...")
        self.results_output.setMinimumHeight(200)
        layout.addWidget(self.results_output)
        
        self.results_info = QLabel("")
        layout.addWidget(self.results_info)
        layout.addStretch()
        return widget
    
    def _create_help_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.help_group = QGroupBox("ADFGVX Cipher Help")
        help_layout = QVBoxLayout()
        help_layout.setSpacing(10)
        
        help_text = QTextBrowser()
        help_text.setOpenExternalLinks(False)
        help_text.setHtml("""
            <h3>ADFGVX Cipher - WWI German Field Cipher</h3>
            <p>Used by the Imperial German Army during World War I.</p>
            
            <h3>Grid Controls</h3>
            <ul>
                <li><b>Grid Keyword:</b> Enter the keyword used to create the grid</li>
                <li><b>Auto-Generate:</b> Creates a random keyword</li>
                <li><b>Shuffle Grid:</b> Randomly shuffles all grid cells</li>
                <li><b>Reset:</b> Returns to standard A-Z order</li>
                <li><b>Double-click</b> any cell to edit it manually</li>
            </ul>
            
            <h3>Decryption</h3>
            <ol>
                <li>Reverse columnar transposition using keyword</li>
                <li>Split resulting string into bigram pairs</li>
                <li>Look up each pair in the Polybius square</li>
            </ol>
        """)
        help_layout.addWidget(help_text)
        
        self.help_group.setLayout(help_layout)
        layout.addWidget(self.help_group)
        return widget
    
    def _execute(self):
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        
        if not hasattr(self, 'ciphertext_input') or not self.ciphertext_input.toPlainText().strip():
            QMessageBox.warning(self, "No Input", "Please enter ciphertext.")
            return
        
        ciphertext = self.ciphertext_input.toPlainText().strip()
        mode_id = self.mode_slot.mode_id
        use_transposition = (mode_id == 2)
        grid_data = self._get_grid_data()
        
        keyword = ""
        if use_transposition:
            if hasattr(self, 'keyword_input'):
                keyword = self.keyword_input.text().strip()
            if not keyword:
                QMessageBox.warning(self, "No Keyword", "Please enter the transposition keyword for Full Decrypt.")
                return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        
        self.worker = ADFGVXDecryptWorker(ciphertext, keyword, use_transposition, grid_data, self.current_use_v)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
    
    def _on_finished(self, success, message, info):
        self.execute_btn.setEnabled(True)
        if success:
            self.status_output.append("\u2713 SUCCESS!")
            self.status_progress.setValue(100)
            self.results_output.setText(message)
            if info:
                parts = [f"Grid: {info.get('grid_type', 'N/A')}"]
                if info.get('keyword') and info['keyword'] != 'None':
                    parts.append(f"Keyword: {info['keyword']}")
                parts.append(f"Mode: {info.get('mode', 'N/A')}")
                self.results_info.setText(" | ".join(parts))
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"\u2717 Error: {message}")
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['mode_group', 'grid_type_group', 'polybius_group', 'options_group', 'help_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
            except RuntimeError:
                pass
        
        if hasattr(self, 'grid_combo') and self.grid_combo is not None:
            try:
                self.grid_combo.setStyleSheet(f"""
                    QComboBox {{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:8px;padding:8px 28px 8px 14px;font-size:13px;font-weight:500;}}
                    QComboBox:hover {{border-color:{t['border_focus']};}}
                    QComboBox::drop-down {{border:none;width:24px;}}
                    QComboBox QAbstractItemView {{background-color:{t['base']};color:{t['text']};border:1px solid {t['border']};border-radius:8px;padding:8px;selection-background-color:{t['hover']};selection-color:{t['text']};outline:none;}}
                    QComboBox QAbstractItemView::item {{color:{t['text']};background-color:transparent;padding:8px 16px;border-radius:4px;}}
                    QComboBox QAbstractItemView::item:hover {{background-color:{t['hover']};color:{t['text']};}}
                """)
            except RuntimeError:
                pass
        
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        for attr in ['ciphertext_input', 'status_output']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(ts)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;}}")
            except RuntimeError:
                pass
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['keyword_input', 'grid_keyword_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}")
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
            except RuntimeError:
                pass
        
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
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        if hasattr(self, 'grid_table') and self.grid_table is not None:
            self._style_grid()
    
    def refresh_theme(self):
        self._apply_theme()