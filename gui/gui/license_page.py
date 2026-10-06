# gui/license_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QTextCursor, QTextBlockFormat
from gui.layout_manager import layout_manager
import os, sys


class LicensePage(QWidget):
    """License page that displays the LICENSE file content."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._init_ui()
        layout_manager.layout_changed.connect(self._on_layout_changed)
    
    def _get_license_path(self):
        base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..')
        paths = [
            os.path.join(base, 'LICENSE'),
            os.path.join(base, '..', 'LICENSE'),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None
    
    def _on_layout_changed(self, layout_type):
        self._apply_theme()
    
    def _get_dynamic_values(self):
        title_font = layout_manager.get_scaled_font_size(24)
        text_font = layout_manager.get_scaled_font_size(14)
        back_font = layout_manager.get_scaled_font_size(14)
        title_font = max(16, title_font)
        text_font = max(10, text_font)
        back_font = max(10, back_font)
        return {
            "title_font": title_font,
            "text_font": text_font,
            "back_font": back_font,
        }
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        values = self._get_dynamic_values()
        
        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)
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
        
        # Set dynamic font on back button
        back_font = QFont()
        back_font.setPixelSize(values["back_font"])
        back_btn.setFont(back_font)
        
        title = QLabel("License")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        
        license_path = self._get_license_path()
        if license_path:
            with open(license_path, 'r', encoding='utf-8') as f:
                license_text = f.read()
            self.text_display.setPlainText(license_text)
        else:
            self.text_display.setPlainText("LICENSE file not found.")
        
        # Center all text
        self._center_all_text()
        
        # Scroll to top
        self.text_display.moveCursor(QTextCursor.MoveOperation.Start)
        
        layout.addWidget(self.text_display)
        self._apply_theme()
    
    def _center_all_text(self):
        """Center all text blocks in the QTextEdit."""
        cursor = self.text_display.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cursor.mergeBlockFormat(block_format)
        cursor.clearSelection()
        self.text_display.setTextCursor(cursor)
    
    def _apply_theme(self):
        t = self.theme.current
        values = self._get_dynamic_values()
        title_font = values["title_font"]
        text_font = values["text_font"]
        back_font = values["back_font"]
        
        self.setStyleSheet(f"background-color:{t['base']};")
        
        # Update back button font
        for child in self.findChildren(QPushButton):
            if child.objectName() == "backButton":
                font = QFont()
                font.setPixelSize(back_font)
                child.setFont(font)
        
        for child in self.findChildren(QLabel):
            if child.objectName() == "pageTitle":
                child.setStyleSheet(f"""
                    color: {t['text']};
                    font-size: {title_font}px;
                    font-weight: bold;
                    background: transparent;
                """)
        
        self.text_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['base']};
                color: {t['text']};
                border: none;
                padding: 20px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: {text_font}px;
            }}
        """)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()