# gui/openssl_generate_ec.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QTextCursor, QDrag

import os
import subprocess
import sys
import tempfile
import re


class GenerateECWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str, str)
    
    def __init__(self, curve, passphrase="", private_key_path="", mode="generate"):
        super().__init__()
        self.curve = curve
        self.passphrase = passphrase
        self.private_key_path = private_key_path
        self.mode = mode
        self.private_key = ""
        self.public_key = ""
    
    def run(self):
        try:
            if self.mode == "private":
                self._generate_private()
            elif self.mode == "public":
                self._generate_public_from_private()
            else:
                self._generate_both()
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "", "")
    
    def _generate_private(self):
        try:
            self.progress.emit(f"Generating EC private key using {self.curve} curve...")
            self.progress_value.emit(20)
            
            cmd = ["openssl", "genpkey", "-algorithm", "EC", "-pkeyopt", f"ec_paramgen_curve:{self.curve}"]
            if self.passphrase:
                cmd.extend(["-aes256", "-pass", f"pass:{self.passphrase}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.finished.emit(False, f"Error generating EC private key: {result.stderr}", "", "")
                return
            
            self.progress_value.emit(100)
            self.progress.emit("EC private key generated successfully!")
            
            self.private_key = result.stdout
            result_text = self.private_key
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(self.private_key)
                temp_priv = f.name
            
            try:
                cmd_detail = ["openssl", "pkey", "-in", temp_priv, "-text", "-noout"]
                result_detail = subprocess.run(cmd_detail, capture_output=True, text=True, timeout=30)
                if result_detail.returncode == 0:
                    result_text += f"\n\n--- Key Details ---\n{result_detail.stdout}"
            finally:
                if os.path.exists(temp_priv):
                    try:
                        os.unlink(temp_priv)
                    except:
                        pass
            
            self.finished.emit(True, result_text, self.private_key, "")
            
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "", "")
    
    def _generate_public_from_private(self):
        try:
            self.progress.emit(f"Loading private key from: {self.private_key_path}")
            self.progress_value.emit(20)
            
            if not os.path.exists(self.private_key_path):
                self.finished.emit(False, "Private key file not found", "", "")
                return
            
            with open(self.private_key_path, 'r') as f:
                self.private_key = f.read()
            
            if "-----BEGIN" not in self.private_key:
                self.finished.emit(False, "Invalid private key format", "", "")
                return
            
            self.progress.emit("Extracting public key from private key...")
            self.progress_value.emit(50)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(self.private_key)
                temp_priv = f.name
            
            try:
                cmd_pub = ["openssl", "pkey", "-in", temp_priv, "-pubout"]
                result_pub = subprocess.run(cmd_pub, capture_output=True, text=True, timeout=30)
                
                if result_pub.returncode != 0:
                    self.finished.emit(False, f"Error extracting public key: {result_pub.stderr}", "", "")
                    return
                
                self.progress_value.emit(100)
                self.progress.emit("Public key extracted successfully!")
                
                self.public_key = result_pub.stdout
                result_text = f"{self.private_key}\n\n{self.public_key}"
                
                cmd_detail = ["openssl", "pkey", "-in", temp_priv, "-text", "-noout"]
                result_detail = subprocess.run(cmd_detail, capture_output=True, text=True, timeout=30)
                if result_detail.returncode == 0:
                    result_text += f"\n\n--- Key Details ---\n{result_detail.stdout}"
                
                self.finished.emit(True, result_text, self.private_key, self.public_key)
                
            finally:
                if os.path.exists(temp_priv):
                    try:
                        os.unlink(temp_priv)
                    except:
                        pass
                            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "", "")
    
    def _generate_both(self):
        try:
            self.progress.emit(f"Generating EC key pair using {self.curve} curve...")
            self.progress_value.emit(10)
            
            cmd = ["openssl", "genpkey", "-algorithm", "EC", "-pkeyopt", f"ec_paramgen_curve:{self.curve}"]
            if self.passphrase:
                cmd.extend(["-aes256", "-pass", f"pass:{self.passphrase}"])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.finished.emit(False, f"Error generating EC private key: {result.stderr}", "", "")
                return
            
            self.progress.emit("EC private key generated successfully!")
            self.progress_value.emit(50)
            
            self.private_key = result.stdout
            
            self.progress.emit("Extracting public key...")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(self.private_key)
                temp_priv = f.name
            
            try:
                cmd_pub = ["openssl", "pkey", "-in", temp_priv, "-pubout"]
                result_pub = subprocess.run(cmd_pub, capture_output=True, text=True, timeout=30)
                
                if result_pub.returncode != 0:
                    self.finished.emit(False, f"Error extracting public key: {result_pub.stderr}", "", "")
                    return
                
                self.progress_value.emit(100)
                self.progress.emit("Public key extracted successfully!")
                
                self.public_key = result_pub.stdout
                result_text = f"{self.private_key}\n\n{self.public_key}"
                
                cmd_detail = ["openssl", "pkey", "-in", temp_priv, "-text", "-noout"]
                result_detail = subprocess.run(cmd_detail, capture_output=True, text=True, timeout=30)
                if result_detail.returncode == 0:
                    result_text += f"\n\n--- Key Details ---\n{result_detail.stdout}"
                
                self.finished.emit(True, result_text, self.private_key, self.public_key)
                
            finally:
                if os.path.exists(temp_priv):
                    try:
                        os.unlink(temp_priv)
                    except:
                        pass
                            
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "", "")


class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self.setFixedSize(130, 60)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _build(self, name):
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(self.name_label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        t = self.colors
        if self.name_label:
            self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 14px; font-weight: 600; background: transparent;")
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
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
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self.setFixedSize(160, 60)
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}")
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}")
    
    def is_filled(self):
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        try:
            mode_id, mode_name = data.split(':', 1)
            self.mode_id = int(mode_id)
            self.mode_name = mode_name
            self._style_filled()
            self.update()
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, OpenSSLGenerateECPage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        if self.is_filled():
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 12, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.mode_name)
        else:
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Drop here")
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, OpenSSLGenerateECPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()


class OpenSSLGenerateECPage(QWidget):
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.openssl_ok = self._check_openssl()
        self.curve_cards = []
        self.mode_cards = []
        self.curve = "prime256v1"
        self.mode_id = None
        self.private_key_path = ""
        self.private_key = ""
        self.public_key = ""
        self._init_ui()
        self._apply_theme()
        self.setAcceptDrops(True)
    
    def _check_openssl(self):
        try:
            result = subprocess.run(["openssl", "version"], capture_output=True, timeout=3)
            return result.returncode == 0
        except:
            return False
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and (filepath.endswith('.pem') or filepath.endswith('.key')):
                self.private_key_path = filepath
                self.private_key_input.setText(filepath)
                self._update_key_preview()
                self._update_execute_button()
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
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
        
        title = QLabel("Generate EC Key")
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
        
        layout.addLayout(header)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_requirements_tab(), "Requirements")
        
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _update_tool_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        
        if self.openssl_ok:
            self.tool_badge.setText("OpenSSL Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "openssl.png")
        else:
            self.tool_badge.setText("OpenSSL Missing")
            c = t['error']
            icon_path = os.path.join(icons_dir, "no.png")
        
        self.tool_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'tools_icon'):
            pixmap = QIcon(icon_path).pixmap(32, 32)
            self.tools_icon.setPixmap(pixmap)
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Elliptic Curve
        self.curve_group = QGroupBox("1. Elliptic Curve")
        curve_layout = QVBoxLayout()
        curve_layout.setSpacing(10)
        
        curve_cards_row = QHBoxLayout()
        curve_cards_row.setSpacing(10)
        t = self.theme.current
        
        # Common EC curves
        curves = [
            (1, "prime256v1"),
            (2, "secp384r1"),
            (3, "secp521r1"),
            (4, "secp256k1")
        ]
        
        for mode_id, name in curves:
            card = DraggableModeCard(mode_id, name, t)
            self.curve_cards.append(card)
            curve_cards_row.addWidget(card)
        curve_cards_row.addStretch()
        curve_layout.addLayout(curve_cards_row)
        
        curve_drop_row = QHBoxLayout()
        self.curve_slot = ModeDropSlot(t)
        curve_drop_row.addWidget(self.curve_slot)
        curve_drop_row.addStretch()
        curve_layout.addLayout(curve_drop_row)
        
        self.curve_slot.dropEvent = self._curve_drop_event
        
        self.curve_group.setLayout(curve_layout)
        layout.addWidget(self.curve_group)
        
        # Operation Mode - HIDDEN INITIALLY
        self.mode_group = QGroupBox("2. Operation Mode")
        self.mode_group.setVisible(False)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        for mode_id, name in [(1, "Private Key"), (2, "Public Key"), (3, "Both Keys")]:
            card = DraggableModeCard(mode_id, name, t)
            self.mode_cards.append(card)
            cards_row.addWidget(card)
        cards_row.addStretch()
        mode_layout.addLayout(cards_row)
        
        drop_row = QHBoxLayout()
        self.mode_slot = ModeDropSlot(t)
        drop_row.addWidget(self.mode_slot)
        drop_row.addStretch()
        mode_layout.addLayout(drop_row)
        
        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)
        
        # Options Group (dynamically changes)
        self.options_group = QGroupBox("3. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        # Execute button
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
    
    def _curve_drop_event(self, event):
        data = event.mimeData().text()
        try:
            mode_id, mode_name = data.split(':', 1)
            self.curve_slot.mode_id = int(mode_id)
            self.curve_slot.mode_name = mode_name
            self.curve_slot._style_filled()
            self.curve_slot.update()
            event.acceptProposedAction()
            
            self.curve = mode_name
            self.mode_group.setVisible(True)
            self._update_execute_button()
        except:
            pass
    
    def _on_mode_dropped(self):
        mode_id = self.mode_slot.mode_id
        self.mode_id = mode_id
        
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
        
        if hasattr(self, 'pass_group'):
            delattr(self, 'pass_group')
        if hasattr(self, 'pass_check'):
            delattr(self, 'pass_check')
        if hasattr(self, 'pass_input'):
            delattr(self, 'pass_input')
        if hasattr(self, 'confirm_input'):
            delattr(self, 'confirm_input')
        if hasattr(self, 'private_group'):
            delattr(self, 'private_group')
        if hasattr(self, 'show_pass'):
            delattr(self, 'show_pass')
        
        t = self.theme.current
        
        if mode_id == 1:  # Private Key
            self.options_group.setVisible(True)
            
            self.pass_group = QGroupBox("Password Protection (Optional)")
            pass_layout = QVBoxLayout()
            
            self.pass_check = QCheckBox("Encrypt private key with password")
            self.pass_check.toggled.connect(self._on_pass_toggle)
            pass_layout.addWidget(self.pass_check)
            
            pass_row = QHBoxLayout()
            pass_label = QLabel("Password:")
            self.pass_input = QLineEdit()
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.pass_input.setPlaceholderText("Enter password...")
            self.pass_input.setEnabled(False)
            pass_row.addWidget(pass_label)
            pass_row.addWidget(self.pass_input, 1)
            
            pass_paste = QPushButton("Paste")
            pass_paste.setObjectName("actionButton")
            pass_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            pass_paste.clicked.connect(lambda: self._paste_to(self.pass_input))
            pass_row.addWidget(pass_paste)
            
            pass_clear = QPushButton("Clear")
            pass_clear.setObjectName("dangerButton")
            pass_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            pass_clear.clicked.connect(self.pass_input.clear)
            pass_row.addWidget(pass_clear)
            
            pass_layout.addLayout(pass_row)
            
            self.show_pass = QCheckBox("Show password")
            self.show_pass.stateChanged.connect(self._toggle_password_visibility)
            pass_layout.addWidget(self.show_pass)
            
            confirm_row = QHBoxLayout()
            confirm_label = QLabel("Confirm:")
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_input.setPlaceholderText("Confirm password...")
            self.confirm_input.setEnabled(False)
            confirm_row.addWidget(confirm_label)
            confirm_row.addWidget(self.confirm_input, 1)
            
            confirm_paste = QPushButton("Paste")
            confirm_paste.setObjectName("actionButton")
            confirm_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_paste.clicked.connect(lambda: self._paste_to(self.confirm_input))
            confirm_row.addWidget(confirm_paste)
            
            confirm_clear = QPushButton("Clear")
            confirm_clear.setObjectName("dangerButton")
            confirm_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_clear.clicked.connect(self.confirm_input.clear)
            confirm_row.addWidget(confirm_clear)
            
            pass_layout.addLayout(confirm_row)
            
            self.pass_group.setLayout(pass_layout)
            self.options_layout.addWidget(self.pass_group)
            
            self.execute_btn.setText("Generate EC Private Key")
            
        elif mode_id == 2:  # Public Key
            self.options_group.setVisible(True)
            
            self.private_group = QGroupBox("Private Key File")
            private_layout = QVBoxLayout()
            
            self.private_preview = QLabel()
            self.private_preview.setFixedHeight(100)
            self.private_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.private_preview.setText("Drag & drop a .pem or .key file here\nor click Browse to select")
            private_layout.addWidget(self.private_preview)
            
            private_row = QHBoxLayout()
            self.private_key_input = QLineEdit()
            self.private_key_input.setReadOnly(True)
            self.private_key_input.setPlaceholderText("No private key selected...")
            
            browse_btn = QPushButton("Browse")
            browse_btn.setObjectName("actionButton")
            browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            browse_btn.clicked.connect(self._browse_private_key)
            
            paste_btn = QPushButton("Paste")
            paste_btn.setObjectName("actionButton")
            paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            paste_btn.clicked.connect(self._paste_private_key)
            
            clear_btn = QPushButton("Clear")
            clear_btn.setObjectName("dangerButton")
            clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_btn.clicked.connect(self._clear_private_key)
            
            private_row.addWidget(self.private_key_input, 1)
            private_row.addWidget(browse_btn)
            private_row.addWidget(paste_btn)
            private_row.addWidget(clear_btn)
            private_layout.addLayout(private_row)
            
            self.private_group.setLayout(private_layout)
            self.options_layout.addWidget(self.private_group)
            
            self.execute_btn.setText("Generate EC Public Key")
            
        elif mode_id == 3:  # Both Keys
            self.options_group.setVisible(True)
            
            self.pass_group = QGroupBox("Password Protection (Optional)")
            pass_layout = QVBoxLayout()
            
            self.pass_check = QCheckBox("Encrypt private key with password")
            self.pass_check.toggled.connect(self._on_pass_toggle)
            pass_layout.addWidget(self.pass_check)
            
            pass_row = QHBoxLayout()
            pass_label = QLabel("Password:")
            self.pass_input = QLineEdit()
            self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.pass_input.setPlaceholderText("Enter password...")
            self.pass_input.setEnabled(False)
            pass_row.addWidget(pass_label)
            pass_row.addWidget(self.pass_input, 1)
            
            pass_paste = QPushButton("Paste")
            pass_paste.setObjectName("actionButton")
            pass_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            pass_paste.clicked.connect(lambda: self._paste_to(self.pass_input))
            pass_row.addWidget(pass_paste)
            
            pass_clear = QPushButton("Clear")
            pass_clear.setObjectName("dangerButton")
            pass_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            pass_clear.clicked.connect(self.pass_input.clear)
            pass_row.addWidget(pass_clear)
            
            pass_layout.addLayout(pass_row)
            
            self.show_pass = QCheckBox("Show password")
            self.show_pass.stateChanged.connect(self._toggle_password_visibility)
            pass_layout.addWidget(self.show_pass)
            
            confirm_row = QHBoxLayout()
            confirm_label = QLabel("Confirm:")
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_input.setPlaceholderText("Confirm password...")
            self.confirm_input.setEnabled(False)
            confirm_row.addWidget(confirm_label)
            confirm_row.addWidget(self.confirm_input, 1)
            
            confirm_paste = QPushButton("Paste")
            confirm_paste.setObjectName("actionButton")
            confirm_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_paste.clicked.connect(lambda: self._paste_to(self.confirm_input))
            confirm_row.addWidget(confirm_paste)
            
            confirm_clear = QPushButton("Clear")
            confirm_clear.setObjectName("dangerButton")
            confirm_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            confirm_clear.clicked.connect(self.confirm_input.clear)
            confirm_row.addWidget(confirm_clear)
            
            pass_layout.addLayout(confirm_row)
            
            self.pass_group.setLayout(pass_layout)
            self.options_layout.addWidget(self.pass_group)
            
            self.execute_btn.setText("Generate EC Key Pair")
        
        self._update_execute_button()
        self._apply_theme()
    
    def _toggle_password_visibility(self, state):
        if hasattr(self, 'pass_input') and hasattr(self, 'confirm_input'):
            echo_mode = QLineEdit.EchoMode.Normal if state == Qt.CheckState.Checked.value else QLineEdit.EchoMode.Password
            self.pass_input.setEchoMode(echo_mode)
            self.confirm_input.setEchoMode(echo_mode)
    
    def _on_mode_cleared(self):
        self.mode_id = None
        
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
        
        if hasattr(self, 'pass_group'):
            delattr(self, 'pass_group')
        if hasattr(self, 'pass_check'):
            delattr(self, 'pass_check')
        if hasattr(self, 'pass_input'):
            delattr(self, 'pass_input')
        if hasattr(self, 'confirm_input'):
            delattr(self, 'confirm_input')
        if hasattr(self, 'private_group'):
            delattr(self, 'private_group')
        if hasattr(self, 'show_pass'):
            delattr(self, 'show_pass')
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _browse_private_key(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "Select Private Key", "",
            "PEM Files (*.pem *.key);;All Files (*)"
        )
        if fp:
            self.private_key_path = fp
            self.private_key_input.setText(fp)
            self._update_key_preview()
            self._update_execute_button()
    
    def _paste_private_key(self):
        clipboard = QApplication.clipboard().text()
        if clipboard and "-----BEGIN" in clipboard:
            self.private_key_input.setText("Pasted from clipboard")
            self.private_key_path = "clipboard"
            self._update_key_preview()
            self._update_execute_button()
    
    def _clear_private_key(self):
        self.private_key_path = ""
        self.private_key_input.clear()
        self._update_key_preview()
        self._update_execute_button()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setText(clipboard)
    
    def _update_key_preview(self):
        t = self.theme.current
        if hasattr(self, 'private_preview'):
            if self.private_key_path:
                name = os.path.basename(self.private_key_path) if self.private_key_path != "clipboard" else "Pasted from clipboard"
                self.private_preview.setText(f"{name}")
                self.private_preview.setStyleSheet(f"""
                    border: 2px dashed {t['border']};
                    border-radius: 8px;
                    background: transparent;
                    color: {t['text']};
                    font-size: 13px;
                    font-weight: 600;
                    padding: 10px;
                """)
            else:
                self.private_preview.setText("Drag & drop a .pem or .key file here\nor click Browse to select")
                self.private_preview.setStyleSheet(f"""
                    border: 2px dashed {t['border']};
                    border-radius: 8px;
                    background: transparent;
                    color: {t['text_tertiary']};
                    font-size: 13px;
                    padding: 10px;
                """)
    
    def _update_execute_button(self):
        curve_filled = self.curve_slot.is_filled()
        mode_filled = self.mode_slot.is_filled()
        
        if not curve_filled or not mode_filled:
            self.execute_btn.setEnabled(False)
            return
        
        if self.mode_id == 2 and not self.private_key_path:
            self.execute_btn.setEnabled(False)
            return
        
        self.execute_btn.setEnabled(True)
    
    def _on_pass_toggle(self, checked):
        if hasattr(self, 'pass_input') and hasattr(self, 'confirm_input'):
            self.pass_input.setEnabled(checked)
            self.confirm_input.setEnabled(checked)
            if not checked:
                self.pass_input.clear()
                self.confirm_input.clear()
    
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
        
        results_header = QHBoxLayout()
        results_label = QLabel("Result:")
        
        self.export_private_btn = QPushButton("Export Private Key")
        self.export_private_btn.setObjectName("actionButton")
        self.export_private_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_private_btn.clicked.connect(lambda: self._export_key("private"))
        self.export_private_btn.hide()
        
        self.export_public_btn = QPushButton("Export Public Key")
        self.export_public_btn.setObjectName("actionButton")
        self.export_public_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_public_btn.clicked.connect(lambda: self._export_key("public"))
        self.export_public_btn.hide()
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(self.export_private_btn)
        results_header.addWidget(self.export_public_btn)
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
        t = self.theme.current
        html = ""
        c = t['success'] if self.openssl_ok else t['error']
        html += f"<h3 style='color:{c};'>OpenSSL</h3>"
        html += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install openssl</p>"
        self.req_output.setHtml(html)
        self.install_btn.setEnabled(not self.openssl_ok)
        self.install_btn.setText("OpenSSL Installed" if self.openssl_ok else "Install Requirements")
    
    def _install_openssl(self):
        if QMessageBox.question(
            self, "Install OpenSSL",
            "Install OpenSSL?\n\nsudo apt install -y openssl",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        self.install_btn.setEnabled(False)
        self.install_btn.setText("Installing...")
        self.install_status.setText("Running: sudo apt install -y openssl")
        
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "openssl"], capture_output=True, text=True, timeout=120)
            self.openssl_ok = self._check_openssl()
            self.install_status.setText("Done!" if self.openssl_ok else "Failed")
        except Exception as e:
            self.install_status.setText(f"Error: {e}")
        
        self._update_tool_badge()
        self._update_requirements()
    
    def _execute(self):
        if not self.curve_slot.is_filled():
            QMessageBox.warning(self, "No Curve Selected", "Please select an elliptic curve")
            return
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Please select an operation mode")
            return
        
        mode_id = self.mode_slot.mode_id
        curve = self.curve
        passphrase = ""
        
        if mode_id == 2 and not self.private_key_path:
            QMessageBox.warning(self, "Missing File", "Please select a private key file")
            return
        
        if hasattr(self, 'pass_check') and self.pass_check.isChecked():
            password = self.pass_input.text()
            confirm = self.confirm_input.text()
            if not password or not confirm:
                QMessageBox.warning(self, "Missing Password", "Please enter and confirm your password.")
                return
            if password != confirm:
                QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                return
            passphrase = password
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        
        self.export_private_btn.hide()
        self.export_public_btn.hide()
        
        if mode_id == 1:
            self.worker = GenerateECWorker(curve, passphrase, mode="private")
        elif mode_id == 2:
            self.worker = GenerateECWorker("", "", private_key_path=self.private_key_path, mode="public")
        else:
            self.worker = GenerateECWorker(curve, passphrase, mode="both")
        
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, result, private_key, public_key):
        self.execute_btn.setEnabled(True)
        if success:
            self.private_key = private_key
            self.public_key = public_key
            
            self.status_output.append("SUCCESS!")
            self.status_progress.setValue(100)
            self.results_output.setText(result)
            
            if private_key:
                self.export_private_btn.show()
            if public_key:
                self.export_public_btn.show()
            
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR:\n{result}")
            self.status_progress.setValue(100)
            QMessageBox.critical(self, "Operation Failed", result)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied to clipboard!")
    
    def _export_key(self, key_type):
        if key_type == "private" and self.private_key:
            fp, _ = QFileDialog.getSaveFileName(
                self, "Export Private Key", "ec_private_key.pem",
                "PEM Files (*.pem);;All Files (*)"
            )
            if fp:
                try:
                    with open(fp, 'w') as f:
                        f.write(self.private_key)
                    QMessageBox.information(self, "Exported", f"Private key saved to:\n{fp}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
        elif key_type == "public" and self.public_key:
            fp, _ = QFileDialog.getSaveFileName(
                self, "Export Public Key", "ec_public_key.pem",
                "PEM Files (*.pem *.pub);;All Files (*)"
            )
            if fp:
                try:
                    with open(fp, 'w') as f:
                        f.write(self.public_key)
                    QMessageBox.information(self, "Exported", f"Public key saved to:\n{fp}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                background-color: {t['base']};
            }}
            QTabBar::tab {{
                background-color: {t['crust']};
                color: {t['text_secondary']};
                border: 1px solid {t['border']};
                padding: 10px 28px;
                margin-right: 2px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {t['base']};
                color: {t['text']};
                border-bottom-color: transparent;
            }}
        """)
        
        gs = f"""
            QGroupBox {{
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                margin-top: 14px;
                padding: 20px 16px 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QGroupBox::title {{
                left: 14px;
                padding: 0 8px;
                color: {t['text']};
            }}
        """
        for attr in ['curve_group', 'mode_group', 'options_group', 'req_group']:
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'curve_slot'):
            self.curve_slot.colors = t
            if self.curve_slot.is_filled():
                self.curve_slot._style_filled()
            else:
                self.curve_slot._style_empty()
            self.curve_slot.update()
        
        if hasattr(self, 'mode_slot'):
            self.mode_slot.colors = t
            if self.mode_slot.is_filled():
                self.mode_slot._style_filled()
            else:
                self.mode_slot._style_empty()
            self.mode_slot.update()
        
        for card in self.curve_cards + self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        if hasattr(self, 'pass_check'):
            self.pass_check.setStyleSheet(f"""
                QCheckBox {{
                    color: {t['text']};
                    font-size: 13px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {t['border']};
                    border-radius: 4px;
                    background: {t['crust']};
                }}
                QCheckBox::indicator:checked {{
                    background: {t['accent']};
                    border-color: {t['accent']};
                }}
            """)
        
        if hasattr(self, 'show_pass'):
            self.show_pass.setStyleSheet(f"""
                QCheckBox {{
                    color: {t['text']};
                    font-size: 13px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {t['border']};
                    border-radius: 4px;
                    background: {t['crust']};
                }}
                QCheckBox::indicator:checked {{
                    background: {t['accent']};
                    border-color: {t['accent']};
                }}
            """)
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['private_key_input', 'pass_input', 'confirm_input']:
            if hasattr(self, attr):
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['text']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: 10px 20px;
                            font-weight: 700;
                            font-size: 14px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                        QPushButton:disabled {{
                            opacity: 0.5;
                        }}
                    """)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['error']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: 10px 20px;
                            font-weight: 700;
                            font-size: 14px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                    """)
                elif btn.objectName() == "backButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: transparent;
                            color: {t['text']};
                            border: none;
                            padding: 8px 16px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            background-color: transparent;
                        }}
                    """)
            except RuntimeError:
                pass
        
        text_style = f"""
            QTextEdit {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 10px;
                font-family: JetBrains Mono, monospace;
                font-size: 13px;
            }}
        """
        if hasattr(self, 'status_output'):
            self.status_output.setStyleSheet(text_style)
        if hasattr(self, 'results_output'):
            self.results_output.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {t['crust']};
                    color: {t['success']};
                    border: 1px solid {t['border']};
                    border-radius: 6px;
                    padding: 16px;
                    font-family: JetBrains Mono, monospace;
                    font-size: 14px;
                    font-weight: 600;
                    line-height: 1.6;
                }}
            """)
        if hasattr(self, 'req_output'):
            self.req_output.setStyleSheet(
                f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:12px;font-size:12px;}}"
            )
        
        if hasattr(self, 'status_progress'):
            self.status_progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {t['surface0']};
                    border: none;
                    border-radius: 4px;
                    height: 14px;
                    text-align: center;
                    font-size: 10px;
                    font-weight: 600;
                }}
                QProgressBar::chunk {{
                    background-color: {t['success']};
                    border-radius: 4px;
                }}
            """)
        
        for label in self.findChildren(QLabel):
            try:
                if label.objectName() == "pageTitle":
                    label.setStyleSheet(f"""
                        color: {t['text']};
                        font-size: 24px;
                        font-weight: 700;
                        padding: 4px 0;
                    """)
            except RuntimeError:
                pass
        
        self._update_key_preview()
    
    def refresh_theme(self):
        self._apply_theme()
        self._update_tool_badge()
        self._update_requirements()