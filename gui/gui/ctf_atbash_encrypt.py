# gui/ctf_atbash_encrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os
import sys
from gui.layout_manager import layout_manager


class AtbashEncryptPage(QWidget):
    """Atbash Cipher Encrypt page."""
    
    # Atbash mapping: A<->Z, B<->Y, etc.
    ATBASH_MAP = str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
        'ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba'
    )
    
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
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
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
        
        title = QLabel("Atbash Encrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_results_tab(), "Results")
        
        # Floor the tabs so the input doesn't collapse in compact mode
        self.tabs.setMinimumHeight(400)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
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
        input_layout.setSpacing(10)
        
        self.plaintext_input = QTextEdit()
        self.plaintext_input.setPlaceholderText(
            "Enter plaintext to encrypt...\nExample: HELLO WORLD"
        )
        self.plaintext_input.setMinimumHeight(180)
        self.plaintext_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        input_layout.addWidget(self.plaintext_input, 1)
        
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        input_layout.addLayout(btn_row)
        
        self.input_group.setLayout(input_layout)
        layout.addWidget(self.input_group, 1)
        
        self.execute_btn = QPushButton("Encrypt")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        layout.addWidget(self.execute_btn)
        
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
        results_label = QLabel("Encrypted Text:")
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
        self.results_output.setPlaceholderText("Encrypted text will appear here...")
        self.results_output.setMinimumHeight(200)
        self.results_output.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.results_output, 1)
        
        self.results_info = QLabel("")
        self.results_info.setWordWrap(True)
        layout.addWidget(self.results_info)
        return widget
    
    def _paste(self):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            self.plaintext_input.setPlainText(clipboard)
    
    def _clear_all(self):
        """Clear plaintext and any previous results."""
        self.plaintext_input.clear()
        self.results_output.clear()
        self.results_info.clear()
    
    def _execute(self):
        plaintext = self.plaintext_input.toPlainText().strip()
        if not plaintext:
            QMessageBox.warning(self, "No Input", "Please enter plaintext.")
            return
        
        ciphertext = plaintext.translate(self.ATBASH_MAP)
        self.results_output.setText(ciphertext)
        self.results_info.setText(f"Encrypted {len(plaintext)} characters")
        self.tabs.setCurrentIndex(1)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy yet.")
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'input_group') and self.input_group is not None:
            try:
                self.input_group.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(16 * scale)}px;"
                        f"font-weight:700;font-size:{int(14 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(16 * scale)}px;"
                        f"font-weight:700;font-size:{int(14 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        # Scale the primary "Encrypt" button so text never clips
        if hasattr(self, 'execute_btn') and self.execute_btn is not None:
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        if hasattr(self, 'plaintext_input') and self.plaintext_input is not None:
            try:
                self.plaintext_input.setStyleSheet(ts)
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(
                    f"color:{t['text_secondary']};font-size:{int(12 * scale)}px;"
                )
            except RuntimeError:
                pass
        
        # Re-floor the input and output on every theme change
        if hasattr(self, 'plaintext_input') and self.plaintext_input is not None:
            self.plaintext_input.setMinimumHeight(max(180, int(220 * scale)))
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setMinimumHeight(max(200, int(240 * scale)))
    
    def refresh_theme(self):
        self._apply_theme()