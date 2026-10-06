# gui/json_config_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
import os, sys, json


class JsonConfigPage(QWidget):
    
    json_configured = Signal(str)
    
    def __init__(self, theme_manager, back_callback, json_path=""):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.json_path = json_path
        self.saved_successfully = False
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and filepath.endswith('.json'):
                if self._validate_json(filepath):
                    self.json_path = filepath
                    self.json_display.setText(filepath)
                    self._update_json_info()
                    self._update_drop_preview()
                    self._update_badge()
    
    def _validate_json(self, filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            required = ['alphabet', 'quadgrams', 'nbr_quadgrams', 'most_frequent_quadgram']
            missing = [k for k in required if k not in data]
            if missing:
                QMessageBox.warning(
                    self, "Invalid Quadgram File",
                    f"The file is missing required keys:\n{', '.join(missing)}\n\n"
                    f"Required: alphabet, quadgrams, nbr_quadgrams, most_frequent_quadgram"
                )
                return False
            return True
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Invalid JSON", "The file is not valid JSON.")
            return False
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read file:\n{str(e)}")
            return False
    
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
        
        # JSON status badge
        badge_container = QHBoxLayout()
        badge_container.setSpacing(4)
        self.json_icon = QLabel()
        self.json_icon.setFixedSize(18, 18)
        self.json_icon.setStyleSheet("background:transparent;")
        self.json_badge = QLabel()
        self._update_badge()
        badge_container.addWidget(self.json_icon)
        badge_container.addWidget(self.json_badge)
        header.addLayout(badge_container)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("Configure the quadgram JSON file used for substitution cipher frequency analysis.")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Drop zone for JSON file
        self.drop_group = QGroupBox("Quadgram JSON File")
        drop_layout = QVBoxLayout()
        
        self.drop_preview = QLabel()
        self.drop_preview.setFixedHeight(120)
        self.drop_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_preview.setText("Drag & drop a .json quadgram file here\nor click Browse to select")
        drop_layout.addWidget(self.drop_preview)
        
        self.json_info = QLabel("")
        drop_layout.addWidget(self.json_info)
        
        upload_row = QHBoxLayout()
        self.json_display = QLineEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setPlaceholderText("No quadgram file selected...")
        if self.json_path:
            self.json_display.setText(self.json_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setMinimumHeight(42)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_json)
        
        upload_row.addWidget(self.json_display, 1)
        upload_row.addWidget(browse_btn)
        drop_layout.addLayout(upload_row)
        
        self.drop_group.setLayout(drop_layout)
        layout.addWidget(self.drop_group)
        
        # Save button
        save_btn = QPushButton("Save Configuration")
        save_btn.setObjectName("actionButton")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_configuration)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        self._apply_theme()
        
        if self.json_path:
            self._update_drop_preview()
            self._update_badge()
    
    def _update_drop_preview(self):
        """Update drop zone preview with file info - clean styling like steganography_extract."""
        t = self.theme.current
        if self.json_path and os.path.exists(self.json_path):
            fn = os.path.basename(self.json_path)
            sz = os.path.getsize(self.json_path)
            ss = f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
            
            try:
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                alphabet = data.get('alphabet', 'unknown')
                self.drop_preview.setText(f"📄 {fn}\n{ss} | Alphabet: '{alphabet}' ({len(alphabet)} chars)")
            except:
                self.drop_preview.setText(f"📄 {fn}\n{ss}")
            
            self.drop_preview.setStyleSheet(f"""
                border: 2px dashed {t['border']};
                border-radius: 8px;
                background: transparent;
                color: {t['text']};
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
            """)
        else:
            self.drop_preview.setText("Drag & drop a .json quadgram file here\nor click Browse to select")
            self.drop_preview.setStyleSheet(f"""
                border: 2px dashed {t['border']};
                border-radius: 8px;
                background: transparent;
                color: {t['text_tertiary']};
                font-size: 13px;
                padding: 10px;
            """)
    
    def _update_badge(self):
        """Update JSON status badge."""
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 
            'assets', 'icons'
        )
        if self.json_path and os.path.exists(self.json_path):
            self.json_badge.setText("JSON Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.json_badge.setText("No JSON")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        
        self.json_badge.setStyleSheet(f"padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;background:{c}22;color:{c};")
        if os.path.exists(icon_path) and hasattr(self, 'json_icon'):
            self.json_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _update_json_info(self):
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            
            alphabet = data.get('alphabet', 'unknown')
            nbr_quads = data.get('nbr_quadgrams', 0)
            most_freq = data.get('most_frequent_quadgram', 'unknown')
            
            self.json_info.setText(
                f"Valid quadgram file | Alphabet: '{alphabet}' ({len(alphabet)} chars) | "
                f"Most frequent: '{most_freq}' | Total: {nbr_quads:,}"
            )
        except:
            self.json_info.setText("Could not read file info")
    
    def _browse_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Quadgram JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            if self._validate_json(file_path):
                self.json_path = file_path
                self.json_display.setText(file_path)
                self._update_json_info()
                self._update_drop_preview()
                self._update_badge()
    
    def _save_configuration(self):
        if not self.json_path:
            QMessageBox.warning(self, "No File", "Please select a quadgram JSON file first.")
            return
        
        if not os.path.exists(self.json_path):
            QMessageBox.warning(self, "File Not Found", "Selected JSON file does not exist.")
            return
        
        if not self._validate_json(self.json_path):
            return
        
        self.json_configured.emit(self.json_path)
        self._update_badge()
        
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 
            'assets', 'icons'
        )
        yes_icon_path = os.path.join(icons_dir, "yes.png")
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Configuration Saved")
        msg.setIcon(QMessageBox.Icon.Information)
        if os.path.exists(yes_icon_path):
            msg.setIconPixmap(
                QPixmap(yes_icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, 
                                               Qt.TransformationMode.SmoothTransformation)
            )
        msg.setText("Quadgram configuration saved!")
        msg.setInformativeText(f"File: {os.path.basename(self.json_path)}")
        msg.exec()
        
        self.back_callback()
    
    def _apply_theme(self):
        t = self.theme.current
        
        # Group box
        group_style = f"""
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
        """
        if hasattr(self, 'drop_group'): 
            self.drop_group.setStyleSheet(group_style)
        
        # Info label
        self.json_info.setStyleSheet(f"color: {t['text_tertiary']}; font-size: 12px; background: transparent;")
        
        # Description
        for label in self.findChildren(QLabel):
            if label.objectName() == "pageSubtitle":
                label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 14px; background: transparent;")
            elif label.objectName() == "pageTitle":
                label.setStyleSheet(f"font-size: 26px; font-weight: 700; color: {t['text']}; background: transparent;")
        
        # Input
        self.json_display.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
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
            elif btn.objectName() == "actionButton":
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
        
        self._update_drop_preview()
        self._update_badge()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()