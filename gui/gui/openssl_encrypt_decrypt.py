# gui/openssl_encrypt_decrypt.py
"""
OpenSSL Encrypt/Decrypt Module
Provides GUI interface for symmetric encryption and decryption
using OpenSSL ciphers.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSpinBox, QCheckBox, QGridLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QDrag

import os
import subprocess
import sys
import tempfile


# ============================================================================
# Cipher Families
# ============================================================================

CIPHER_FAMILIES = {
    "AES": ["aes-128-cbc", "aes-128-ecb", "aes-128-ctr", "aes-128-ofb", "aes-128-cfb",
            "aes-192-cbc", "aes-192-ecb", "aes-192-ctr", "aes-192-ofb", "aes-192-cfb",
            "aes-256-cbc", "aes-256-ecb", "aes-256-ctr", "aes-256-ofb", "aes-256-cfb"],
    "ARIA": ["aria-128-cbc", "aria-128-ecb", "aria-128-ctr", "aria-128-ofb",
             "aria-128-cfb", "aria-128-cfb1", "aria-128-cfb8",
             "aria-192-cbc", "aria-192-ecb", "aria-192-ctr", "aria-192-ofb",
             "aria-192-cfb", "aria-192-cfb1", "aria-192-cfb8",
             "aria-256-cbc", "aria-256-ecb", "aria-256-ctr", "aria-256-ofb",
             "aria-256-cfb", "aria-256-cfb1", "aria-256-cfb8"],
    "Blowfish": ["bf", "bf-cbc", "bf-cfb", "bf-ecb", "bf-ofb"],
    "Camellia": ["camellia-128-cbc", "camellia-128-ecb", "camellia-192-cbc",
                 "camellia-192-ecb", "camellia-256-cbc", "camellia-256-ecb"],
    "CAST": ["cast", "cast-cbc", "cast5-cbc", "cast5-cfb", "cast5-ecb", "cast5-ofb"],
    "DES": ["des", "des-cbc", "des-cfb", "des-ecb", "des-ofb",
            "des-ede", "des-ede-cbc", "des-ede-cfb", "des-ede-ofb",
            "des-ede3", "des-ede3-cbc", "des-ede3-cfb", "des-ede3-ofb", "des3", "desx"],
    "RC2": ["rc2", "rc2-40-cbc", "rc2-64-cbc", "rc2-cbc", "rc2-cfb", "rc2-ecb", "rc2-ofb"],
    "RC4": ["rc4", "rc4-40"],
    "SEED": ["seed", "seed-cbc", "seed-cfb", "seed-ecb", "seed-ofb"],
    "SM4": ["sm4-cbc", "sm4-cfb", "sm4-ctr", "sm4-ecb", "sm4-ofb"],
    "Other": ["zlib", "zstd", "base64"],
}


# ============================================================================
# Encrypt/Decrypt Worker Thread
# ============================================================================

class EncryptDecryptWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, bytes)
    
    def __init__(self, mode, input_data="", input_is_file=True, password="", 
                 cipher="aes-256-cbc", base64=False, salt=True, pbkdf2=True,
                 iterations=10000):
        super().__init__()
        self.mode = mode
        self.input_data = input_data
        self.input_is_file = input_is_file
        self.password = password
        self.cipher = cipher
        self.base64 = base64
        self.salt = salt
        self.pbkdf2 = pbkdf2
        self.iterations = iterations
        self.output_data = b""
    
    def run(self):
        try:
            if self.mode == "encrypt":
                self._encrypt()
            elif self.mode == "decrypt":
                self._decrypt()
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", b"")
    
    def _run_openssl(self, mode_flag):
        self.progress_value.emit(20)
        
        cmd = ["openssl", "enc", f"-{self.cipher}", mode_flag]
        is_special = self.cipher in ["zlib", "zstd", "base64"]
        
        if self.pbkdf2 and not is_special:
            cmd.extend(["-pbkdf2", "-iter", str(self.iterations)])
        if self.salt and not is_special:
            cmd.append("-salt")
        if self.base64:
            cmd.append("-base64")
        if not is_special:
            cmd.extend(["-pass", f"pass:{self.password}"])
        
        temp_input = None
        temp_output = None
        
        try:
            if self.input_is_file:
                if not os.path.exists(self.input_data):
                    self.finished.emit(False, "Input file not found", b"")
                    return False
                cmd.extend(["-in", self.input_data])
            else:
                temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False)
                temp_input.write(self.input_data)
                temp_input.close()
                cmd.extend(["-in", temp_input.name])
            
            temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False)
            temp_output.close()
            cmd.extend(["-out", temp_output.name])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.finished.emit(False, f"Operation failed: {result.stderr}", b"")
                return False
            
            with open(temp_output.name, 'rb') as f:
                self.output_data = f.read()
            
            return True
        finally:
            if temp_input and os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            if temp_output and os.path.exists(temp_output.name):
                os.unlink(temp_output.name)
    
    def _encrypt(self):
        try:
            self.progress.emit(f"Encrypting with {self.cipher}...")
            if not self._run_openssl("-e"):
                return
            self.progress_value.emit(100)
            self.progress.emit("Encryption completed!")
            self.finished.emit(True, self.output_data.hex(), self.output_data)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", b"")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", b"")
    
    def _decrypt(self):
        try:
            self.progress.emit(f"Decrypting with {self.cipher}...")
            if not self._run_openssl("-d"):
                return
            self.progress_value.emit(100)
            self.progress.emit("Decryption completed!")
            try:
                result = self.output_data.decode('utf-8', errors='replace')
            except:
                result = self.output_data.hex()
            self.finished.emit(True, result, self.output_data)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", b"")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", b"")


# ============================================================================
# Drag and Drop Components
# ============================================================================

class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.setFixedSize(220, 90)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _build(self, name):
        if self.layout():
            QWidget().setLayout(self.layout())
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {t['text']}; font-size: 15px; font-weight: 600; background: transparent; padding: 2px;")
        layout.addWidget(label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:12px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._build(self.mode_name)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"mode:{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class DraggableCipherFamilyCard(QFrame):
    def __init__(self, family_name, theme_colors, parent=None):
        super().__init__(parent)
        self.family_name = family_name
        self.colors = theme_colors
        self.setFixedSize(200, 70)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _build(self):
        if self.layout():
            QWidget().setLayout(self.layout())
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        label = QLabel(self.family_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {t['text']}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:10px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._build()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"family:{self.family_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class DraggableCipherCard(QFrame):
    def __init__(self, cipher_name, theme_colors, parent=None):
        super().__init__(parent)
        self.cipher_name = cipher_name
        self.colors = theme_colors
        self.setFixedSize(150, 40)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _build(self):
        if self.layout():
            QWidget().setLayout(self.layout())
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        label = QLabel(self.cipher_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {t['text']}; font-size: 11px; font-weight: 600; background: transparent;")
        layout.addWidget(label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:6px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._build()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"cipher:{self.cipher_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class DropSlot(QFrame):
    def __init__(self, theme_colors, accept_type, default_text, fixed_size=None, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.accept_type = accept_type
        self.default_text = default_text
        self.value = None
        self.display_text = ""
        if fixed_size:
            self.setFixedSize(*fixed_size)
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:12px;}}")
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:3px solid {t['accent']}88;border-radius:12px;}}")
    
    def is_filled(self):
        return self.value is not None
    
    def clear_slot(self):
        self.value = None
        self.display_text = ""
        self._style_empty()
        self.update()
    
    def set_value(self, value, display_text=""):
        self.value = value
        self.display_text = display_text
        self._style_filled()
        self.update()
    
    def _notify_parent(self, action):
        p = self.parent()
        while p is not None:
            if isinstance(p, OpenSSLEncryptDecryptPage):
                if action == "dropped":
                    p._on_slot_dropped(self.accept_type, self.value)
                elif action == "cleared":
                    p._on_slot_cleared(self.accept_type)
                break
            p = p.parent()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith(f"{self.accept_type}:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            data = event.mimeData().text()
            if data.startswith(f"{self.accept_type}:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        try:
            if data.startswith(f"{self.accept_type}:"):
                parts = data.split(':', 2)
                if len(parts) >= 2:
                    self.value = parts[1]
                    self.display_text = parts[2] if len(parts) > 2 else parts[1]
                    self._style_filled()
                    self.update()
                    event.acceptProposedAction()
                    self._notify_parent("dropped")
        except Exception:
            pass
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        if self.is_filled():
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 13, QFont.Weight.Bold))
            painter.drawText(self.rect().adjusted(15, 10, -15, -10), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.display_text)
        else:
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 11))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.default_text)
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            self._notify_parent("cleared")


# ============================================================================
# Main Encrypt/Decrypt Page
# ============================================================================

class OpenSSLEncryptDecryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        
        self.worker = None
        self.openssl_ok = self._check_openssl()
        self.mode_id = None
        self.selected_family = None
        self.selected_cipher = "aes-256-cbc"
        self.input_path = ""
        self.input_text = ""
        self.input_is_file = True
        self.output_data = b""
        
        self.mode_cards = []
        self.family_cards = []
        self.cipher_cards = []
        
        self.icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        
        self._init_widget_refs()
        self._init_ui()
        self._apply_theme()
        self.setAcceptDrops(True)
    
    def _init_widget_refs(self):
        self.mode_slot = None
        self.family_slot = None
        self.cipher_slot = None
        self.password_input = None
        self.confirm_input = None
        self.show_pass = None
        self.base64_check = None
        self.salt_check = None
        self.pbkdf2_check = None
        self.iterations_input = None
        self.input_group = None
        self.input_preview = None
        self.input_text_edit = None
        self.input_path_input = None
        self.mode_group = None
        self.options_group = None
        self.family_group = None
        self.cipher_group = None
        self.req_group = None
        self.execute_btn = None
        self.export_btn = None
        self.export_file_btn = None
        self.status_output = None
        self.status_progress = None
        self.results_output = None
        self.req_output = None
        self.install_btn = None
        self.install_status = None
        self.tabs = None
        self.tools_icon = None
        self.tool_badge = None
        self.results_metadata = None
    
    def _check_openssl(self):
        try:
            result = subprocess.run(["openssl", "version"], capture_output=True, timeout=3)
            return result.returncode == 0
        except Exception:
            return False
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                self.input_path = filepath
                self.input_is_file = True
                if self.input_path_input:
                    self.input_path_input.setText(filepath)
                if self.input_text_edit:
                    self.input_text_edit.setVisible(False)
                self._update_file_preview("input")
                self._update_execute_button()
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        layout.addLayout(self._create_header())
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_requirements_tab(), "Requirements")
        layout.addWidget(self.tabs)
        self._apply_theme()
    
    def _create_header(self):
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        back_icon_path = os.path.join(self.icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Encrypt / Decrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        tools_container = QHBoxLayout()
        tools_container.setSpacing(4)
        self.tools_icon = QLabel()
        self.tools_icon.setFixedSize(32, 32)
        self.tools_icon.setStyleSheet("background:transparent;")
        self.tool_badge = QLabel()
        self._update_tool_badge()
        tools_container.addWidget(self.tools_icon)
        tools_container.addWidget(self.tool_badge)
        header.addLayout(tools_container)
        return header
    
    def _update_tool_badge(self):
        t = self.theme.current
        if self.openssl_ok:
            self.tool_badge.setText("OpenSSL Ready")
            c = t['success']
            icon_path = os.path.join(self.icons_dir, "openssl.png")
        else:
            self.tool_badge.setText("OpenSSL Missing")
            c = t['error']
            icon_path = os.path.join(self.icons_dir, "no.png")
        self.tool_badge.setStyleSheet(f"padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:{c}22;color:{c};")
        if os.path.exists(icon_path) and self.tools_icon:
            self.tools_icon.setPixmap(QIcon(icon_path).pixmap(32, 32))
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Operation Mode
        self.mode_group = QGroupBox("1. Operation Mode (Drag card to the slot below)")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(15)
        t = self.theme.current
        for mode_id, name in [(1, "Encrypt"), (2, "Decrypt")]:
            card = DraggableModeCard(mode_id, name, t)
            self.mode_cards.append(card)
            cards_row.addWidget(card)
        cards_row.addStretch()
        mode_layout.addLayout(cards_row)
        drop_row = QHBoxLayout()
        self.mode_slot = DropSlot(t, "mode", "Drop operation here", (240, 90))
        drop_row.addWidget(self.mode_slot)
        drop_row.addStretch()
        mode_layout.addLayout(drop_row)
        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)
        
        # Cipher Family Selection
        self.family_group = QGroupBox("2. Cipher Family (Drag card to the slot)")
        self.family_group.setVisible(False)
        family_layout = QVBoxLayout()
        family_layout.setSpacing(10)
        family_cards_row = QHBoxLayout()
        family_cards_row.setSpacing(12)
        for family_name in CIPHER_FAMILIES.keys():
            card = DraggableCipherFamilyCard(family_name, t)
            self.family_cards.append(card)
            family_cards_row.addWidget(card)
        family_cards_row.addStretch()
        family_layout.addLayout(family_cards_row)
        family_drop_row = QHBoxLayout()
        self.family_slot = DropSlot(t, "family", "Drop cipher family here", (240, 70))
        family_drop_row.addWidget(self.family_slot)
        family_drop_row.addStretch()
        family_layout.addLayout(family_drop_row)
        self.family_group.setLayout(family_layout)
        layout.addWidget(self.family_group)
        
        # Cipher Selection
        self.cipher_group = QGroupBox("3. Cipher (Drag card to the slot)")
        self.cipher_group.setVisible(False)
        cipher_layout = QVBoxLayout()
        cipher_layout.setSpacing(10)
        self.cipher_cards_layout = QVBoxLayout()
        self.cipher_cards_layout.setSpacing(4)
        cipher_layout.addLayout(self.cipher_cards_layout)
        cipher_drop_row = QHBoxLayout()
        self.cipher_slot = DropSlot(t, "cipher", "Drop cipher here", (280, 50))
        self.cipher_slot.set_value("aes-256-cbc", "aes-256-cbc")
        cipher_drop_row.addWidget(self.cipher_slot)
        cipher_drop_row.addStretch()
        cipher_layout.addLayout(cipher_drop_row)
        self.cipher_group.setLayout(cipher_layout)
        layout.addWidget(self.cipher_group)
        
        # Options Section
        self.options_group = QGroupBox("4. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        # Execute Button
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setMinimumHeight(48)
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        self.execute_btn.setEnabled(False)
        layout.addWidget(self.execute_btn)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        layout.addWidget(self.status_progress)
        layout.addWidget(self.status_output)
        return widget
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.results_metadata = QLabel("")
        layout.addWidget(self.results_metadata)
        
        results_header = QHBoxLayout()
        results_header.addStretch()
        
        self.export_file_btn = QPushButton("Export to File")
        self.export_file_btn.setObjectName("actionButton")
        self.export_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_file_btn.clicked.connect(self._export_to_file)
        self.export_file_btn.hide()
        results_header.addWidget(self.export_file_btn)
        
        self.export_btn = QPushButton("Export Result")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_result)
        self.export_btn.hide()
        results_header.addWidget(self.export_btn)
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        results_header.addWidget(copy_btn)
        layout.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Result will appear here...")
        layout.addWidget(self.results_output, 1)
        return widget
    
    def _create_requirements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(14)
        self.req_group = QGroupBox("Required Tools")
        req_layout = QVBoxLayout()
        req_layout.setSpacing(10)
        self.req_output = QTextBrowser()
        self.req_output.setOpenExternalLinks(False)
        req_layout.addWidget(self.req_output)
        self.install_btn = QPushButton("Install Requirements")
        self.install_btn.setObjectName("actionButton")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._install_openssl)
        req_layout.addWidget(self.install_btn)
        self.install_status = QLabel("")
        req_layout.addWidget(self.install_status)
        self.req_group.setLayout(req_layout)
        layout.addWidget(self.req_group)
        layout.addStretch()
        self._update_requirements()
        return widget
    
    def _update_requirements(self):
        if self.req_output is None:
            return
        t = self.theme.current
        c = t['success'] if self.openssl_ok else t['error']
        html = f"<h3 style='color:{c};'>OpenSSL</h3><p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install openssl</p>"
        self.req_output.setHtml(html)
        if self.install_btn:
            self.install_btn.setEnabled(not self.openssl_ok)
            self.install_btn.setText("OpenSSL Installed" if self.openssl_ok else "Install Requirements")
    
    # ========================================================================
    # Slot Event Handlers
    # ========================================================================
    
    def _on_slot_dropped(self, slot_type, value):
        if slot_type == "mode":
            self.mode_id = int(value)
            self._show_family_selection()
        elif slot_type == "family":
            self.selected_family = value
            self._show_cipher_selection(value)
        elif slot_type == "cipher":
            self.selected_cipher = value
            self._show_options()
    
    def _on_slot_cleared(self, slot_type):
        if slot_type == "mode":
            self.mode_id = None
            self._hide_all()
        elif slot_type == "family":
            self.selected_family = None
            self.cipher_group.setVisible(False)
            self.options_group.setVisible(False)
        elif slot_type == "cipher":
            self.selected_cipher = "aes-256-cbc"
            if self.cipher_slot:
                self.cipher_slot.set_value("aes-256-cbc", "aes-256-cbc")
            self.options_group.setVisible(False)
    
    def _hide_all(self):
        self.family_group.setVisible(False)
        self.cipher_group.setVisible(False)
        self.options_group.setVisible(False)
        self.execute_btn.setEnabled(False)
    
    def _show_family_selection(self):
        if self.mode_id is None:
            return
        self.family_group.setVisible(True)
        self.cipher_group.setVisible(False)
        self.options_group.setVisible(False)
        self._clear_cipher_cards()
        self._clear_options()
        self.execute_btn.setEnabled(False)
    
    def _clear_cipher_cards(self):
        while self.cipher_cards_layout.count():
            item = self.cipher_cards_layout.takeAt(0)
            if item is None:
                continue
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
            elif item.layout():
                sl = item.layout()
                while sl.count():
                    si = sl.takeAt(0)
                    if si and si.widget():
                        si.widget().setParent(None)
                        si.widget().deleteLater()
        self.cipher_cards.clear()
    
    def _show_cipher_selection(self, family_name):
        self._clear_cipher_cards()
        self.cipher_group.setVisible(True)
        self.options_group.setVisible(False)
        self._clear_options()
        self.execute_btn.setEnabled(False)
        
        t = self.theme.current
        ciphers = CIPHER_FAMILIES.get(family_name, [])
        
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        max_cols = 5
        
        for i, cipher in enumerate(ciphers):
            row = i // max_cols
            col = i % max_cols
            card = DraggableCipherCard(cipher, t)
            self.cipher_cards.append(card)
            grid.addWidget(card, row, col)
        
        grid.setColumnStretch(max_cols, 1)
        self.cipher_cards_layout.addLayout(grid)
        self.cipher_slot.clear_slot()
        self._apply_theme()
    
    def _clear_options(self):
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        for attr in ['password_input', 'confirm_input', 'show_pass',
                     'base64_check', 'salt_check', 'pbkdf2_check', 'iterations_input',
                     'input_group', 'input_preview', 'input_text_edit', 'input_path_input']:
            setattr(self, attr, None)
        
        self.input_path = ""
        self.input_text = ""
        self.input_is_file = True
        self.execute_btn.setText("Execute")
    
    def _show_options(self):
        self._clear_options()
        if self.mode_id is None:
            return
        
        self.options_group.setVisible(True)
        t = self.theme.current
        
        # Password
        pass_group = QGroupBox("Password")
        pass_layout = QVBoxLayout()
        pass_layout.setSpacing(8)
        
        pass_row = QHBoxLayout()
        pass_row.setSpacing(8)
        pass_row.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password...")
        pass_row.addWidget(self.password_input, 1)
        pass_paste = QPushButton("Paste")
        pass_paste.setObjectName("actionButton")
        pass_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        pass_paste.setMaximumWidth(60)
        pass_paste.clicked.connect(lambda: self._paste_to(self.password_input))
        pass_row.addWidget(pass_paste)
        pass_clear = QPushButton("Clear")
        pass_clear.setObjectName("dangerButton")
        pass_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        pass_clear.setMaximumWidth(60)
        pass_clear.clicked.connect(self.password_input.clear)
        pass_row.addWidget(pass_clear)
        pass_layout.addLayout(pass_row)
        
        self.show_pass = QCheckBox("Show password")
        self.show_pass.stateChanged.connect(self._toggle_password_visibility)
        pass_layout.addWidget(self.show_pass)
        
        confirm_row = QHBoxLayout()
        confirm_row.setSpacing(8)
        confirm_row.addWidget(QLabel("Confirm:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password...")
        confirm_row.addWidget(self.confirm_input, 1)
        confirm_paste = QPushButton("Paste")
        confirm_paste.setObjectName("actionButton")
        confirm_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_paste.setMaximumWidth(60)
        confirm_paste.clicked.connect(lambda: self._paste_to(self.confirm_input))
        confirm_row.addWidget(confirm_paste)
        confirm_clear = QPushButton("Clear")
        confirm_clear.setObjectName("dangerButton")
        confirm_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_clear.setMaximumWidth(60)
        confirm_clear.clicked.connect(self.confirm_input.clear)
        confirm_row.addWidget(confirm_clear)
        pass_layout.addLayout(confirm_row)
        
        pass_group.setLayout(pass_layout)
        self.options_layout.addWidget(pass_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        options_layout.setSpacing(6)
        
        self.base64_check = QCheckBox("Base64 encode/decode output")
        options_layout.addWidget(self.base64_check)
        self.salt_check = QCheckBox("Use salt (recommended)")
        self.salt_check.setChecked(True)
        options_layout.addWidget(self.salt_check)
        self.pbkdf2_check = QCheckBox("Use PBKDF2 key derivation (recommended)")
        self.pbkdf2_check.setChecked(True)
        self.pbkdf2_check.toggled.connect(self._on_pbkdf2_toggle)
        options_layout.addWidget(self.pbkdf2_check)
        
        iter_row = QHBoxLayout()
        iter_row.setSpacing(8)
        iter_row.addWidget(QLabel("Iterations:"))
        self.iterations_input = QSpinBox()
        self.iterations_input.setRange(1000, 10000000)
        self.iterations_input.setValue(10000)
        self.iterations_input.setSingleStep(1000)
        self.iterations_input.setSuffix(" iterations")
        iter_row.addWidget(self.iterations_input, 1)
        options_layout.addLayout(iter_row)
        
        options_group.setLayout(options_layout)
        self.options_layout.addWidget(options_group)
        
        # Input
        self.input_group = QGroupBox("Input (File or Text)")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)
        file_btn = QPushButton("File Input")
        file_btn.setObjectName("actionButton")
        file_btn.setCheckable(True)
        file_btn.setChecked(self.input_is_file)
        file_btn.clicked.connect(self._switch_to_file_input)
        toggle_row.addWidget(file_btn)
        
        text_btn = QPushButton("Text Input")
        text_btn.setObjectName("actionButton")
        text_btn.setCheckable(True)
        text_btn.setChecked(not self.input_is_file)
        text_btn.clicked.connect(self._switch_to_text_input)
        toggle_row.addWidget(text_btn)
        toggle_row.addStretch()
        input_layout.addLayout(toggle_row)
        
        self.input_preview = QLabel()
        self.input_preview.setFixedHeight(60)
        self.input_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_preview.setText("Drag & drop a file here\nor click Browse to select")
        self.input_preview.setVisible(self.input_is_file)
        input_layout.addWidget(self.input_preview)
        
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.input_path_input = QLineEdit()
        self.input_path_input.setReadOnly(True)
        self.input_path_input.setPlaceholderText("No file selected...")
        self.input_path_input.setVisible(self.input_is_file)
        file_row.addWidget(self.input_path_input, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_input)
        file_row.addWidget(browse_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_input)
        file_row.addWidget(clear_btn)
        input_layout.addLayout(file_row)
        
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText("Enter text to encrypt/decrypt...")
        self.input_text_edit.setMaximumHeight(150)
        self.input_text_edit.setVisible(not self.input_is_file)
        self.input_text_edit.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.input_text_edit)
        
        self.input_group.setLayout(input_layout)
        self.options_layout.addWidget(self.input_group)
        
        self.execute_btn.setText("Encrypt" if self.mode_id == 1 else "Decrypt")
        self._apply_theme()
        self._update_execute_button()
    
    def _switch_to_file_input(self):
        self.input_is_file = True
        if self.input_preview:
            self.input_preview.setVisible(True)
        if self.input_path_input:
            self.input_path_input.setVisible(True)
        if self.input_text_edit:
            self.input_text_edit.setVisible(False)
        self._update_execute_button()
    
    def _switch_to_text_input(self):
        self.input_is_file = False
        if self.input_preview:
            self.input_preview.setVisible(False)
        if self.input_path_input:
            self.input_path_input.setVisible(False)
        if self.input_text_edit:
            self.input_text_edit.setVisible(True)
        self._update_execute_button()
    
    def _on_text_changed(self):
        self.input_text = self.input_text_edit.toPlainText() if self.input_text_edit else ""
        self._update_execute_button()
    
    def _toggle_password_visibility(self, state):
        if self.password_input and self.confirm_input:
            echo_mode = QLineEdit.EchoMode.Normal if state == Qt.CheckState.Checked.value else QLineEdit.EchoMode.Password
            self.password_input.setEchoMode(echo_mode)
            self.confirm_input.setEchoMode(echo_mode)
    
    def _on_pbkdf2_toggle(self, checked):
        if self.iterations_input:
            self.iterations_input.setEnabled(checked)
    
    def _browse_input(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "All Files (*)")
        if fp:
            self.input_path = fp
            self.input_is_file = True
            if self.input_path_input:
                self.input_path_input.setText(fp)
            if self.input_text_edit:
                self.input_text_edit.setVisible(False)
            if self.input_preview:
                self.input_preview.setVisible(True)
            self._update_file_preview("input")
            self._update_execute_button()
    
    def _clear_input(self):
        self.input_path = ""
        self.input_text = ""
        if self.input_path_input:
            self.input_path_input.clear()
        if self.input_text_edit:
            self.input_text_edit.clear()
        self._update_file_preview("input")
        self._update_execute_button()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard and widget:
            widget.setText(clipboard)
    
    def _update_file_preview(self, file_type):
        t = self.theme.current
        if file_type == "input" and self.input_preview:
            if self.input_path:
                name = os.path.basename(self.input_path)
                try:
                    size = os.path.getsize(self.input_path)
                    self.input_preview.setText(f"{name} ({size:,} bytes)")
                except:
                    self.input_preview.setText(name)
                self.input_preview.setStyleSheet(f"border:1px solid {t['border']};border-radius:8px;background:{t['crust']};color:{t['text']};font-size:13px;font-weight:600;padding:10px;")
            else:
                self.input_preview.setText("Drag & drop a file here\nor click Browse to select")
                self.input_preview.setStyleSheet(f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;padding:10px;")
    
    def _update_execute_button(self):
        mode_filled = self.mode_slot.is_filled() if self.mode_slot else False
        if not mode_filled or not self.execute_btn:
            if self.execute_btn:
                self.execute_btn.setEnabled(False)
            return
        
        if self.input_is_file:
            if not self.input_path:
                self.execute_btn.setEnabled(False)
                return
        else:
            if not self.input_text.strip():
                self.execute_btn.setEnabled(False)
                return
        
        self.execute_btn.setEnabled(True)
    
    def _install_openssl(self):
        if QMessageBox.question(self, "Install OpenSSL", "Install OpenSSL?\n\nsudo apt install -y openssl",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        if self.install_btn:
            self.install_btn.setEnabled(False)
            self.install_btn.setText("Installing...")
        if self.install_status:
            self.install_status.setText("Running: sudo apt install -y openssl")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "openssl"], capture_output=True, text=True, timeout=120)
            self.openssl_ok = self._check_openssl()
            if self.install_status:
                self.install_status.setText("Done!" if self.openssl_ok else "Failed")
        except Exception as e:
            if self.install_status:
                self.install_status.setText(f"Error: {e}")
        self._update_tool_badge()
        self._update_requirements()
    
    def _execute(self):
        if not self.mode_slot or not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Please select an operation mode")
            return
        
        mode_id = int(self.mode_slot.value)
        
        if self.input_is_file and not self.input_path:
            QMessageBox.warning(self, "Missing Input", "Please select an input file")
            return
        
        if not self.input_is_file and not self.input_text.strip():
            QMessageBox.warning(self, "Missing Input", "Please enter text to process")
            return
        
        password = self.password_input.text() if self.password_input else ""
        confirm = self.confirm_input.text() if self.confirm_input else ""
        if not password or not confirm:
            QMessageBox.warning(self, "Missing Password", "Please enter and confirm your password.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return
        
        self.tabs.setCurrentIndex(1)
        if self.status_output:
            self.status_output.clear()
        if self.results_output:
            self.results_output.clear()
        if self.status_progress:
            self.status_progress.setValue(0)
        if self.execute_btn:
            self.execute_btn.setEnabled(False)
        if self.export_btn:
            self.export_btn.hide()
        if self.export_file_btn:
            self.export_file_btn.hide()
        if self.results_metadata:
            self.results_metadata.setText("")
        
        cipher = self.selected_cipher
        base64 = self.base64_check.isChecked() if self.base64_check else False
        salt = self.salt_check.isChecked() if self.salt_check else True
        pbkdf2 = self.pbkdf2_check.isChecked() if self.pbkdf2_check else True
        iterations = self.iterations_input.value() if self.iterations_input else 10000
        mode = "encrypt" if mode_id == 1 else "decrypt"
        
        input_data = self.input_path if self.input_is_file else self.input_text
        
        self.worker = EncryptDecryptWorker(
            mode=mode, input_data=input_data, input_is_file=self.input_is_file,
            password=password, cipher=cipher, base64=base64, salt=salt,
            pbkdf2=pbkdf2, iterations=iterations
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        if self.status_output:
            self.status_output.append(msg)
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
    
    def _on_finished(self, success, result, output_data):
        if self.execute_btn:
            self.execute_btn.setEnabled(True)
        
        if success:
            self.output_data = output_data
            if self.status_output:
                self.status_output.append("SUCCESS!")
            if self.status_progress:
                self.status_progress.setValue(100)
            if self.results_output:
                self.results_output.setText(result)
            if self.results_metadata:
                self.results_metadata.setText(f"Cipher: {self.selected_cipher} | Size: {len(output_data)} bytes")
                self.results_metadata.setStyleSheet(f"color: {self.theme.current['text_secondary']}; font-size: 12px; font-weight: 600; padding: 4px 0;")
            if self.export_btn:
                self.export_btn.show()
            if self.export_file_btn:
                self.export_file_btn.show()
            self.tabs.setCurrentIndex(2)
        else:
            if self.status_output:
                self.status_output.append(f"ERROR:\n{result}")
            if self.status_progress:
                self.status_progress.setValue(100)
            QMessageBox.critical(self, "Operation Failed", result)
    
    def _copy_results(self):
        if self.results_output:
            text = self.results_output.toPlainText()
            if text:
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, "Copied", "Results copied to clipboard!")
    
    def _export_to_file(self):
        if not self.output_data:
            QMessageBox.warning(self, "No Data", "No output data to export.")
            return
        
        mode_text = "encrypted" if self.mode_id == 1 else "decrypted"
        default_name = f"{mode_text}_output.bin"
        fp, _ = QFileDialog.getSaveFileName(self, "Export to File", default_name, "All Files (*)")
        if fp:
            try:
                with open(fp, 'wb') as f:
                    f.write(self.output_data)
                QMessageBox.information(self, "Exported", f"Output saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def _export_result(self):
        if not self.results_output:
            return
        text = self.results_output.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Results", "Nothing to export")
            return
        mode_text = "encrypt" if self.mode_id == 1 else "decrypt"
        default_name = f"{mode_text}_result.txt"
        fp, _ = QFileDialog.getSaveFileName(self, "Export Result", default_name, "Text Files (*.txt);;All Files (*)")
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Exported", f"Results saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def _apply_theme(self):
        t = self.theme.current
        
        if self.tabs:
            self.tabs.setStyleSheet(f"""
                QTabWidget::pane {{ border: 1px solid {t['border']}; border-radius: 8px; background-color: {t['base']}; }}
                QTabBar::tab {{ background-color: {t['crust']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; padding: 10px 28px; margin-right: 2px; border-top-left-radius: 7px; border-top-right-radius: 7px; font-size: 13px; font-weight: 600; }}
                QTabBar::tab:selected {{ background-color: {t['base']}; color: {t['text']}; border-bottom-color: transparent; }}
            """)
        
        gs = f"""
            QGroupBox {{ color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; margin-top: 14px; padding: 20px 16px 16px; font-weight: 600; font-size: 13px; }}
            QGroupBox::title {{ left: 14px; padding: 0 8px; color: {t['text']}; }}
        """
        for attr in ['mode_group', 'options_group', 'req_group', 'family_group', 'cipher_group', 'input_group']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(gs)
                    except RuntimeError:
                        pass
        
        for slot_attr in ['mode_slot', 'family_slot', 'cipher_slot']:
            if hasattr(self, slot_attr):
                slot = getattr(self, slot_attr)
                if slot:
                    slot.colors = t
                    slot._style_filled() if slot.is_filled() else slot._style_empty()
                    slot.update()
        
        for card_list in [self.mode_cards, self.family_cards, self.cipher_cards]:
            for card in card_list:
                try:
                    card.update_theme(t)
                except RuntimeError:
                    pass
        
        cb_style = f"""
            QCheckBox {{ color: {t['text']}; font-size: 13px; spacing: 8px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {t['border']}; border-radius: 4px; background: {t['crust']}; }}
            QCheckBox::indicator:checked {{ background: {t['accent']}; border-color: {t['accent']}; }}
        """
        for attr in ['show_pass', 'base64_check', 'salt_check', 'pbkdf2_check']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(cb_style)
                    except RuntimeError:
                        pass
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['password_input', 'confirm_input', 'input_path_input']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(input_style)
                    except RuntimeError:
                        pass
        
        if hasattr(self, 'input_text_edit') and self.input_text_edit:
            self.input_text_edit.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px;font-family:JetBrains Mono,monospace;font-size:13px;}}")
        
        if self.results_metadata:
            self.results_metadata.setStyleSheet(f"color: {t['text_secondary']}; font-size: 12px; font-weight: 600; padding: 4px 0;")
        
        spinbox_style = f"QSpinBox{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}} QSpinBox:hover{{border-color:{t['accent']};}}"
        if hasattr(self, 'iterations_input') and self.iterations_input:
            self.iterations_input.setStyleSheet(spinbox_style)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:10px 20px;font-weight:700;font-size:14px;}} QPushButton:hover{{background-color:{t['surface0']};}} QPushButton:disabled{{opacity:0.5;}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:10px 20px;font-weight:700;font-size:14px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
                elif btn.objectName() == "backButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:transparent;color:{t['text']};border:none;padding:8px 16px;font-weight:600;}} QPushButton:hover{{background-color:transparent;}}")
            except RuntimeError:
                pass
        
        text_style = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        if self.status_output:
            self.status_output.setStyleSheet(text_style)
        if self.results_output:
            self.results_output.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,monospace;font-size:14px;font-weight:600;line-height:1.6;}}")
        if self.req_output:
            self.req_output.setStyleSheet(f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:12px;font-size:12px;}}")
        
        if self.status_progress:
            self.status_progress.setStyleSheet(f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}")
        
        for label in self.findChildren(QLabel):
            try:
                if label.objectName() == "pageTitle":
                    label.setStyleSheet(f"color:{t['text']};font-size:24px;font-weight:700;padding:4px 0;")
            except RuntimeError:
                pass
        
        self._update_file_preview("input")
    
    def refresh_theme(self):
        self._apply_theme()
        self._update_tool_badge()
        self._update_requirements()