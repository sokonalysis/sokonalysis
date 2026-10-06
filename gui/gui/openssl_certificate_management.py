# gui/openssl_certificate_management.py
"""
OpenSSL Certificate Management Module
Provides GUI interface for CSR generation, self-signed certificates,
CSR signing, and certificate viewing using OpenSSL.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSpinBox, QFormLayout, QCheckBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QDrag

import os
import subprocess
import sys
import tempfile
from datetime import datetime
from gui.layout_manager import layout_manager


# ============================================================================
# Certificate Worker Thread
# ============================================================================

class CertificateWorker(QThread):
    """Background thread for executing OpenSSL operations."""
    
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str)
    
    def __init__(self, mode, key_path="", cert_path="", csr_path="", 
                 subject="", days=365, key_size=2048, passphrase="",
                 existing_key_path="", use_existing_key=False):
        super().__init__()
        self.mode = mode
        self.key_path = key_path
        self.cert_path = cert_path
        self.csr_path = csr_path
        self.subject = subject
        self.days = days
        self.key_size = key_size
        self.passphrase = passphrase
        self.existing_key_path = existing_key_path
        self.use_existing_key = use_existing_key
        self.result = ""
        self.private_key = ""
        self.csr_data = ""
        self.certificate = ""
    
    def run(self):
        try:
            operations = {
                "generate_csr": self._generate_csr,
                "generate_self_signed": self._generate_self_signed,
                "sign_csr": self._sign_csr,
                "view_cert": self._view_cert,
            }
            if self.mode in operations:
                operations[self.mode]()
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")
    
    def _get_private_key(self):
        if self.use_existing_key and self.existing_key_path:
            if self.existing_key_path == "clipboard":
                return QApplication.clipboard().text()
            with open(self.existing_key_path, 'r') as f:
                return f.read()
        
        key_cmd = [
            "openssl", "genpkey", "-algorithm", "RSA",
            "-pkeyopt", f"rsa_keygen_bits:{self.key_size}"
        ]
        if self.passphrase:
            key_cmd.extend(["-aes256", "-pass", f"pass:{self.passphrase}"])
        
        result = subprocess.run(key_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            self.finished.emit(False, f"Error generating private key: {result.stderr}", "")
            return None
        return result.stdout
    
    def _generate_csr(self):
        try:
            self.progress.emit("Generating CSR...")
            self.progress_value.emit(20)
            
            private_key = self._get_private_key()
            if private_key is None:
                return
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(private_key)
                temp_key = f.name
            
            try:
                csr_cmd = ["openssl", "req", "-new", "-key", temp_key, "-subj", self.subject]
                if self.passphrase:
                    csr_cmd.extend(["-passin", f"pass:{self.passphrase}"])
                
                result = subprocess.run(csr_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self.finished.emit(False, f"Error generating CSR: {result.stderr}", "")
                    return
                
                csr = result.stdout
                self.private_key = private_key if not self.use_existing_key else ""
                self.csr_data = csr
                self.progress_value.emit(100)
                self.progress.emit("CSR generated successfully!")
                
                if self.use_existing_key:
                    result_text = f"# CSR (generated from existing key)\n{csr}"
                else:
                    result_text = f"# Private Key\n{private_key}\n\n# Certificate Signing Request (CSR)\n{csr}"
                
                self.result = result_text
                self.finished.emit(True, result_text, csr)
            finally:
                if os.path.exists(temp_key):
                    os.unlink(temp_key)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")
    
    def _generate_self_signed(self):
        try:
            self.progress.emit("Generating self-signed certificate...")
            self.progress_value.emit(20)
            
            private_key = self._get_private_key()
            if private_key is None:
                return
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(private_key)
                temp_key = f.name
            
            try:
                cert_cmd = [
                    "openssl", "req", "-new", "-x509",
                    "-key", temp_key, "-subj", self.subject,
                    "-days", str(self.days)
                ]
                if self.passphrase:
                    cert_cmd.extend(["-passin", f"pass:{self.passphrase}"])
                
                result = subprocess.run(cert_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    self.finished.emit(False, f"Error generating certificate: {result.stderr}", "")
                    return
                
                certificate = result.stdout
                self.private_key = private_key if not self.use_existing_key else ""
                self.certificate = certificate
                self.progress_value.emit(100)
                self.progress.emit("Self-signed certificate generated successfully!")
                
                if self.use_existing_key:
                    result_text = f"# Self-Signed Certificate (using existing key)\n{certificate}"
                else:
                    result_text = f"# Private Key\n{private_key}\n\n# Self-Signed Certificate\n{certificate}"
                
                self.result = result_text
                self.finished.emit(True, result_text, certificate)
            finally:
                if os.path.exists(temp_key):
                    os.unlink(temp_key)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")
    
    def _sign_csr(self):
        try:
            self.progress.emit("Signing CSR with CA certificate...")
            self.progress_value.emit(20)
            
            if self.csr_path == "clipboard":
                csr_content = QApplication.clipboard().text()
            elif os.path.exists(self.csr_path):
                with open(self.csr_path, 'r') as f:
                    csr_content = f.read()
            else:
                self.finished.emit(False, "CSR file not found", "")
                return
            
            key_cmd = ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048"]
            result_key = subprocess.run(key_cmd, capture_output=True, text=True, timeout=60)
            if result_key.returncode != 0:
                self.finished.emit(False, f"Error generating CA key: {result_key.stderr}", "")
                return
            ca_key = result_key.stdout
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(ca_key)
                temp_ca_key = f.name
            
            try:
                cmd_ca = [
                    "openssl", "req", "-new", "-x509",
                    "-key", temp_ca_key, "-subj", "/CN=CA Certificate",
                    "-days", "365"
                ]
                result_ca = subprocess.run(cmd_ca, capture_output=True, text=True, timeout=30)
                if result_ca.returncode != 0:
                    self.finished.emit(False, f"Error generating CA certificate: {result_ca.stderr}", "")
                    return
                ca_cert = result_ca.stdout
                
                temp_files = {}
                for suffix, content in [
                    ('.csr', csr_content),
                    ('.pem', ca_cert),
                    ('.crt', ''),
                    ('.conf', "[req]\ndefault_bits = 2048\ndistinguished_name = req_distinguished_name\n[req_distinguished_name]\n[v3_req]\nbasicConstraints = CA:FALSE\nkeyUsage = nonRepudiation, digitalSignature, keyEncipherment\n")
                ]:
                    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                        f.write(content)
                        temp_files[suffix] = f.name
                
                try:
                    cmd_sign = [
                        "openssl", "x509", "-req",
                        "-in", temp_files['.csr'],
                        "-CA", temp_files['.pem'],
                        "-CAkey", temp_ca_key,
                        "-CAcreateserial",
                        "-out", temp_files['.crt'],
                        "-days", str(self.days),
                        "-extensions", "v3_req",
                        "-extfile", temp_files['.conf']
                    ]
                    
                    result_sign = subprocess.run(cmd_sign, capture_output=True, text=True, timeout=30)
                    if result_sign.returncode != 0:
                        self.finished.emit(False, f"Error signing CSR: {result_sign.stderr}", "")
                        return
                    
                    with open(temp_files['.crt'], 'r') as f:
                        certificate = f.read()
                    
                    self.certificate = certificate
                    self.progress_value.emit(100)
                    self.progress.emit("CSR signed successfully!")
                    
                    result_text = f"# CA Certificate\n{ca_cert}\n\n# Signed Certificate\n{certificate}"
                    self.finished.emit(True, result_text, certificate)
                finally:
                    for filepath in temp_files.values():
                        if os.path.exists(filepath):
                            os.unlink(filepath)
            finally:
                if os.path.exists(temp_ca_key):
                    os.unlink(temp_ca_key)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")
    
    def _view_cert(self):
        """Display certificate information. Auto-detects CSR / cert / key."""
        try:
            self.progress.emit("Analyzing file...")
            self.progress_value.emit(20)
            
            temp_cert_file = None
            if self.cert_path == "clipboard":
                cert_content = QApplication.clipboard().text()
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                    f.write(cert_content)
                    temp_cert_file = f.name
                cert_path_to_use = temp_cert_file
            elif not os.path.exists(self.cert_path):
                self.finished.emit(False, "File not found", "")
                return
            else:
                cert_path_to_use = self.cert_path
            
            try:
                with open(cert_path_to_use, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if "-----BEGIN" not in content:
                    self.finished.emit(False, "File does not appear to be PEM-encoded", "")
                    return
                
                is_cert = (
                    "-----BEGIN CERTIFICATE-----" in content or
                    "-----BEGIN TRUSTED CERTIFICATE-----" in content or
                    "-----BEGIN X509 CERTIFICATE-----" in content
                )
                is_csr = (
                    "-----BEGIN CERTIFICATE REQUEST-----" in content or
                    "-----BEGIN NEW CERTIFICATE REQUEST-----" in content
                )
                is_key = "PRIVATE KEY" in content
                
                if is_cert:
                    primary_cmd = ["openssl", "x509", "-in", cert_path_to_use, "-text", "-noout"]
                    type_name = "X.509 Certificate"
                elif is_csr:
                    primary_cmd = ["openssl", "req", "-in", cert_path_to_use, "-text", "-noout", "-verify"]
                    type_name = "Certificate Signing Request (CSR)"
                elif is_key:
                    primary_cmd = ["openssl", "pkey", "-in", cert_path_to_use, "-text", "-noout"]
                    type_name = "Private Key"
                else:
                    self.finished.emit(False, "Unknown PEM type", "")
                    return
                
                self.progress.emit(f"Detected: {type_name}")
                self.progress_value.emit(40)
                
                result = subprocess.run(primary_cmd, capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    self.finished.emit(False, f"Error parsing {type_name}: {result.stderr}", "")
                    return
                
                details = result.stdout.strip()
                extra_lines = []
                
                if is_cert:
                    for key, cmd in [
                        ("Subject", ["openssl", "x509", "-in", cert_path_to_use, "-noout", "-subject"]),
                        ("Issuer", ["openssl", "x509", "-in", cert_path_to_use, "-noout", "-issuer"]),
                        ("Validity", ["openssl", "x509", "-in", cert_path_to_use, "-noout", "-dates"]),
                        ("Serial", ["openssl", "x509", "-in", cert_path_to_use, "-noout", "-serial"]),
                        ("Fingerprint", ["openssl", "x509", "-in", cert_path_to_use, "-noout", "-fingerprint"]),
                    ]:
                        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if r.stdout.strip():
                            extra_lines.append(f"{key}: {r.stdout.strip()}")
                
                elif is_csr:
                    for key, cmd in [
                        ("Subject", ["openssl", "req", "-in", cert_path_to_use, "-noout", "-subject"]),
                        ("Public Key", ["openssl", "req", "-in", cert_path_to_use, "-noout", "-pubkey"]),
                        ("Signature", ["openssl", "req", "-in", cert_path_to_use, "-noout", "-verify"]),
                    ]:
                        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if r.stdout.strip():
                            extra_lines.append(f"{key}: {r.stdout.strip()}")
                        elif r.stderr.strip():
                            extra_lines.append(f"{key}: {r.stderr.strip()}")
                
                elif is_key:
                    r = subprocess.run(
                        ["openssl", "pkey", "-in", cert_path_to_use, "-noout", "-text"],
                        capture_output=True, text=True, timeout=5
                    )
                    if r.stdout.strip():
                        extra_lines.append(r.stdout.strip())
                
                self.progress_value.emit(100)
                self.progress.emit(f"Displayed {type_name} information!")
                
                summary = "\n".join(extra_lines) if extra_lines else ""
                if summary:
                    result_text = f"{type_name}\n\n{summary}\n\n{details}"
                else:
                    result_text = f"{type_name}\n\n{details}"
                
                self.finished.emit(True, result_text.strip(), "")
            finally:
                if temp_cert_file and os.path.exists(temp_cert_file):
                    os.unlink(temp_cert_file)
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out", "")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")


# ============================================================================
# Drag and Drop Components
# ============================================================================

class DropForwarder(QLabel):
    """A QLabel that forwards file drops to its parent page."""
    
    def __init__(self, page, file_type, parent=None):
        super().__init__(parent)
        self.page = page
        self.file_type = file_type
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and os.path.isfile(filepath):
                self.page._handle_dropped_file(filepath, self.file_type)
                event.acceptProposedAction()
                return


class DraggableCard(QFrame):
    """Base class for draggable cards with scaled sizing."""
    
    def __init__(self, theme_colors, base_width, base_height, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self._base_w = base_width
        self._base_h = base_height
        self._apply_scaled_size()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(int(self._base_w * 0.7), int(self._base_w * scale))
        h = max(int(self._base_h * 0.7), int(self._base_h * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(40 * scale), h + int(30 * scale))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    
    def _clear_layout(self):
        if self.layout():
            QWidget().setLayout(self.layout())
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def _start_drag(self, mime_text):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(mime_text)
        drag.setMimeData(mime)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.exec(Qt.DropAction.CopyAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)


class DraggableModeCard(DraggableCard):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        self.mode_id = mode_id
        self.mode_name = name
        super().__init__(theme_colors, 220, 90, parent)
        self._build(name)
    
    def _build(self, name):
        self._clear_layout()
        self._apply_scaled_size()
        t = self.colors
        scale = layout_manager.font_scale()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            int(15 * scale), int(12 * scale),
            int(15 * scale), int(12 * scale)
        )
        layout.setSpacing(int(6 * scale))
        
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(15 * scale))}px; "
            f"font-weight: 600; background: transparent; padding: 2px;"
        )
        layout.addWidget(label)
        
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:12px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        super().update_theme(theme_colors)
        self._build(self.mode_name)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._start_drag(f"mode:{self.mode_id}:{self.mode_name}")


class DraggableKeySizeCard(DraggableCard):
    def __init__(self, key_size, theme_colors, parent=None):
        self.key_size = key_size
        super().__init__(theme_colors, 110, 50, parent)
        self._build()
    
    def _build(self):
        self._clear_layout()
        self._apply_scaled_size()
        t = self.colors
        scale = layout_manager.font_scale()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            int(8 * scale), int(6 * scale),
            int(8 * scale), int(6 * scale)
        )
        
        label = QLabel(f"{self.key_size} bits")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(14 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        layout.addWidget(label)
        
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        super().update_theme(theme_colors)
        self._build()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._start_drag(f"keysize:{self.key_size}")


class DraggableKeySourceCard(DraggableCard):
    def __init__(self, source_id, name, theme_colors, parent=None):
        self.source_id = source_id
        self.source_name = name
        super().__init__(theme_colors, 220, 80, parent)
        self._build(name)
    
    def _build(self, name):
        self._clear_layout()
        self._apply_scaled_size()
        t = self.colors
        scale = layout_manager.font_scale()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            int(15 * scale), int(12 * scale),
            int(15 * scale), int(12 * scale)
        )
        layout.setSpacing(int(6 * scale))
        
        label = QLabel(name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(14 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        layout.addWidget(label)
        
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:10px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        super().update_theme(theme_colors)
        self._build(self.source_name)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._start_drag(f"keysource:{self.source_id}:{self.source_name}")


class DropSlot(QFrame):
    """Generic drop target slot — filled state gets pale accent tint (matches stego page)."""
    
    def __init__(self, theme_colors, accept_type, default_text, base_size=None, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.accept_type = accept_type
        self.default_text = default_text
        self.value = None
        self.display_text = ""
        
        if base_size:
            self._base_w, self._base_h = base_size
        else:
            self._base_w, self._base_h = 240, 90
        
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        font_px = max(9, int(12 * scale))
        text_w = int(len(self.default_text) * font_px * 0.65) + int(60 * scale)
        w = max(self._base_w, text_w)
        h = max(int(self._base_h * 0.7), int(self._base_h * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(160 * scale), h + int(40 * scale))
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};"
            f"border:3px dashed {t['border']};border-radius:12px;}}"
        )
    
    def _style_filled(self):
        # Pale accent tint — matches the stego page "No Password" filled slot
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['accent']}15;"
            f"border:2px solid {t['accent']}88;border-radius:12px;}}"
        )
    
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
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()
    
    def _notify_parent(self, action):
        p = self.parent()
        while p is not None:
            if isinstance(p, OpenSSLCertificateManagementPage):
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
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont(
                "JetBrains Mono, Consolas, monospace",
                max(11, int(14 * scale)), QFont.Weight.Bold
            ))
            text = self.display_text
        else:
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont(
                "JetBrains Mono, Consolas, monospace",
                max(9, int(12 * scale))
            ))
            text = self.default_text
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = painter.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            self._notify_parent("cleared")


# ============================================================================
# Main Certificate Management Page
# ============================================================================

class OpenSSLCertificateManagementPage(QWidget):
    """
    Main page for OpenSSL certificate management operations.
    """
    
    PLACEHOLDERS = {
        'cn': 'kmu.ac.zm',
        'o': 'Kapasa Makasa University',
        'ou': 'ICT Department',
        'l': 'Chinsali',
        'st': 'MU',
        'c': 'ZM',
        'email': 'sokonalysis@kmu.ac.zm'
    }
    
    KEY_SIZES = [1024, 2048, 3072, 4096, 8192]
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        
        self.worker = None
        self.openssl_ok = self._check_openssl()
        self.mode_id = None
        self.csr_path = ""
        self.cert_path = ""
        self.existing_key_path = ""
        self.selected_key_size = 2048
        self.selected_key_source = "new"
        
        self.mode_cards = []
        self.key_size_cards = []
        self.key_source_cards = []
        
        self.icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        
        self._init_widget_refs()
        self._init_ui()
        self._apply_theme()
        self.setAcceptDrops(True)
    
    def _init_widget_refs(self):
        self.key_size_slot = None
        self.key_source_slot = None
        self.days_input = None
        self.pass_group = None
        self.pass_check = None
        self.pass_input = None
        self.confirm_input = None
        self.show_pass = None
        self.csr_group = None
        self.cert_group = None
        self.csr_preview = None
        self.cert_preview = None
        self.csr_input = None
        self.cert_input = None
        self.mode_group = None
        self.options_group = None
        self.req_group = None
        self.mode_slot = None
        self.execute_btn = None
        self.export_btn = None
        self.export_private_btn = None
        self.export_csr_btn = None
        self.export_cert_btn = None
        self.status_output = None
        self.status_progress = None
        self.results_output = None
        self.req_output = None
        self.install_btn = None
        self.install_status = None
        self.tabs = None
        self.tools_icon = None
        self.tool_badge = None
        self.cn_input = None
        self.o_input = None
        self.ou_input = None
        self.l_input = None
        self.st_input = None
        self.c_input = None
        self.email_input = None
        self.key_size_group = None
        self.existing_key_group = None
        self.existing_key_preview = None
        self.existing_key_input = None
    
    def _check_openssl(self):
        try:
            result = subprocess.run(["openssl", "version"], capture_output=True, timeout=3)
            return result.returncode == 0
        except Exception:
            return False
    
    def _build_subject_from_fields(self):
        field_map = {
            'cn_input': 'CN',
            'o_input': 'O',
            'ou_input': 'OU',
            'l_input': 'L',
            'st_input': 'ST',
            'c_input': 'C',
            'email_input': 'emailAddress'
        }
        
        parts = []
        for attr, prefix in field_map.items():
            if hasattr(self, attr):
                widget = getattr(self, attr)
                if widget and widget.text().strip():
                    parts.append(f"/{prefix}={widget.text().strip()}")
        
        return "".join(parts) if parts else ""
    
    # ------------------------------------------------------------------------
    # File type detection
    # ------------------------------------------------------------------------
    def _is_valid_certificate_file(self, filepath):
        if filepath == "clipboard":
            content = QApplication.clipboard().text()
            return (
                "-----BEGIN CERTIFICATE-----" in content or
                "-----BEGIN TRUSTED CERTIFICATE-----" in content or
                "-----BEGIN X509 CERTIFICATE-----" in content
            )
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for header in [
                "-----BEGIN CERTIFICATE-----",
                "-----BEGIN TRUSTED CERTIFICATE-----",
                "-----BEGIN X509 CERTIFICATE-----",
                "-----BEGIN PKCS7-----",
            ]:
                if header in content:
                    return True
            
            result = subprocess.run(
                ["openssl", "x509", "-in", filepath, "-noout"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return True
            
            try:
                result = subprocess.run(
                    ["openssl", "x509", "-inform", "DER", "-in", filepath, "-noout"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False
    
    def _is_valid_key_file(self, filepath):
        if filepath == "clipboard":
            content = QApplication.clipboard().text()
            return "-----BEGIN" in content and "PRIVATE KEY" in content
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return "-----BEGIN" in content and "PRIVATE KEY" in content
        except Exception:
            return False
    
    def _is_csr_file(self, filepath):
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for header in [
                "-----BEGIN CERTIFICATE REQUEST-----",
                "-----BEGIN NEW CERTIFICATE REQUEST-----",
                "-----BEGIN PKCS10-----",
            ]:
                if header in content:
                    return True
            
            try:
                result = subprocess.run(
                    ["openssl", "req", "-in", filepath, "-noout", "-verify"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
            
            try:
                result = subprocess.run(
                    ["openssl", "req", "-in", filepath, "-noout"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False
    
    # ------------------------------------------------------------------------
    # Central drop handler
    # ------------------------------------------------------------------------
    def _handle_dropped_file(self, filepath, file_type):
        if not filepath or not os.path.isfile(filepath):
            return
        
        if file_type == "csr":
            if not self._is_csr_file(filepath):
                QMessageBox.warning(
                    self, "Invalid CSR",
                    f"'{os.path.basename(filepath)}' is not a valid CSR file."
                )
                return
            self.csr_path = filepath
            if self.csr_input:
                self.csr_input.setText(filepath)
            self._update_file_preview("csr")
        
        elif file_type == "cert":
            if (self._is_valid_certificate_file(filepath) or
                self._is_csr_file(filepath) or
                self._is_valid_key_file(filepath)):
                self.cert_path = filepath
                if self.cert_input:
                    self.cert_input.setText(filepath)
                self._update_file_preview("cert")
            else:
                QMessageBox.warning(
                    self, "Invalid File",
                    f"'{os.path.basename(filepath)}' is not a valid certificate, CSR, or key file."
                )
                return
        
        elif file_type == "key":
            if not self._is_valid_key_file(filepath):
                QMessageBox.warning(
                    self, "Invalid Key",
                    f"'{os.path.basename(filepath)}' is not a valid private key file."
                )
                return
            self.existing_key_path = filepath
            if self.existing_key_input:
                self.existing_key_input.setText(filepath)
            self._update_key_preview()
        
        self._update_execute_button()
    
    # ------------------------------------------------------------------------
    # Page-level drag and drop
    # ------------------------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if not filepath or not os.path.isfile(filepath):
                continue
            
            if self.mode_id == 4:
                target = "cert"
            elif self.mode_id == 3:
                target = "csr"
            elif self.mode_id in [1, 2] and self.selected_key_source == "existing":
                target = "key"
            else:
                if self._is_csr_file(filepath):
                    target = "csr"
                elif self._is_valid_certificate_file(filepath):
                    target = "cert"
                elif self._is_valid_key_file(filepath):
                    target = "key"
                else:
                    QMessageBox.warning(
                        self, "Unsupported File",
                        f"Could not identify '{os.path.basename(filepath)}' as a "
                        f"CSR, certificate, or private key."
                    )
                    continue
            
            self._handle_dropped_file(filepath, target)
            break
    
    # ------------------------------------------------------------------------
    # UI Initialization
    # ------------------------------------------------------------------------
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
        
        title = QLabel("Certificate Management")
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
        
        self.tool_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:12px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
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
        
        self.mode_group = QGroupBox("1. Operation Mode (Drag card to the slot below)")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        
        cards_row = QHBoxLayout()
        cards_row.setSpacing(int(15 * layout_manager.font_scale()))
        cards_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        t = self.theme.current
        
        mode_definitions = [
            (1, "Generate CSR"),
            (2, "Self-Signed Certificate"),
            (3, "Sign CSR"),
            (4, "View Certificate")
        ]
        
        for mode_id, name in mode_definitions:
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
        
        self.options_group = QGroupBox("2. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
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
        
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)
        export_layout.addStretch()
        export_layout.addWidget(QLabel("Export:"))
        
        self.export_private_btn = QPushButton("Private Key")
        self.export_private_btn.setObjectName("actionButton")
        self.export_private_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_private_btn.clicked.connect(lambda: self._export_single("private"))
        self.export_private_btn.hide()
        export_layout.addWidget(self.export_private_btn)
        
        self.export_csr_btn = QPushButton("CSR")
        self.export_csr_btn.setObjectName("actionButton")
        self.export_csr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_csr_btn.clicked.connect(lambda: self._export_single("csr"))
        self.export_csr_btn.hide()
        export_layout.addWidget(self.export_csr_btn)
        
        self.export_cert_btn = QPushButton("Certificate")
        self.export_cert_btn.setObjectName("actionButton")
        self.export_cert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_cert_btn.clicked.connect(lambda: self._export_single("cert"))
        self.export_cert_btn.hide()
        export_layout.addWidget(self.export_cert_btn)
        
        self.export_btn = QPushButton("Export All")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_result)
        self.export_btn.hide()
        export_layout.addWidget(self.export_btn)
        
        copy_btn = QPushButton("Copy All")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        export_layout.addWidget(copy_btn)
        
        layout.addLayout(export_layout)
        
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
        html = f"<h3 style='color:{c};'>OpenSSL</h3>"
        html += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install openssl</p>"
        self.req_output.setHtml(html)
        
        if self.install_btn:
            self.install_btn.setEnabled(not self.openssl_ok)
            self.install_btn.setText(
                "OpenSSL Installed" if self.openssl_ok else "Install Requirements"
            )
    
    # ------------------------------------------------------------------------
    # Slot Event Handlers
    # ------------------------------------------------------------------------
    def _on_slot_dropped(self, slot_type, value):
        if slot_type == "mode":
            self.mode_id = int(value)
            self._rebuild_options()
        elif slot_type == "keysource":
            self.selected_key_source = value
            self._update_key_source_visibility()
        elif slot_type == "keysize":
            self.selected_key_size = int(value)
    
    def _on_slot_cleared(self, slot_type):
        if slot_type == "mode":
            self.mode_id = None
            self._clear_options()
            self.options_group.setVisible(False)
        elif slot_type == "keysource":
            self.selected_key_source = "new"
            if self.key_source_slot:
                self.key_source_slot.set_value("new", "Generate New Private Key")
            self._update_key_source_visibility()
    
    # ------------------------------------------------------------------------
    # Options Management
    # ------------------------------------------------------------------------
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
        
        widget_attrs = [
            'key_size_slot', 'key_source_slot', 'days_input',
            'pass_group', 'pass_check', 'pass_input', 'confirm_input', 'show_pass',
            'csr_group', 'cert_group', 'csr_preview', 'cert_preview',
            'csr_input', 'cert_input', 'cn_input', 'o_input', 'ou_input',
            'l_input', 'st_input', 'c_input', 'email_input',
            'key_size_group', 'existing_key_group',
            'existing_key_preview', 'existing_key_input'
        ]
        for attr in widget_attrs:
            setattr(self, attr, None)
        
        self.key_size_cards.clear()
        self.key_source_cards.clear()
        self.existing_key_path = ""
        self.csr_path = ""
        self.cert_path = ""
        self.selected_key_source = "new"
        if self.execute_btn:
            self.execute_btn.setText("Execute")
            self.execute_btn.setEnabled(False)
    
    def _rebuild_options(self):
        self._clear_options()
        
        if self.mode_id is None:
            self.options_group.setVisible(False)
            return
        
        t = self.theme.current
        
        if self.mode_id in [1, 2]:
            self._build_subject_section()
            if self.mode_id == 2:
                self._build_validity_section()
            self._build_key_source_section(t)
            self._build_key_size_section(t)
            self._build_existing_key_section()
            self._build_password_section()
            self.execute_btn.setText(
                "Generate CSR" if self.mode_id == 1 else "Generate Self-Signed Certificate"
            )
        elif self.mode_id == 3:
            self._build_csr_file_section()
            self._build_validity_section()
            self.execute_btn.setText("Sign CSR")
        elif self.mode_id == 4:
            self._build_cert_file_section()
            self.execute_btn.setText("View Certificate")
        
        self.options_group.setVisible(True)
        self._apply_theme()
        self._update_execute_button()
    
    def _build_subject_section(self):
        subject_group = QGroupBox("Subject (Distinguished Name)")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        fields = [
            ("Common Name (CN) *:", 'cn_input', 'cn'),
            ("Organization (O):", 'o_input', 'o'),
            ("Org Unit (OU):", 'ou_input', 'ou'),
            ("City/Locality (L):", 'l_input', 'l'),
            ("State/Province (ST):", 'st_input', 'st'),
            ("Country (C):", 'c_input', 'c'),
            ("Email:", 'email_input', 'email'),
        ]
        
        for label_text, attr_name, placeholder_key in fields:
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"e.g. {self.PLACEHOLDERS[placeholder_key]}")
            if placeholder_key == 'c':
                input_widget.setMaxLength(2)
                input_widget.setMaximumWidth(80)
            else:
                input_widget.setMinimumWidth(300)
            
            setattr(self, attr_name, input_widget)
            form_layout.addRow(label_text, input_widget)
        
        subject_group.setLayout(form_layout)
        self.options_layout.addWidget(subject_group)
    
    def _build_validity_section(self):
        days_row = QHBoxLayout()
        days_label = QLabel("Validity (days):")
        days_label.setMinimumWidth(120)
        
        self.days_input = QSpinBox()
        self.days_input.setRange(1, 36500)
        self.days_input.setValue(365)
        self.days_input.setMaximumWidth(120)
        self.days_input.setSuffix(" days")
        
        days_row.addWidget(days_label)
        days_row.addWidget(self.days_input)
        days_row.addStretch()
        self.options_layout.addLayout(days_row)
    
    def _build_key_source_section(self, t):
        key_source_wrapper = QGroupBox("Private Key Source (Drag card to slot)")
        key_source_outer = QVBoxLayout()
        key_source_outer.setSpacing(10)
        
        source_cards_row = QHBoxLayout()
        source_cards_row.setSpacing(int(15 * layout_manager.font_scale()))
        for sid, sname in [("new", "Generate New Private Key"), ("existing", "Use Existing Private Key")]:
            card = DraggableKeySourceCard(sid, sname, t)
            self.key_source_cards.append(card)
            source_cards_row.addWidget(card)
        source_cards_row.addStretch()
        key_source_outer.addLayout(source_cards_row)
        
        source_slot_row = QHBoxLayout()
        self.key_source_slot = DropSlot(t, "keysource", "Drop key source here", (240, 80))
        self.key_source_slot.set_value("new", "Generate New Private Key")
        source_slot_row.addWidget(self.key_source_slot)
        source_slot_row.addStretch()
        key_source_outer.addLayout(source_slot_row)
        
        key_source_wrapper.setLayout(key_source_outer)
        self.options_layout.addWidget(key_source_wrapper)
    
    def _build_key_size_section(self, t):
        self.key_size_group = QGroupBox("Key Size (Drag card to slot)")
        key_size_layout = QVBoxLayout()
        key_size_layout.setSpacing(8)
        
        key_cards_row = QHBoxLayout()
        key_cards_row.setSpacing(int(12 * layout_manager.font_scale()))
        for ks in self.KEY_SIZES:
            card = DraggableKeySizeCard(ks, t)
            self.key_size_cards.append(card)
            key_cards_row.addWidget(card)
        key_cards_row.addStretch()
        key_size_layout.addLayout(key_cards_row)
        
        key_slot_row = QHBoxLayout()
        self.key_size_slot = DropSlot(t, "keysize", "Drop key size here", (160, 55))
        self.key_size_slot.set_value("2048", "2048 bits")
        key_slot_row.addWidget(self.key_size_slot)
        key_slot_row.addStretch()
        key_size_layout.addLayout(key_slot_row)
        
        self.key_size_group.setLayout(key_size_layout)
        self.options_layout.addWidget(self.key_size_group)
    
    def _build_existing_key_section(self):
        self.existing_key_group = QGroupBox("Existing Private Key File")
        existing_key_layout = QVBoxLayout()
        
        self.existing_key_preview = DropForwarder(self, "key")
        self.existing_key_preview.setFixedHeight(60)
        self.existing_key_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.existing_key_preview.setText(
            "Drag & drop a private key file here\nor click Browse to select"
        )
        existing_key_layout.addWidget(self.existing_key_preview)
        
        key_file_row = QHBoxLayout()
        self.existing_key_input = QLineEdit()
        self.existing_key_input.setReadOnly(True)
        self.existing_key_input.setPlaceholderText("No key selected...")
        
        for label, slot in [
            ("Browse", self._browse_key_file),
            ("Paste", self._paste_key_file),
            ("Clear", self._clear_key_file)
        ]:
            btn = QPushButton(label)
            btn.setObjectName("actionButton" if label != "Clear" else "dangerButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            key_file_row.addWidget(btn)
        
        existing_key_layout.addLayout(key_file_row)
        self.existing_key_group.setLayout(existing_key_layout)
        self.existing_key_group.setVisible(False)
        self.options_layout.addWidget(self.existing_key_group)
    
    def _build_password_section(self):
        self.pass_group = QGroupBox("Password Protection (Optional)")
        pass_layout = QVBoxLayout()
        
        self.pass_check = QCheckBox("Encrypt private key with password")
        self.pass_check.toggled.connect(self._on_pass_toggle)
        pass_layout.addWidget(self.pass_check)
        
        pass_row = QHBoxLayout()
        pass_row.addWidget(QLabel("Password:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Enter password...")
        self.pass_input.setEnabled(False)
        pass_row.addWidget(self.pass_input, 1)
        
        for label, target in [("Paste", self.pass_input), ("Clear", self.pass_input)]:
            btn = QPushButton(label)
            btn.setObjectName("actionButton" if label == "Paste" else "dangerButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if label == "Paste":
                btn.clicked.connect(lambda checked, w=self.pass_input: self._paste_to(w))
            else:
                btn.clicked.connect(self.pass_input.clear)
            pass_row.addWidget(btn)
        
        pass_layout.addLayout(pass_row)
        
        self.show_pass = QCheckBox("Show password")
        self.show_pass.stateChanged.connect(self._toggle_password_visibility)
        pass_layout.addWidget(self.show_pass)
        
        confirm_row = QHBoxLayout()
        confirm_row.addWidget(QLabel("Confirm:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password...")
        self.confirm_input.setEnabled(False)
        confirm_row.addWidget(self.confirm_input, 1)
        
        for label, target in [("Paste", self.confirm_input), ("Clear", self.confirm_input)]:
            btn = QPushButton(label)
            btn.setObjectName("actionButton" if label == "Paste" else "dangerButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if label == "Paste":
                btn.clicked.connect(lambda checked, w=self.confirm_input: self._paste_to(w))
            else:
                btn.clicked.connect(self.confirm_input.clear)
            confirm_row.addWidget(btn)
        
        pass_layout.addLayout(confirm_row)
        self.pass_group.setLayout(pass_layout)
        self.options_layout.addWidget(self.pass_group)
    
    def _build_csr_file_section(self):
        self.csr_group = QGroupBox("CSR File (Any format)")
        csr_layout = QVBoxLayout()
        
        self.csr_preview = DropForwarder(self, "csr")
        self.csr_preview.setFixedHeight(80)
        self.csr_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.csr_preview.setText("Drag & drop a CSR file here\nor click Browse to select")
        csr_layout.addWidget(self.csr_preview)
        
        csr_row = QHBoxLayout()
        self.csr_input = QLineEdit()
        self.csr_input.setReadOnly(True)
        self.csr_input.setPlaceholderText("No CSR selected...")
        csr_row.addWidget(self.csr_input, 1)
        
        for label, slot in [
            ("Browse", lambda: self._browse_file("csr")),
            ("Paste", lambda: self._paste_file("csr")),
            ("Clear", lambda: self._clear_file("csr"))
        ]:
            btn = QPushButton(label)
            btn.setObjectName("actionButton" if label != "Clear" else "dangerButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            csr_row.addWidget(btn)
        
        csr_layout.addLayout(csr_row)
        self.csr_group.setLayout(csr_layout)
        self.options_layout.addWidget(self.csr_group)
    
    def _build_cert_file_section(self):
        self.cert_group = QGroupBox("Certificate / CSR / Key File (Any format)")
        cert_layout = QVBoxLayout()
        
        self.cert_preview = DropForwarder(self, "cert")
        self.cert_preview.setFixedHeight(80)
        self.cert_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cert_preview.setText(
            "Drag & drop a certificate, CSR, or key file here\n"
            "or click Browse to select"
        )
        cert_layout.addWidget(self.cert_preview)
        
        cert_row = QHBoxLayout()
        self.cert_input = QLineEdit()
        self.cert_input.setReadOnly(True)
        self.cert_input.setPlaceholderText("No file selected...")
        cert_row.addWidget(self.cert_input, 1)
        
        for label, slot in [
            ("Browse", lambda: self._browse_file("cert")),
            ("Paste", lambda: self._paste_file("cert")),
            ("Clear", lambda: self._clear_file("cert"))
        ]:
            btn = QPushButton(label)
            btn.setObjectName("actionButton" if label != "Clear" else "dangerButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            cert_row.addWidget(btn)
        
        cert_layout.addLayout(cert_row)
        self.cert_group.setLayout(cert_layout)
        self.options_layout.addWidget(self.cert_group)
    
    def _update_key_source_visibility(self):
        if self.key_size_group:
            self.key_size_group.setVisible(self.selected_key_source == "new")
        if self.existing_key_group:
            self.existing_key_group.setVisible(self.selected_key_source == "existing")
    
    # ------------------------------------------------------------------------
    # File Handling
    # ------------------------------------------------------------------------
    def _browse_key_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Private Key File", "", "All Files (*)")
        if fp and self._is_valid_key_file(fp):
            self.existing_key_path = fp
            if self.existing_key_input:
                self.existing_key_input.setText(fp)
            self._update_key_preview()
        elif fp:
            QMessageBox.warning(self, "Invalid Key", f"'{os.path.basename(fp)}' is not a valid private key file.")
    
    def _paste_key_file(self):
        clipboard = QApplication.clipboard().text()
        if clipboard and "-----BEGIN" in clipboard and "PRIVATE KEY" in clipboard:
            if self.existing_key_input:
                self.existing_key_input.setText("Pasted from clipboard")
            self.existing_key_path = "clipboard"
            self._update_key_preview()
        else:
            QMessageBox.warning(self, "Invalid Content", "Clipboard does not contain a valid private key")
    
    def _clear_key_file(self):
        self.existing_key_path = ""
        if self.existing_key_input:
            self.existing_key_input.clear()
        self._update_key_preview()
    
    def _update_key_preview(self):
        """Preview label — keeps dashed border when filled (matches stego page)."""
        t = self.theme.current
        if not self.existing_key_preview:
            return
        
        scale = layout_manager.font_scale()
        if self.existing_key_path:
            name = os.path.basename(self.existing_key_path) if self.existing_key_path != "clipboard" else "Pasted from clipboard"
            self.existing_key_preview.setText(name)
            # Keep dashed border, just change text to readable color
            self.existing_key_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;"
                f"background:transparent;color:{t['text']};"
                f"font-size:{int(14 * scale)}px;font-weight:600;padding:10px;"
            )
        else:
            self.existing_key_preview.setText("Drag & drop a private key file here\nor click Browse to select")
            self.existing_key_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;"
                f"background:transparent;color:{t['text_tertiary']};"
                f"font-size:{int(13 * scale)}px;padding:10px;"
            )
    
    def _browse_file(self, file_type):
        if file_type == "csr":
            fp, _ = QFileDialog.getOpenFileName(self, "Select CSR File", "", "All Files (*)")
            if fp:
                if self._is_csr_file(fp):
                    self.csr_path = fp
                    if self.csr_input:
                        self.csr_input.setText(fp)
                    self._update_file_preview("csr")
                    self._update_execute_button()
                else:
                    QMessageBox.warning(self, "Invalid CSR", f"'{os.path.basename(fp)}' is not a valid CSR file.")
        else:
            fp, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
            if fp:
                if (self._is_valid_certificate_file(fp) or
                    self._is_csr_file(fp) or
                    self._is_valid_key_file(fp)):
                    self.cert_path = fp
                    if self.cert_input:
                        self.cert_input.setText(fp)
                    self._update_file_preview("cert")
                    self._update_execute_button()
                else:
                    QMessageBox.warning(
                        self, "Invalid File",
                        f"'{os.path.basename(fp)}' is not a valid certificate, CSR, or key file."
                    )
    
    def _paste_file(self, file_type):
        clipboard = QApplication.clipboard().text()
        if not clipboard or "-----BEGIN" not in clipboard:
            QMessageBox.warning(self, "No Content", "Clipboard does not contain PEM data")
            return
        
        if file_type == "csr":
            if "CERTIFICATE REQUEST" not in clipboard:
                QMessageBox.warning(self, "Invalid Content", "Clipboard does not contain a valid CSR")
                return
            if self.csr_input:
                self.csr_input.setText("Pasted from clipboard")
            self.csr_path = "clipboard"
            self._update_file_preview("csr")
        else:
            if self.cert_input:
                self.cert_input.setText("Pasted from clipboard")
            self.cert_path = "clipboard"
            self._update_file_preview("cert")
        
        self._update_execute_button()
    
    def _clear_file(self, file_type):
        if file_type == "csr":
            self.csr_path = ""
            if self.csr_input:
                self.csr_input.clear()
            self._update_file_preview("csr")
        else:
            self.cert_path = ""
            if self.cert_input:
                self.cert_input.clear()
            self._update_file_preview("cert")
        self._update_execute_button()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard and widget:
            widget.setText(clipboard)
    
    def _update_file_preview(self, file_type):
        """Preview labels — keep dashed border when filled (matches stego page)."""
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        if file_type == "csr" and self.csr_preview:
            if self.csr_path:
                name = os.path.basename(self.csr_path) if self.csr_path != "clipboard" else "Pasted from clipboard"
                self.csr_preview.setText(name)
                # Keep dashed border, change text color
                self.csr_preview.setStyleSheet(
                    f"border:2px dashed {t['border']};border-radius:8px;"
                    f"background:transparent;color:{t['text']};"
                    f"font-size:{int(14 * scale)}px;font-weight:600;padding:10px;"
                )
            else:
                self.csr_preview.setText("Drag & drop a CSR file here\nor click Browse to select")
                self.csr_preview.setStyleSheet(
                    f"border:2px dashed {t['border']};border-radius:8px;"
                    f"background:transparent;color:{t['text_tertiary']};"
                    f"font-size:{int(13 * scale)}px;padding:10px;"
                )
        elif file_type == "cert" and self.cert_preview:
            if self.cert_path:
                name = os.path.basename(self.cert_path) if self.cert_path != "clipboard" else "Pasted from clipboard"
                self.cert_preview.setText(name)
                # Keep dashed border, change text color
                self.cert_preview.setStyleSheet(
                    f"border:2px dashed {t['border']};border-radius:8px;"
                    f"background:transparent;color:{t['text']};"
                    f"font-size:{int(14 * scale)}px;font-weight:600;padding:10px;"
                )
            else:
                self.cert_preview.setText(
                    "Drag & drop a certificate, CSR, or key file here\n"
                    "or click Browse to select"
                )
                self.cert_preview.setStyleSheet(
                    f"border:2px dashed {t['border']};border-radius:8px;"
                    f"background:transparent;color:{t['text_tertiary']};"
                    f"font-size:{int(13 * scale)}px;padding:10px;"
                )
    
    def _update_execute_button(self):
        mode_filled = self.mode_slot.is_filled() if self.mode_slot else False
        mode_id = int(self.mode_slot.value) if (self.mode_slot and self.mode_slot.is_filled()) else None
        
        if not mode_filled or not self.execute_btn:
            if self.execute_btn:
                self.execute_btn.setEnabled(False)
            return
        
        if mode_id == 3 and not self.csr_path:
            self.execute_btn.setEnabled(False)
            return
        
        if mode_id == 4 and not self.cert_path:
            self.execute_btn.setEnabled(False)
            return
        
        self.execute_btn.setEnabled(True)
    
    def _toggle_password_visibility(self, state):
        if self.pass_input and self.confirm_input:
            echo_mode = QLineEdit.EchoMode.Normal if state == Qt.CheckState.Checked.value else QLineEdit.EchoMode.Password
            self.pass_input.setEchoMode(echo_mode)
            self.confirm_input.setEchoMode(echo_mode)
    
    def _on_pass_toggle(self, checked):
        if self.pass_input and self.confirm_input:
            self.pass_input.setEnabled(checked)
            self.confirm_input.setEnabled(checked)
            if not checked:
                self.pass_input.clear()
                self.confirm_input.clear()
    
    def _install_openssl(self):
        if QMessageBox.question(
            self, "Install OpenSSL",
            "Install OpenSSL?\n\nsudo apt install -y openssl",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        if self.install_btn:
            self.install_btn.setEnabled(False)
            self.install_btn.setText("Installing...")
        if self.install_status:
            self.install_status.setText("Running: sudo apt install -y openssl")
        
        try:
            subprocess.run(
                ["sudo", "apt", "install", "-y", "openssl"],
                capture_output=True, text=True, timeout=120
            )
            self.openssl_ok = self._check_openssl()
            if self.install_status:
                self.install_status.setText("Done!" if self.openssl_ok else "Failed")
        except Exception as e:
            if self.install_status:
                self.install_status.setText(f"Error: {e}")
        
        self._update_tool_badge()
        self._update_requirements()
    
    # ------------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------------
    def _execute(self):
        if not self.mode_slot or not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Please select an operation mode")
            return
        
        mode_id = int(self.mode_slot.value)
        
        if mode_id == 3 and not self.csr_path:
            QMessageBox.warning(self, "Missing File", "Please select a CSR file")
            return
        
        if mode_id == 4 and not self.cert_path:
            QMessageBox.warning(self, "Missing File", "Please select a file")
            return
        
        passphrase = ""
        if self.pass_check and self.pass_check.isChecked():
            password = self.pass_input.text() if self.pass_input else ""
            confirm = self.confirm_input.text() if self.confirm_input else ""
            if not password or not confirm:
                QMessageBox.warning(self, "Missing Password", "Please enter and confirm your password.")
                return
            if password != confirm:
                QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                return
            passphrase = password
        
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
        if self.export_private_btn:
            self.export_private_btn.hide()
        if self.export_csr_btn:
            self.export_csr_btn.hide()
        if self.export_cert_btn:
            self.export_cert_btn.hide()
        
        use_existing_key = (self.selected_key_source == "existing")
        if use_existing_key and not self.existing_key_path:
            QMessageBox.warning(self, "Missing Key", "Please select an existing private key file.")
            if self.execute_btn:
                self.execute_btn.setEnabled(True)
            return
        
        if mode_id in [1, 2]:
            subject = self._build_subject_from_fields()
            if not subject:
                QMessageBox.warning(self, "Missing Subject", "Please fill in at least the Common Name (CN) field.")
                if self.execute_btn:
                    self.execute_btn.setEnabled(True)
                return
            
            key_size = self.selected_key_size
            
            if mode_id == 1:
                self.worker = CertificateWorker(
                    mode="generate_csr", subject=subject, key_size=key_size,
                    passphrase=passphrase, existing_key_path=self.existing_key_path,
                    use_existing_key=use_existing_key
                )
            else:
                days = self.days_input.value() if self.days_input else 365
                self.worker = CertificateWorker(
                    mode="generate_self_signed", subject=subject, days=days,
                    key_size=key_size, passphrase=passphrase,
                    existing_key_path=self.existing_key_path, use_existing_key=use_existing_key
                )
        elif mode_id == 3:
            days = self.days_input.value() if self.days_input else 365
            self.worker = CertificateWorker(mode="sign_csr", csr_path=self.csr_path, days=days)
        elif mode_id == 4:
            self.worker = CertificateWorker(mode="view_cert", cert_path=self.cert_path)
        
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
    
    def _on_finished(self, success, result, data):
        if self.execute_btn:
            self.execute_btn.setEnabled(True)
        
        if success:
            if self.status_output:
                self.status_output.append("SUCCESS!")
            if self.status_progress:
                self.status_progress.setValue(100)
            if self.results_output:
                self.results_output.setText(result)
            if self.export_btn:
                self.export_btn.show()
            if self.worker and self.worker.private_key and self.export_private_btn:
                self.export_private_btn.show()
            if self.worker and self.worker.csr_data and self.export_csr_btn:
                self.export_csr_btn.show()
            if self.worker and self.worker.certificate and self.export_cert_btn:
                self.export_cert_btn.show()
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
    
    def _export_single(self, data_type):
        if not self.worker:
            return
        
        data_map = {
            'private': (self.worker.private_key, 'private_key.pem', 'PEM Files (*.pem);;KEY Files (*.key);;All Files (*)'),
            'csr': (self.worker.csr_data, 'request.csr', 'CSR Files (*.csr);;PEM Files (*.pem);;All Files (*)'),
            'cert': (self.worker.certificate, 'certificate.crt', 'CRT Files (*.crt);;PEM Files (*.pem);;CER Files (*.cer);;All Files (*)'),
        }
        
        if data_type not in data_map:
            return
        
        data, default_name, file_filter = data_map[data_type]
        if not data:
            QMessageBox.warning(self, "No Data", f"No {data_type.upper()} data to export.")
            return
        
        fp, _ = QFileDialog.getSaveFileName(self, f"Export {data_type.upper()}", default_name, file_filter)
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(data)
                QMessageBox.information(self, "Exported", f"{data_type.upper()} saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def _export_result(self):
        if not self.results_output:
            return
        
        text = self.results_output.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Results", "Nothing to export")
            return
        
        mode_id = int(self.mode_slot.value) if (self.mode_slot and self.mode_slot.is_filled()) else 1
        names = {1: "csr_and_key.txt", 2: "self_signed_cert.txt", 3: "signed_cert.txt", 4: "cert_info.txt"}
        default_name = names.get(mode_id, "cert_info.txt")
        
        fp, _ = QFileDialog.getSaveFileName(self, "Export Results", default_name, "Text Files (*.txt);;All Files (*)")
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Exported", f"Results saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    # ------------------------------------------------------------------------
    # Theme Application
    # ------------------------------------------------------------------------
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        if self.tabs:
            self.tabs.setStyleSheet(f"""
                QTabWidget::pane {{ border: 1px solid {t['border']}; border-radius: 8px; background-color: {t['base']}; }}
                QTabBar::tab {{ background-color: {t['crust']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; padding: 10px 28px; margin-right: 2px; border-top-left-radius: 7px; border-top-right-radius: 7px; font-size: {int(13 * scale)}px; font-weight: 600; }}
                QTabBar::tab:selected {{ background-color: {t['base']}; color: {t['text']}; border-bottom-color: transparent; }}
            """)
        
        gs = (
            f"QGroupBox {{ color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; "
            f"margin-top: 14px; padding: 20px 16px 16px; font-weight: 600; font-size: {int(13 * scale)}px; }} "
            f"QGroupBox::title {{ left: 14px; padding: 0 8px; color: {t['text']}; }}"
        )
        for attr in ['mode_group', 'options_group', 'req_group', 'key_size_group', 'existing_key_group', 'csr_group', 'cert_group']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(gs)
                    except RuntimeError:
                        pass
        
        for slot_attr in ['mode_slot', 'key_source_slot', 'key_size_slot']:
            if hasattr(self, slot_attr):
                slot = getattr(self, slot_attr)
                if slot:
                    slot.update_colors(t)
        
        for card_list in [self.mode_cards, self.key_size_cards, self.key_source_cards]:
            for card in card_list:
                try:
                    card.update_theme(t)
                except RuntimeError:
                    pass
        
        cb_style = (
            f"QCheckBox {{ color: {t['text']}; font-size: {int(13 * scale)}px; spacing: 8px; }} "
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {t['border']}; "
            f"border-radius: 4px; background: {t['crust']}; }} "
            f"QCheckBox::indicator:checked {{ background: {t['accent']}; border-color: {t['accent']}; }}"
        )
        for attr in ['pass_check', 'show_pass']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(cb_style)
                    except RuntimeError:
                        pass
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        input_attrs = [
            'csr_input', 'cert_input', 'pass_input', 'confirm_input', 'existing_key_input',
            'cn_input', 'o_input', 'ou_input', 'l_input', 'st_input', 'c_input', 'email_input'
        ]
        for attr in input_attrs:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj:
                    try:
                        obj.setStyleSheet(input_style)
                    except RuntimeError:
                        pass
        
        if self.days_input:
            self.days_input.setStyleSheet(
                f"QSpinBox{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
                f"font-size:{max(12, int(13 * scale))}px;}} "
                f"QSpinBox:hover{{border-color:{t['accent']};}}"
            )
        
        btn_min_w = max(70, int(84 * scale))
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(20 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}} "
                        f"QPushButton:disabled{{color:{t['text_tertiary']};}}"
                    )
                    if btn.text() in ("Paste", "Copy", "Browse"):
                        btn.setMinimumWidth(btn_min_w)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(20 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                    if btn.text() == "Clear":
                        btn.setMinimumWidth(btn_min_w)
                elif btn.objectName() == "backButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:transparent;color:{t['text']};"
                        f"border:none;padding:8px 16px;font-weight:600;}} "
                        f"QPushButton:hover{{background-color:transparent;}}"
                    )
            except RuntimeError:
                pass
        
        if self.execute_btn:
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        text_style = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        if self.status_output:
            self.status_output.setStyleSheet(text_style)
        if self.results_output:
            self.results_output.setStyleSheet(
                f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(14 * scale)}px;"
                f"font-weight:600;line-height:1.6;}}"
            )
        if self.req_output:
            self.req_output.setStyleSheet(
                f"QTextBrowser{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-size:{int(12 * scale)}px;}}"
            )
        
        if self.status_progress:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
            )
        
        for label in self.findChildren(QLabel):
            try:
                if label.objectName() == "pageTitle":
                    label.setStyleSheet(
                        f"color:{t['text']};font-size:{int(24 * scale)}px;"
                        f"font-weight:700;padding:4px 0;"
                    )
            except RuntimeError:
                pass
        
        self._update_file_preview("csr")
        self._update_file_preview("cert")
        self._update_key_preview()
    
    def refresh_theme(self):
        self._apply_theme()
        self._update_tool_badge()
        self._update_requirements()