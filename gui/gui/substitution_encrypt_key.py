# gui/substitution_encrypt_key.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QApplication, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os, sys, string
from gui.layout_manager import layout_manager


class SubstitutionEncryptKeyPage(QWidget):
    """Encrypt substitution cipher with known key."""
    
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
        
        title = QLabel("Substitution Cipher - Encrypt with Known Key")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_results(), "Results")
        
        # Floor the tabs area so the input never collapses in compact mode
        self.tabs.setMinimumHeight(400)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;
            font-size:{int(12 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for g in [self.in_grp, self.key_grp, self.res_grp]:
            try:
                g.setStyleSheet(gs)
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
        for btn in self.findChildren(QPushButton):
            try:
                if btn.text() == "Encrypt":
                    btn.setMinimumHeight(max(42, int(52 * scale)))
            except RuntimeError:
                pass
        
        self.input_text.setStyleSheet(
            f"QTextEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
        )
        self.key_input.setStyleSheet(
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
        )
        self.output_text.setStyleSheet(
            f"QTextEdit{{background:{t['crust']};color:{t['success']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
            f"font-family:JetBrains Mono;font-size:{int(18 * scale)}px;font-weight:700;}}"
        )
        
        # Re-floor the input area and key input on every theme change
        if hasattr(self, 'input_text') and self.input_text is not None:
            self.input_text.setMinimumHeight(max(120, int(160 * scale)))
        if hasattr(self, 'key_input') and self.key_input is not None:
            self.key_input.setMinimumHeight(max(40, int(44 * scale)))
        if hasattr(self, 'output_text') and self.output_text is not None:
            self.output_text.setMinimumHeight(max(150, int(200 * scale)))
        
        # Reapply hint style if present
        if hasattr(self, 'hint') and self.hint is not None:
            self.hint.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{int(11 * scale)}px;"
                f"background:transparent;padding:0 4px;"
            )
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        # Plaintext
        self.in_grp = QGroupBox("Plaintext")
        il = QVBoxLayout()
        il.setSpacing(10)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter plaintext to encrypt...")
        self.input_text.setMinimumHeight(160)
        self.input_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        il.addWidget(self.input_text, 1)
        
        # Paste / Clear row
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.input_text))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        il.addLayout(btn_row)
        
        self.in_grp.setLayout(il)
        
        # Substitution key
        self.key_grp = QGroupBox("Substitution Key (26 letters)")
        kl = QVBoxLayout()
        kl.setSpacing(10)
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText(
            "Enter substitution alphabet (e.g., QWERTYUIOPASDFGHJKLZXCVBNM)"
        )
        self.key_input.setMinimumHeight(44)
        self.key_input.setMaxLength(26)
        kl.addWidget(self.key_input)
        
        # Key Paste / Clear row
        k_btn_row = QHBoxLayout()
        k_paste = QPushButton("Paste")
        k_paste.setObjectName("actionButton")
        k_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        k_paste.clicked.connect(lambda: self._paste_to(self.key_input))
        k_clear = QPushButton("Clear")
        k_clear.setObjectName("dangerButton")
        k_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        k_clear.clicked.connect(self.key_input.clear)
        k_btn_row.addWidget(k_paste)
        k_btn_row.addWidget(k_clear)
        k_btn_row.addStretch()
        kl.addLayout(k_btn_row)
        
        self.key_grp.setLayout(kl)
        
        self.hint = QLabel("A→first key letter, B→second, etc. (26 unique letters)")
        self.hint.setStyleSheet(
            f"color:{self.theme.current['text_tertiary']};font-size:11px;"
            f"background:transparent;padding:0 4px;"
        )
        self.hint.setWordWrap(True)
        
        br = QHBoxLayout()
        br.addStretch()
        encrypt_btn = QPushButton("Encrypt")
        encrypt_btn.setObjectName("actionButton")
        encrypt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        encrypt_btn.clicked.connect(self._encrypt)
        br.addWidget(encrypt_btn)
        
        l.addWidget(self.in_grp, 2)
        l.addWidget(self.key_grp, 1)
        l.addWidget(self.hint)
        l.addLayout(br)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.res_grp = QGroupBox("Encrypted Output")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        
        # Copy button in header row
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Encrypted Text:"))
        hdr.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_output)
        hdr.addWidget(copy_btn)
        rl.addLayout(hdr)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Encrypted text will appear here...")
        self.output_text.setMinimumHeight(200)
        self.output_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        rl.addWidget(self.output_text, 1)
        
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _paste_to(self, widget):
        """Paste clipboard contents into the given widget (QTextEdit or QLineEdit)."""
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        if isinstance(widget, QTextEdit):
            widget.setPlainText(clipboard)
        else:
            widget.setText(clipboard.strip())
    
    def _clear_all(self):
        """Clear plaintext, key, and output."""
        self.input_text.clear()
        self.key_input.clear()
        self.output_text.clear()
    
    def _copy_output(self):
        """Copy the encrypted output to the clipboard."""
        text = self.output_text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Encrypted text copied to clipboard!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No encrypted text available yet.")
    
    def _encrypt(self):
        plaintext = self.input_text.toPlainText()
        key = self.key_input.text().strip().upper()
        
        if not plaintext.strip():
            QMessageBox.warning(self, "No Input", "Please enter plaintext to encrypt.")
            return
        if not key or len(key) != 26:
            self.output_text.setPlainText("Please enter a valid 26-letter substitution key.")
            self.tabs.setCurrentIndex(1)
            return
        if len(set(key)) != 26:
            self.output_text.setPlainText("Key must contain 26 unique letters.")
            self.tabs.setCurrentIndex(1)
            return
        
        # Build encryption mapping: plaintext letter → ciphertext letter
        plain_alphabet = string.ascii_uppercase
        encrypt_map = {}
        for i, plain_letter in enumerate(plain_alphabet):
            encrypt_map[plain_letter] = key[i]
            encrypt_map[plain_letter.lower()] = key[i].lower()
        
        result = []
        for char in plaintext:
            if char in encrypt_map:
                result.append(encrypt_map[char])
            else:
                result.append(char)
        
        self.output_text.setPlainText(''.join(result))
        self.tabs.setCurrentIndex(1)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()