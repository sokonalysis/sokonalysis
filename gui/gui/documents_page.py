# gui/documents_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from gui.card_grid import CardGrid
from gui.search_registry import register_options

import os
import sys

# Register at module level
register_options("Documents", [
    ("Zip File", "Crack password-protected ZIP archives using John the Ripper with wordlist support"),
    ("Rar File", "Crack password-protected RAR archives using John the Ripper with wordlist support"),
    ("PDF File", "Crack password-protected PDF documents using John the Ripper or pdfcrack"),
    ("Office Document", "Crack password-protected Word, Excel, PowerPoint files"),
    ("7z File", "Crack password-protected 7z archives using John the Ripper with wordlist support"),
])

class DocumentsPage(QWidget):
    """Documents options submenu page."""
    
    def __init__(self, theme_manager, back_callback, on_option_clicked):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.on_option_clicked = on_option_clicked
        self.card_grid = None
        self._init_ui()
    
    def _init_ui(self):
        # Match CTF RSA page margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)  # Changed from 40,40,40,50
        layout.setSpacing(20)
        
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
        header.addWidget(back_btn)
        header.addStretch()
        
        title = QLabel("Documents")
        title.setObjectName("pageTitle")
        
        desc = QLabel("Crack password-protected document files and archives:")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        
        separator = QFrame()
        separator.setObjectName("separator")
        
        options = [
            ("Zip File", "Crack password-protected ZIP archives using John the Ripper with wordlist support"),
            ("Rar File", "Crack password-protected RAR archives using John the Ripper with wordlist support"),
            ("PDF File", "Crack password-protected PDF documents using John the Ripper or pdfcrack"),
            ("Office Document", "Crack password-protected Word, Excel, PowerPoint files"),
            ("7z File", "Crack password-protected 7z archives using John the Ripper with wordlist support"),
        ]
        
        self.card_grid = CardGrid()
        self.card_grid.add_cards(options, self.theme, self.on_option_clicked)
        
        layout.addLayout(header)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(self.card_grid)
        # Removed layout.addStretch() - matching CTF RSA page
    
    def refresh_theme(self):
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)