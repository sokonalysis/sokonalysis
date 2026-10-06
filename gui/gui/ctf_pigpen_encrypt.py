# gui/ctf_pigpen_encrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QScrollArea, QTextBrowser,
    QFrame, QApplication, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter
import os
import sys
import base64


PIGPEN_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class PigpenEncryptPage(QWidget):
    """Pigpen Cipher Encrypt page with real symbol images."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.symbols_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'symbols', 'pigpen'
        )
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
        
        title = QLabel("Pigpen Encrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_alphabet_tab(), "Alphabet")
        
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
        
        self.input_group = QGroupBox("Plaintext")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        self.plaintext_input = QTextEdit()
        self.plaintext_input.setPlaceholderText("Enter plaintext to encrypt...\nExample: HELLO WORLD")
        self.plaintext_input.setMinimumHeight(120)
        input_layout.addWidget(self.plaintext_input)
        
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.plaintext_input.clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        input_layout.addLayout(btn_row)
        self.input_group.setLayout(input_layout)
        layout.addWidget(self.input_group)
        
        self.execute_btn = QPushButton("Encrypt")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setMinimumHeight(48)
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        layout.addWidget(self.execute_btn)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Encrypted Output:")
        
        copy_btn = QPushButton("Copy as Text")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_as_text)
        
        export_btn = QPushButton("Export as PNG")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_as_png)
        
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        results_header.addWidget(export_btn)
        layout.addLayout(results_header)
        
        # Results text area - fills available space, scrolls when needed
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text, 1)  # Stretch factor 1 = fill all available space
        
        self.results_info = QLabel("")
        layout.addWidget(self.results_info)
        return widget
    
    def _create_alphabet_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(30)
        
        # Row 1: A-M (letters on top of symbols)
        row1_layout = QGridLayout()
        row1_layout.setSpacing(8)
        
        for i, letter in enumerate('ABCDEFGHIJKLM'):
            col = i
            
            letter_lbl = QLabel(letter)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_lbl.setStyleSheet(f"font-weight:700; font-size:16px; color:{self.theme.current['text']};")
            row1_layout.addWidget(letter_lbl, 0, col)
            
            img_path = os.path.join(self.symbols_dir, f"{letter}.png")
            symbol_lbl = QLabel()
            symbol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                symbol_lbl.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                symbol_lbl.setText("?")
            symbol_lbl.setFixedSize(64, 64)
            row1_layout.addWidget(symbol_lbl, 1, col)
        
        layout.addLayout(row1_layout)
        
        # Row 2: N-Z (letters below symbols)
        row2_layout = QGridLayout()
        row2_layout.setSpacing(8)
        
        for i, letter in enumerate('NOPQRSTUVWXYZ'):
            col = i
            
            img_path = os.path.join(self.symbols_dir, f"{letter}.png")
            symbol_lbl = QLabel()
            symbol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                symbol_lbl.setPixmap(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                symbol_lbl.setText("?")
            symbol_lbl.setFixedSize(64, 64)
            row2_layout.addWidget(symbol_lbl, 0, col)
            
            letter_lbl = QLabel(letter)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_lbl.setStyleSheet(f"font-weight:700; font-size:16px; color:{self.theme.current['text']};")
            row2_layout.addWidget(letter_lbl, 1, col)
        
        layout.addLayout(row2_layout)
        
        layout.addStretch()
        scroll.setWidget(inner)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _paste(self):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            self.plaintext_input.setPlainText(clipboard)
    
    def _execute(self):
        plaintext = self.plaintext_input.toPlainText().strip().upper()
        if not plaintext:
            QMessageBox.warning(self, "No Input", "Please enter plaintext.")
            return
        
        self._last_plaintext = plaintext
        
        t = self.theme.current
        bg = t['crust']
        
        html_parts = [f'<div style="line-height:2.2;">']
        
        for char in plaintext:
            if char == ' ':
                html_parts.append('<span style="display:inline-block;width:20px;"></span>')
            elif char in PIGPEN_LETTERS:
                img_path = os.path.join(self.symbols_dir, f"{char}.png")
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode()
                    html_parts.append(f'<img src="data:image/png;base64,{b64}" width="52" height="52" style="vertical-align:middle;margin:1px;" title="{char}">')
                else:
                    html_parts.append(f'<span style="font-size:20px;font-weight:700;">[{char}]</span>')
        
        html_parts.append('</div>')
        
        self.results_text.setHtml(''.join(html_parts))
        self.results_info.setText(f"Encrypted {len(plaintext)} characters")
        self.tabs.setCurrentIndex(1)
    
    def _copy_as_text(self):
        if not hasattr(self, '_last_plaintext'):
            QMessageBox.warning(self, "Nothing to Copy", "Run encryption first.")
            return
        
        result = []
        for char in self._last_plaintext:
            if char == ' ':
                result.append(' ')
            elif char in PIGPEN_LETTERS:
                result.append(f'[{char}]')
        
        text = ''.join(result)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", f"Copied: {text}")
    
    def _export_as_png(self):
        if not hasattr(self, '_last_plaintext'):
            QMessageBox.warning(self, "Nothing to Export", "Run encryption first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Pigpen Cipher", "pigpen_output.png",
            "PNG Images (*.png)"
        )
        if not file_path:
            return
        
        char_width = 60
        spacing = 3
        max_width = 700
        
        lines = []
        current_line = []
        current_width = 0
        
        for char in self._last_plaintext:
            if char == ' ':
                current_width += 22
                if current_width > max_width:
                    lines.append(current_line)
                    current_line = []
                    current_width = 0
                current_line.append(None)
            elif char in PIGPEN_LETTERS:
                current_width += char_width + spacing
                if current_width > max_width:
                    lines.append(current_line)
                    current_line = []
                    current_width = char_width + spacing
                current_line.append(char)
        
        if current_line:
            lines.append(current_line)
        
        line_height = 62
        padding = 10
        total_height = padding * 2 + len(lines) * line_height
        
        pixmap = QPixmap(max_width + padding * 2, total_height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        y = padding
        for line in lines:
            x = padding
            for char in line:
                if char is None:
                    x += 22
                else:
                    img_path = os.path.join(self.symbols_dir, f"{char}.png")
                    if os.path.exists(img_path):
                        symbol = QPixmap(img_path).scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        painter.drawPixmap(x, y + 4, symbol)
                        x += char_width + spacing
            y += line_height
        
        painter.end()
        pixmap.save(file_path, "PNG")
        QMessageBox.information(self, "Exported", f"Saved to:\n{file_path}")
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        if hasattr(self, 'input_group') and self.input_group is not None:
            try:
                self.input_group.setStyleSheet(gs)
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
        
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        if hasattr(self, 'plaintext_input') and self.plaintext_input is not None:
            try:
                self.plaintext_input.setStyleSheet(ts)
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_text') and self.results_text is not None:
            try:
                self.results_text.setStyleSheet(f"background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-size:18px;font-weight:700;")
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()