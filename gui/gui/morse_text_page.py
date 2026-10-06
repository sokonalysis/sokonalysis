# gui/morse_text_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QScrollArea, QGridLayout,
    QToolButton, QMenu, QApplication, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
import os, sys
from gui.layout_manager import layout_manager


TEXT_TO_MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', '!': '-.-.--',
    '/': '-..-.', '@': '.--.-.', '&': '.-...', ':': '---...',
    ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '-': '-....-',
    '_': '..--.-', '"': '.-..-.', '$': '...-..-',
    '(': '-.--.', ')': '-.--.-', "'": '.----.',
    ' ': '/'
}

MORSE_TO_TEXT = {v: k for k, v in TEXT_TO_MORSE.items() if v != '/'}

PUNCT_TO_FILENAME = {
    '.': 'DOT', ',': 'COMMA', '?': 'QMARK', '!': 'EXCL',
    '/': 'SLASH', '@': 'AT', '&': 'AMP', ':': 'COLON',
    ';': 'SEMI', '=': 'EQ', '+': 'PLUS', '-': 'MINUS',
    '_': 'UNDER', '"': 'DQUOTE', '$': 'DOLLAR',
    '(': 'LPAREN', ')': 'RPAREN', "'": 'APOS'
}


class MorseTextPage(QWidget):
    """Morse Code Text Translator with visual symbol display."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.symbols_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'symbols', 'morse'
        )
        self._last_plaintext = ""
        self._last_morse = ""
        self._last_displayed_source = ""
        self._current_ref_category = 'LETTERS'
        self._init_ui()
    
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
        
        title = QLabel("Morse Code Translator")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._create_reference_tab(), "Reference")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}} "
            f"QTabBar::tab{{background:{t['crust']};color:{t['text_secondary']};"
            f"border:1px solid {t['border']};padding:{int(10 * scale)}px {int(20 * scale)}px;"
            f"margin-right:2px;border-radius:7px 7px 0 0;"
            f"font-size:{max(11, int(12 * scale))}px;font-weight:600;}} "
            f"QTabBar::tab:selected{{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}"
        )
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:{int(20 * scale)}px {int(16 * scale)}px {int(16 * scale)}px;"
            f"font-weight:600;font-size:{max(12, int(13 * scale))}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['in_grp', 'res_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        text_edit_style = (
            f"QTextEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,Consolas,monospace;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        if hasattr(self, 'input_text') and self.input_text is not None:
            self.input_text.setStyleSheet(text_edit_style)
        if hasattr(self, 'text_output') and self.text_output is not None:
            self.text_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,Consolas,monospace;"
                f"font-size:{max(12, int(14 * scale))}px;font-weight:700;}}"
            )
        
        if hasattr(self, 'results_container') and self.results_container is not None:
            self.results_container.setStyleSheet(
                f"background-color:{t['crust']};border:1px solid {t['border']};border-radius:6px;"
            )
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(18 * scale)}px;"
                        f"font-weight:700;font-size:{max(12, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(18 * scale)}px;"
                        f"font-weight:700;font-size:{max(12, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        if hasattr(self, 'ref_filter_btn') and self.ref_filter_btn is not None:
            self.ref_filter_btn.setStyleSheet(
                f"QToolButton{{color:{t['text_secondary']};padding:4px 12px;border-radius:4px;"
                f"font-size:{max(11, int(12 * scale))}px;font-weight:500;background:transparent;border:none;}} "
                f"QToolButton:hover{{color:{t['text']};}}"
            )
        if hasattr(self, 'ref_menu') and self.ref_menu is not None:
            self.ref_menu.setStyleSheet(
                f"QMenu{{background-color:{t['base']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:8px;padding:{int(8 * scale)}px;}} "
                f"QMenu::item{{padding:{int(8 * scale)}px {int(36 * scale)}px {int(8 * scale)}px {int(16 * scale)}px;"
                f"border-radius:4px;font-size:{max(11, int(12 * scale))}px;}} "
                f"QMenu::item:selected{{background-color:{t['hover']};color:{t['text']};}}"
            )
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            self.results_info.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{max(10, int(11 * scale))}px;background:transparent;"
            )
        
        if hasattr(self, 'ref_grid_layout'):
            self._apply_ref_labels_theme(t)
    
    def _icon(self, name):
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        path = os.path.join(icons_dir, name)
        return QIcon(path) if os.path.exists(path) else QIcon()
    
    def _get_symbol_filename(self, char):
        if char in PUNCT_TO_FILENAME:
            return PUNCT_TO_FILENAME[char]
        return char
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        scale = layout_manager.font_scale()
        
        self.in_grp = QGroupBox("Input")
        il = QVBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Enter text to encode or Morse code to decode...\n"
            "Use . (dot) and - (dash) for Morse, spaces between letters, / between words"
        )
        self.input_text.setMaximumHeight(max(96, int(120 * scale)))
        self.input_text.setMinimumHeight(max(80, int(100 * scale)))
        il.addWidget(self.input_text)
        
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.input_text))
        btn_row.addWidget(paste_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        il.addLayout(btn_row)
        
        self.in_grp.setLayout(il)
        
        br = QHBoxLayout()
        br.addStretch()
        encode_btn = QPushButton("Encode")
        encode_btn.setObjectName("actionButton")
        encode_btn.setMinimumHeight(max(36, int(42 * scale)))
        encode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        encode_btn.clicked.connect(self._encode)
        br.addWidget(encode_btn)
        
        decode_btn = QPushButton("Decode")
        decode_btn.setObjectName("actionButton")
        decode_btn.setMinimumHeight(max(36, int(42 * scale)))
        decode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decode_btn.clicked.connect(self._decode)
        br.addWidget(decode_btn)
        
        l.addWidget(self.in_grp)
        l.addLayout(br)
        l.addStretch()
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        scale = layout_manager.font_scale()
        
        self.res_grp = QGroupBox("Output")
        rl = QVBoxLayout()
        
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("border:none;background:transparent;")
        self.results_scroll.setMinimumHeight(max(160, int(200 * scale)))
        self.results_container = QWidget()
        self.results_flow = QHBoxLayout(self.results_container)
        self.results_flow.setSpacing(6)
        self.results_flow.setContentsMargins(12, 12, 12, 12)
        self.results_flow.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.results_scroll.setWidget(self.results_container)
        rl.addWidget(self.results_scroll, 1)
        
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setMaximumHeight(max(64, int(80 * scale)))
        self.text_output.setPlaceholderText("Text representation will appear here...")
        rl.addWidget(self.text_output)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        btn_row.addWidget(copy_btn)
        
        export_btn = QPushButton("Export as PNG")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_as_png)
        btn_row.addWidget(export_btn)
        rl.addLayout(btn_row)
        
        self.results_info = QLabel("")
        rl.addWidget(self.results_info)
        
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp)
        l.addStretch()
        return w
    
    def _create_reference_tab(self):
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)
        scale = layout_manager.font_scale()
        
        fltr_row = QHBoxLayout()
        self.ref_filter_btn = QToolButton()
        self.ref_filter_btn.setIcon(self._icon("filter.png"))
        self.ref_filter_btn.setIconSize(QSize(max(24, int(32 * scale)), max(24, int(32 * scale))))
        self.ref_filter_btn.setText("Filter")
        self.ref_filter_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.ref_filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.ref_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ref_menu = QMenu(self.ref_filter_btn)
        cats = [
            ("Letters A-Z", 'LETTERS'),
            ("Numbers 0-9", 'NUMBERS'),
            ("Punctuation", 'PUNCT')
        ]
        for cn, ci in cats:
            a = self.ref_menu.addAction(cn)
            a.triggered.connect(lambda checked, c=ci: self._filter_reference(c))
        self.ref_filter_btn.setMenu(self.ref_menu)
        fltr_row.addWidget(self.ref_filter_btn)
        fltr_row.addStretch()
        outer.addLayout(fltr_row)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ref_grid_widget = QWidget()
        self.ref_grid_layout = QGridLayout(self.ref_grid_widget)
        self.ref_grid_layout.setSpacing(4)
        self.ref_grid_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self.ref_grid_widget)
        outer.addWidget(scroll, 1)
        
        self.ref_symbols = {
            'LETTERS': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            'NUMBERS': list('0123456789'),
            'PUNCT': ['DOT', 'COMMA', 'QMARK', 'EXCL', 'SLASH', 'AT', 'AMP', 'COLON', 'SEMI', 'EQ', 'PLUS', 'MINUS', 'UNDER', 'DQUOTE', 'DOLLAR', 'LPAREN', 'RPAREN', 'APOS'],
        }
        self._filter_reference('LETTERS')
        return widget
    
    def _filter_reference(self, cat):
        self._current_ref_category = cat
        self.ref_filter_btn.setText("Filter")
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        while self.ref_grid_layout.count():
            item = self.ref_grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        symbols = self.ref_symbols.get(cat, [])
        if not symbols:
            return
        
        COLS = 10
        cell_w = max(80, int(100 * scale))
        cell_h = max(44, int(55 * scale))
        pix_w = max(72, int(90 * scale))
        pix_h = max(40, int(50 * scale))
        label_size = max(10, int(12 * scale))
        mono_size = max(9, int(10 * scale))
        
        for i, symbol in enumerate(symbols):
            row = (i // COLS) * 2
            col = i % COLS
            
            letter_lbl = QLabel(symbol)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_lbl.setStyleSheet(
                f"font-weight:700; font-size:{label_size}px; color:{t['text']}; background:transparent;"
            )
            
            img_path = os.path.join(self.symbols_dir, f"{symbol}.png")
            symbol_lbl = QLabel()
            symbol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                symbol_lbl.setPixmap(
                    pixmap.scaled(
                        pix_w, pix_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
            else:
                symbol_lbl.setText(TEXT_TO_MORSE.get(symbol, '?'))
                symbol_lbl.setStyleSheet(
                    f"font-family:JetBrains Mono,monospace; font-size:{mono_size}px; color:{t['text']};"
                )
            symbol_lbl.setFixedSize(cell_w, cell_h)
            
            self.ref_grid_layout.addWidget(letter_lbl, row, col)
            self.ref_grid_layout.addWidget(symbol_lbl, row + 1, col)
        
        final_row = ((len(symbols) - 1) // COLS + 1) * 2
        self.ref_grid_layout.setRowStretch(final_row, 1)
        self._apply_ref_labels_theme(t)
    
    def _apply_ref_labels_theme(self, t):
        scale = layout_manager.font_scale()
        for i in range(self.ref_grid_layout.count()):
            item = self.ref_grid_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                lbl = item.widget()
                if lbl.pixmap() is None:
                    lbl.setStyleSheet(
                        f"font-weight:700; font-size:{max(10, int(12 * scale))}px; "
                        f"color:{t['text']}; background:transparent;"
                    )
    
    def _display_results_symbols(self, text):
        """Display text characters as actual QLabel PNG widgets (like Reference tab)."""
        self._last_displayed_source = text
        
        while self.results_flow.count():
            item = self.results_flow.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        if not text:
            return
        
        scale = layout_manager.font_scale()
        pix_w = max(64, int(80 * scale))
        pix_h = max(40, int(50 * scale))
        lbl_w = max(68, int(85 * scale))
        lbl_h = max(44, int(55 * scale))
        word_gap = max(14, int(20 * scale))
        line_gap = max(8, int(10 * scale))
        fallback_size = max(12, int(16 * scale))
        
        for char in text.upper():
            if char == ' ' or char == '/':
                spacer = QLabel()
                spacer.setFixedWidth(word_gap)
                self.results_flow.addWidget(spacer)
            elif char == '\n':
                spacer = QLabel()
                spacer.setFixedWidth(line_gap)
                self.results_flow.addWidget(spacer)
            else:
                filename = self._get_symbol_filename(char)
                img_path = os.path.join(self.symbols_dir, f"{filename}.png")
                
                symbol_lbl = QLabel()
                symbol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                symbol_lbl.setToolTip(char)
                
                if os.path.exists(img_path):
                    pixmap = QPixmap(img_path)
                    symbol_lbl.setPixmap(
                        pixmap.scaled(
                            pix_w, pix_h,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )
                    symbol_lbl.setFixedSize(lbl_w, lbl_h)
                else:
                    symbol_lbl.setText(f"[{char}]")
                    symbol_lbl.setStyleSheet(
                        f"font-size:{fallback_size}px; font-weight:700; "
                        f"color:{self.theme.current['text']};"
                    )
                    symbol_lbl.setFixedSize(max(40, int(50 * scale)), lbl_h)
                
                self.results_flow.addWidget(symbol_lbl)
        
        self.results_flow.addStretch()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setPlainText(clipboard)
    
    def _copy_result(self):
        text = self.text_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Text copied to clipboard!")
    
    def _clear_all(self):
        self.input_text.clear()
        self.text_output.clear()
        self.results_info.setText("")
        self._last_plaintext = ""
        self._last_morse = ""
        self._last_displayed_source = ""
        self._display_results_symbols("")
    
    def _export_as_png(self):
        if not self._last_displayed_source:
            QMessageBox.warning(self, "Nothing to Export", "Run encoding or decoding first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Morse Symbols", "morse_output.png",
            "PNG Images (*.png)"
        )
        if not file_path:
            return
        
        scale = layout_manager.font_scale()
        char_width = max(72, int(90 * scale))
        spacing = max(3, int(4 * scale))
        word_gap = max(20, int(25 * scale))
        line_height = max(48, int(60 * scale))
        max_width = max(640, int(800 * scale))
        padding = max(8, int(10 * scale))
        pix_w = max(64, int(80 * scale))
        pix_h = max(40, int(50 * scale))
        
        lines = []
        current_line = []
        current_width = 0
        
        for char in self._last_displayed_source.upper():
            if char == ' ':
                current_width += word_gap
                if current_width > max_width:
                    lines.append(current_line)
                    current_line = []
                    current_width = word_gap
                current_line.append(None)
            else:
                filename = self._get_symbol_filename(char)
                img_path = os.path.join(self.symbols_dir, f"{filename}.png")
                if os.path.exists(img_path):
                    current_width += char_width + spacing
                    if current_width > max_width:
                        lines.append(current_line)
                        current_line = []
                        current_width = char_width + spacing
                    current_line.append(filename)
        
        if current_line:
            lines.append(current_line)
        
        total_height = padding * 2 + len(lines) * line_height
        
        pixmap = QPixmap(max_width + padding * 2, total_height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        y = padding
        for line in lines:
            x = padding
            for filename in line:
                if filename is None:
                    x += word_gap
                else:
                    img_path = os.path.join(self.symbols_dir, f"{filename}.png")
                    if os.path.exists(img_path):
                        symbol = QPixmap(img_path).scaled(
                            pix_w, pix_h,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        painter.drawPixmap(x, y + 5, symbol)
                        x += char_width + spacing
            y += line_height
        
        painter.end()
        pixmap.save(file_path, "PNG")
        QMessageBox.information(self, "Exported", f"Saved to:\n{file_path}")
    
    def _encode(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        self._last_plaintext = text
        morse_parts = []
        
        for char in text.upper():
            if char in TEXT_TO_MORSE:
                morse_parts.append(TEXT_TO_MORSE[char])
            else:
                morse_parts.append('#')
        
        self._last_morse = ' '.join(morse_parts)
        
        self._display_results_symbols(text)
        self.text_output.setPlainText(self._last_morse)
        self.results_info.setText(
            f"Encoded {len(text)} characters → {len(self._last_morse.split())} Morse symbols"
        )
        self.tabs.setCurrentIndex(1)
    
    def _decode(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        if not any(c in text for c in '.-'):
            QMessageBox.warning(
                self, "Invalid Input",
                "Input doesn't appear to be Morse code.\n"
                "Use . (dot) and - (dash) for Morse, spaces between letters, / between words."
            )
            return
        
        clean = text.replace('_', '-')
        words = clean.split(' / ')
        decoded_words = []
        
        for word in words:
            letters = word.strip().split()
            decoded_word = []
            for letter in letters:
                if letter in MORSE_TO_TEXT:
                    decoded_word.append(MORSE_TO_TEXT[letter])
                else:
                    decoded_word.append('#')
            decoded_words.append(''.join(decoded_word))
        
        decoded_text = ' '.join(decoded_words).strip()
        self._last_plaintext = decoded_text
        self._last_morse = clean
        
        self._display_results_symbols(decoded_text)
        self.text_output.setPlainText(decoded_text)
        self.results_info.setText(
            f"Decoded {len(clean.split())} Morse symbols → {len(decoded_text)} characters"
        )
        self.tabs.setCurrentIndex(1)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()
        if hasattr(self, 'ref_grid_layout'):
            self._filter_reference(self._current_ref_category)
        if self._last_displayed_source:
            self._display_results_symbols(self._last_displayed_source)