# gui/base100_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os
import sys


class Base100Page(QWidget):
    """Base100 Encoder/Decoder - emoji range U+1F3F7 to U+1F4F6."""
    
    BASE_START = 0x1F3F7  # 🏷
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
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
        
        title = QLabel("Base💯")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_results(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;font-size:12px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for g in [self.in_grp, self.res_grp]:
            g.setStyleSheet(gs)
        
        self.input_text.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,Consolas,monospace;font-size:13px;}}")
        self.output_text.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,Consolas,monospace;font-size:18px;font-weight:700;}}")
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.in_grp = QGroupBox("Input")
        il = QVBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter text to encode or emojis to decode...")
        self.input_text.setMaximumHeight(100)
        self.input_text.setMinimumHeight(80)
        il.addWidget(self.input_text)
        self.in_grp.setLayout(il)
        
        br = QHBoxLayout()
        br.addStretch()
        encode_btn = QPushButton("Encode")
        encode_btn.setObjectName("actionButton")
        encode_btn.setMinimumHeight(42)
        encode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        encode_btn.clicked.connect(self._encode)
        br.addWidget(encode_btn)
        
        decode_btn = QPushButton("Decode")
        decode_btn.setObjectName("actionButton")
        decode_btn.setMinimumHeight(42)
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
        l.setSpacing(14)
        self.res_grp = QGroupBox("Output")
        rl = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Result will appear here...")
        self.output_text.setMinimumHeight(100)
        self.output_text.setMaximumHeight(120)
        rl.addWidget(self.output_text)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp)
        l.addStretch()
        return w
    
    def _base100_encode(self, data):
        """Encode bytes to Base100 emoji string."""
        result = []
        for byte in data:
            result.append(chr(self.BASE_START + byte))
        return ''.join(result)
    
    def _base100_decode(self, encoded):
        """Decode Base100 emoji string to bytes."""
        result = bytearray()
        for char in encoded:
            code = ord(char)
            if self.BASE_START <= code <= self.BASE_START + 255:
                result.append(code - self.BASE_START)
            else:
                raise ValueError(f"Invalid Base100 character: {char}")
        return bytes(result)
    
    def _encode(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        try:
            encoded = self._base100_encode(text.encode('utf-8'))
            self.output_text.setPlainText(encoded)
        except Exception as e:
            self.output_text.setPlainText(f"Error: {str(e)}")
        
        self.tabs.setCurrentIndex(1)
    
    def _decode(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            return
        
        try:
            decoded = self._base100_decode(text).decode('utf-8')
            self.output_text.setPlainText(decoded)
        except Exception as e:
            self.output_text.setPlainText(f"Error: {str(e)}")
        
        self.tabs.setCurrentIndex(1)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()