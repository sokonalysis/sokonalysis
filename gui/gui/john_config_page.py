# gui/john_config_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
import os, sys, shutil


class JohnConfigPage(QWidget):
    """John the Ripper session data management."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        t = self.theme.current
        
        # Header
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
        
        title = QLabel("Configurations")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        # John status badge
        badge_container = QHBoxLayout()
        badge_container.setSpacing(4)
        self.john_icon = QLabel()
        self.john_icon.setFixedSize(18, 18)
        self.john_icon.setStyleSheet("background:transparent;")
        self.john_badge = QLabel()
        self._update_badge()
        badge_container.addWidget(self.john_icon)
        badge_container.addWidget(self.john_badge)
        header.addLayout(badge_container)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("Manage John the Ripper session data, pot files, and cached sessions.")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Pot files group
        self.pot_group = QGroupBox("Pot Files & Sessions")
        pot_layout = QVBoxLayout()
        pot_layout.setSpacing(10)
        
        self.pot_desc = QLabel(
            "John stores cracked passwords in pot files and session state in ~/.john/. "
            "If cracking returns wrong results or gets stuck, clearing these files can resolve the issue."
        )
        self.pot_desc.setWordWrap(True)
        pot_layout.addWidget(self.pot_desc)
        
        self.clear_pot_btn = QPushButton("Clear Pot Files")
        self.clear_pot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_pot_btn.setMinimumHeight(42)
        self.clear_pot_btn.clicked.connect(self._clear_pot_files)
        pot_layout.addWidget(self.clear_pot_btn)
        
        self.clear_sessions_btn = QPushButton("Clear Session Files")
        self.clear_sessions_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_sessions_btn.setMinimumHeight(42)
        self.clear_sessions_btn.clicked.connect(self._clear_sessions)
        pot_layout.addWidget(self.clear_sessions_btn)
        
        self.clear_all_btn = QPushButton("Clear Everything")
        self.clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_btn.setMinimumHeight(42)
        self.clear_all_btn.clicked.connect(self._clear_all)
        pot_layout.addWidget(self.clear_all_btn)
        
        self.pot_group.setLayout(pot_layout)
        layout.addWidget(self.pot_group)
        
        layout.addStretch()
        
        self._apply_theme()
    
    def _update_badge(self):
        """Update John status badge."""
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        
        pot = os.path.expanduser("~/.john/john.pot")
        sess_dir = os.path.expanduser("~/.john/sessions")
        has_pot = os.path.exists(pot)
        has_sessions = os.path.exists(sess_dir) and os.listdir(sess_dir)
        
        if has_pot or has_sessions:
            self.john_badge.setText("Data Present")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "jonny.png")
        else:
            self.john_badge.setText("Clean")
            c = t['success']
            icon_path = os.path.join(icons_dir, "yes.png")
        
        self.john_badge.setStyleSheet(f"padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;background:{c}22;color:{c};")
        if os.path.exists(icon_path) and hasattr(self, 'john_icon'):
            self.john_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _clear_pot_files(self):
        reply = QMessageBox.question(
            self, "Clear Pot Files",
            "Delete ~/.john/john.pot?\n\nThis stores all previously cracked passwords.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        pot = os.path.expanduser("~/.john/john.pot")
        if os.path.exists(pot):
            os.remove(pot)
            QMessageBox.information(self, "Done", "Pot file removed.")
        else:
            QMessageBox.information(self, "Done", "No pot file found.")
        
        self._update_badge()
    
    def _clear_sessions(self):
        reply = QMessageBox.question(
            self, "Clear Sessions",
            "Delete ~/.john/sessions/ directory?\n\nThis stores John's session state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        sess_dir = os.path.expanduser("~/.john/sessions")
        if os.path.exists(sess_dir):
            shutil.rmtree(sess_dir)
            QMessageBox.information(self, "Done", "Session files removed.")
        else:
            QMessageBox.information(self, "Done", "No session files found.")
        
        self._update_badge()
    
    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Clear Everything",
            "Delete ALL John the Ripper data?\n\n~/.john/john.pot\n~/.john/sessions/\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        removed = []
        pot = os.path.expanduser("~/.john/john.pot")
        if os.path.exists(pot):
            os.remove(pot)
            removed.append("pot file")
        
        sess_dir = os.path.expanduser("~/.john/sessions")
        if os.path.exists(sess_dir):
            shutil.rmtree(sess_dir)
            removed.append("sessions")
        
        msg = f"Cleared: {', '.join(removed)}" if removed else "Nothing to clear."
        QMessageBox.information(self, "Done", msg)
        
        self._update_badge()
    
    def _apply_theme(self):
        t = self.theme.current
        
        # Group box
        self.pot_group.setStyleSheet(f"""
            QGroupBox {{
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                margin-top: 14px;
                padding: 20px 16px 16px 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: {t['text']};
            }}
        """)
        
        # Description
        self.pot_desc.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px; background: transparent;")
        
        # Regular buttons
        btn_style = f"""
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
        """
        self.clear_pot_btn.setStyleSheet(btn_style)
        self.clear_sessions_btn.setStyleSheet(btn_style)
        
        # Danger button (Clear Everything)
        self.clear_all_btn.setStyleSheet(f"""
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
        
        # Back button
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "backButton":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {t['text_secondary']};
                        border: none;
                        font-size: 13px;
                        font-weight: 500;
                        padding: 6px 0px;
                    }}
                    QPushButton:hover {{
                        color: {t['text']};
                    }}
                """)
        
        # Page title
        for label in self.findChildren(QLabel):
            if label.objectName() == "pageTitle":
                label.setStyleSheet(f"""
                    font-size: 26px;
                    font-weight: 700;
                    color: {t['text']};
                    background: transparent;
                """)
            elif label.objectName() == "pageSubtitle":
                label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 14px; background: transparent;")
        
        self._update_badge()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()