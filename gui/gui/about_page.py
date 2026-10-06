# gui/about_page.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from gui.utils import get_version, get_os_info, find_logo, get_arch, get_python_version


class AboutDialog(QDialog):
    """About popup dialog for sokonalysis."""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.setWindowTitle("About sokonalysis")
        self.setFixedWidth(420)
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(6)
        
        t = self.theme.current
        
        # Logo
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel()
        logo_path = find_logo()
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
        logo_label.setFixedSize(80, 80)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        logo_layout.addWidget(logo_label)
        
        layout.addLayout(logo_layout)
        
        # App name
        app_name = QLabel("sokonalysis")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet(f"font-size: 34px; font-weight: 800; letter-spacing: 2px; color: {t['text']}; background: transparent;")
        layout.addWidget(app_name)
        
        # Tagline
        tagline = QLabel("The Cipher Toolkit Built For All Skill Levels")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setWordWrap(True)
        tagline.setStyleSheet(f"font-size: 11px; color: {t['text_tertiary']}; background: transparent; padding: 0 10px;")
        layout.addWidget(tagline)
        
        # Version
        version = QLabel(f"Version {get_version()}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"font-size: 14px; color: {t['text_secondary']}; background: transparent;")
        layout.addWidget(version)
        
        layout.addSpacing(6)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {t['border']};")
        layout.addWidget(sep)
        
        # System info
        os_info = get_os_info()
        arch = get_arch()
        
        info_text = f"<b>System:</b> {os_info}<br><b>Architecture:</b> {arch}"
        info_text += f"<br><b>Python:</b> {get_python_version()}"
        
        sys_info = QLabel(info_text)
        sys_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sys_info.setStyleSheet(f"font-size: 12px; color: {t['text_secondary']}; background: transparent;")
        sys_info.setWordWrap(True)
        layout.addWidget(sys_info)
        
        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {t['border']};")
        layout.addWidget(sep2)
        
        # Creators
        creators = QLabel("Created by Soko James & Rosaria Phiri")
        creators.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creators.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {t['text']}; background: transparent;")
        layout.addWidget(creators)
        
        # University
        university = QLabel("Kapasa Makasa University (KMU)")
        university.setAlignment(Qt.AlignmentFlag.AlignCenter)
        university.setStyleSheet(f"font-size: 12px; color: {t['text_secondary']}; background: transparent;")
        layout.addWidget(university)
        
        # Copyright
        copyright_label = QLabel("\u00a9 2024-2026 Kapasa Makasa University")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet(f"font-size: 11px; color: {t['text_tertiary']}; background: transparent;")
        layout.addWidget(copyright_label)
        
        layout.addSpacing(4)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("actionButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setMinimumHeight(38)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t['base']};
            }}
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 12px;
                font-weight: 700;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {t['surface0']};
            }}
        """)