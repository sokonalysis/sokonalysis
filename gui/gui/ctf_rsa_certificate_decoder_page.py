# gui/ctf_rsa_certificate_decoder_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QTextCursor

import os
import subprocess
import sys
import re
import tempfile
import hashlib
from datetime import datetime


class CertificateDecoderWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, pem_content):
        super().__init__()
        self.pem_content = pem_content
    
    def _fix_pem_format(self, pem):
        """Fix PEM format by removing whitespace and adding proper line breaks"""
        header = "-----BEGIN CERTIFICATE-----"
        footer = "-----END CERTIFICATE-----"
        
        header_pos = pem.find(header)
        footer_pos = pem.find(footer)
        if header_pos == -1 or footer_pos == -1:
            return None
        
        base64_start = header_pos + len(header)
        base64_data = pem[base64_start:footer_pos]
        
        # Remove whitespace
        base64_data = re.sub(r'\s+', '', base64_data)
        
        fixed_pem = header + "\n"
        for i in range(0, len(base64_data), 64):
            fixed_pem += base64_data[i:i+64] + "\n"
        fixed_pem += footer + "\n"
        
        return fixed_pem
    
    def _format_hex_with_spaces(self, hex_str):
        """Format hex string with spaces every 2 characters"""
        if not hex_str:
            return ""
        clean = re.sub(r'[\s:\n]', '', hex_str)
        if not clean:
            return ""
        return ' '.join(clean[i:i+2] for i in range(0, len(clean), 2))
    
    def _run_openssl_command(self, cmd):
        """Run an openssl command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except:
            return ""
    
    def _get_der_from_pubkey(self, pubkey_pem):
        """Convert PEM public key to DER bytes"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pub', delete=False) as pub_f:
                pub_f.write(pubkey_pem)
                temp_pub = pub_f.name
            
            try:
                result = subprocess.run(
                    ["openssl", "pkey", "-pubin", "-in", temp_pub, "-outform", "DER"],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout
            except:
                pass
            finally:
                if os.path.exists(temp_pub):
                    try:
                        os.unlink(temp_pub)
                    except:
                        pass
        except:
            pass
        return None
    
    def _parse_asn1_for_exponent(self, asn1_output):
        """Parse ASN.1 output to find the exponent"""
        if not asn1_output:
            return None, None
        
        lines = asn1_output.split('\n')
        int_count = 0
        for line in lines:
            if 'INTEGER' in line:
                int_count += 1
                if int_count == 2:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        hex_val = parts[2].strip()
                        hex_val = hex_val.lstrip('0')
                        if hex_val:
                            return hex_val, str(int(hex_val, 16))
        return None, None
    
    def _decode_certificate(self, pem_content):
        """Decode certificate and extract RSA parameters using openssl"""
        try:
            fixed_pem = self._fix_pem_format(pem_content)
            if not fixed_pem:
                return False, "Invalid PEM certificate format"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                f.write(fixed_pem)
                temp_pem = f.name
            
            try:
                self.progress.emit("Decoding certificate...")
                self.progress_value.emit(20)
                
                # Get all certificate info
                subject_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-subject"])
                issuer_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-issuer"])
                dates_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-dates"])
                serial_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-serial"])
                fingerprint_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-fingerprint"])
                modulus_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-noout", "-modulus"])
                pubkey_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-pubkey", "-noout"])
                text_output = self._run_openssl_command(["openssl", "x509", "-in", temp_pem, "-text", "-noout"])
                asn1_output = self._run_openssl_command(["openssl", "asn1parse", "-in", temp_pem])
                
                # Get MD5 fingerprint specifically
                md5_fingerprint = ""
                cmd_md5 = ["openssl", "x509", "-in", temp_pem, "-noout", "-fingerprint", "-md5"]
                md5_result = self._run_openssl_command(cmd_md5)
                if md5_result:
                    for line in md5_result.split('\n'):
                        if 'MD5 Fingerprint=' in line:
                            fp = line.split('=', 1)[1].strip()
                            md5_fingerprint = self._format_hex_with_spaces(fp)
                            break
                
                self.progress.emit("Extracting RSA parameters...")
                self.progress_value.emit(50)
                
                # Parse subject
                subject_parts = {}
                if subject_output:
                    subject_str = subject_output.replace("subject=", "").strip()
                    parts = re.split(r',\s*(?=[A-Z]+=)', subject_str)
                    for part in parts:
                        part = part.strip()
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key_map = {
                                'OU': 'OU (Organisational Unit)',
                                'O': 'O (Organisation)',
                                'L': 'L (Locality)',
                                'ST': 'ST (County)',
                                'C': 'C (Country)',
                                'CN': 'CN (Common Name)'
                            }
                            display_key = key_map.get(key, key)
                            subject_parts[display_key] = value.strip()
                
                # Parse issuer
                issuer_parts = {}
                if issuer_output:
                    issuer_str = issuer_output.replace("issuer=", "").strip()
                    parts = re.split(r',\s*(?=[A-Z]+=)', issuer_str)
                    for part in parts:
                        part = part.strip()
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key_map = {
                                'OU': 'OU (Organisational Unit)',
                                'O': 'O (Organisation)',
                                'L': 'L (Locality)',
                                'ST': 'ST (County)',
                                'C': 'C (Country)',
                                'CN': 'CN (Common Name)'
                            }
                            display_key = key_map.get(key, key)
                            issuer_parts[display_key] = value.strip()
                
                # Parse dates
                not_before = ""
                not_after = ""
                if dates_output:
                    for line in dates_output.split('\n'):
                        if 'notBefore=' in line:
                            date_str = line.replace('notBefore=', '').strip()
                            try:
                                dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                                not_before = dt.strftime("%Y-%m-%d")
                            except:
                                not_before = date_str
                        elif 'notAfter=' in line:
                            date_str = line.replace('notAfter=', '').strip()
                            try:
                                dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                                not_after = dt.strftime("%Y-%m-%d")
                            except:
                                not_after = date_str
                
                # Parse serial
                serial = ""
                if serial_output:
                    serial_raw = serial_output.replace("serial=", "").strip()
                    serial = self._format_hex_with_spaces(serial_raw)
                
                # Parse SHA1 fingerprint
                sha1_fp = ""
                if fingerprint_output:
                    for line in fingerprint_output.split('\n'):
                        if 'SHA1 Fingerprint=' in line:
                            fp = line.split('=', 1)[1].strip()
                            sha1_fp = self._format_hex_with_spaces(fp)
                            break
                
                # Parse modulus
                modulus_hex = ""
                modulus_clean = ""
                if modulus_output:
                    mod_str = modulus_output.replace("Modulus=", "").strip()
                    modulus_clean = mod_str
                    modulus_hex = self._format_hex_with_spaces(mod_str)
                
                # Get key size
                key_size = ""
                key_size_match = re.search(r'Public-Key:\s*\((\d+)\s+bit\)', text_output)
                if key_size_match:
                    key_size = key_size_match.group(1)
                elif modulus_clean:
                    key_size = str(len(modulus_clean) * 4)
                
                # Get exponent from ASN.1
                exponent_hex = ""
                exponent_dec = ""
                
                if asn1_output:
                    exp_hex, exp_dec = self._parse_asn1_for_exponent(asn1_output)
                    if exp_hex:
                        exponent_hex = exp_hex
                        exponent_dec = exp_dec
                
                if not exponent_hex:
                    exp_match = re.search(r'Exponent:\s*(\d+)\s*\(0x([0-9a-fA-F]+)\)', text_output)
                    if exp_match:
                        exponent_dec = exp_match.group(1)
                        exponent_hex = exp_match.group(2).upper()
                    else:
                        exp_match = re.search(r'Exponent:\s*(\d+)', text_output)
                        if exp_match:
                            exponent_dec = exp_match.group(1)
                            exponent_hex = hex(int(exponent_dec))[2:].upper()
                
                # Get Key SHA1 Fingerprint
                key_sha1 = ""
                if pubkey_output:
                    der_data = self._get_der_from_pubkey(pubkey_output)
                    if der_data:
                        sha1_hash = hashlib.sha1(der_data).hexdigest().upper()
                        key_sha1 = self._format_hex_with_spaces(sha1_hash)
                
                # Build Public Key ASN.1
                public_key_asn1 = ""
                if modulus_clean and exponent_hex:
                    mod_clean_no_leading = modulus_clean.lstrip('0')
                    if not mod_clean_no_leading:
                        mod_clean_no_leading = '0'
                    mod_len = len(mod_clean_no_leading) // 2
                    exp_len = len(exponent_hex) // 2
                    
                    asn1_parts = []
                    asn1_parts.append("30")
                    total_len = 2 + 2 + mod_len + 2 + 2 + exp_len
                    asn1_parts.append(format(total_len, '02X'))
                    
                    asn1_parts.append("02")
                    asn1_parts.append(format(mod_len, '02X'))
                    mod_spaced = ' '.join(mod_clean_no_leading[i:i+2] for i in range(0, len(mod_clean_no_leading), 2))
                    asn1_parts.append(mod_spaced)
                    
                    asn1_parts.append("02")
                    asn1_parts.append(format(exp_len, '02X'))
                    exp_spaced = ' '.join(exponent_hex[i:i+2] for i in range(0, len(exponent_hex), 2))
                    asn1_parts.append(exp_spaced)
                    
                    public_key_asn1 = ' '.join(asn1_parts)
                
                # Key Parameters
                key_params = ""
                if exponent_hex:
                    if len(exponent_hex) % 2 != 0:
                        exponent_hex = '0' + exponent_hex
                    key_params = self._format_hex_with_spaces(exponent_hex)
                
                # Get signature
                sig_alg = ""
                sig_match = re.search(r'Signature Algorithm:\s*(.+?)(?:\n|$)', text_output)
                if sig_match:
                    sig_alg = sig_match.group(1).strip()
                    sig_alg = sig_alg.replace('WithRSAEncryption', ' with RSA')
                    sig_alg = sig_alg.replace('WithRSA', ' with RSA')
                    sig_alg = sig_alg.replace('md2', 'MD2')
                
                signature = ""
                sig_body_match = re.search(r'Signature:\s*([0-9a-fA-F:\n ]+?)(?:\n\s*\n|$)', text_output, re.DOTALL)
                if sig_body_match:
                    sig_str = sig_body_match.group(1).strip()
                    sig_str = re.sub(r'[\s:]', '', sig_str)
                    signature = self._format_hex_with_spaces(sig_str)
                
                sig_params = key_params
                
                self.progress_value.emit(90)
                
                # Build formatted result - simple, clean, no tabs
                result_lines = []
                
                # Identity
                cn = subject_parts.get('CN (Common Name)', 'Unknown')
                issuer_cn = issuer_parts.get('CN (Common Name)', 'Unknown')
                
                result_lines.append(f"{cn}")
                result_lines.append(f"Identity: {cn}")
                result_lines.append(f"Verified by: {issuer_cn}")
                
                expiry = "Unknown"
                if not_after:
                    try:
                        dt = datetime.strptime(not_after, "%Y-%m-%d")
                        expiry = dt.strftime("%d/%m/%y")
                    except:
                        expiry = not_after
                result_lines.append(f"Expires: {expiry}")
                result_lines.append("")
                
                # Subject Name
                result_lines.append("Subject Name")
                if subject_parts:
                    for key, value in subject_parts.items():
                        result_lines.append(f"{key}: {value}")
                result_lines.append("")
                
                # Issuer Name
                result_lines.append("Issuer Name")
                if issuer_parts:
                    for key, value in issuer_parts.items():
                        result_lines.append(f"{key}: {value}")
                result_lines.append("")
                
                # Issued Certificate
                result_lines.append("Issued Certificate")
                version_match = re.search(r'Version:\s*(\d+)', text_output)
                if version_match:
                    result_lines.append(f"Version: {version_match.group(1)}")
                if serial:
                    result_lines.append(f"Serial Number: {serial}")
                if not_before:
                    result_lines.append(f"Not Valid Before: {not_before}")
                if not_after:
                    result_lines.append(f"Not Valid After: {not_after}")
                result_lines.append("")
                
                # Certificate Fingerprints
                result_lines.append("Certificate Fingerprints")
                if sha1_fp:
                    result_lines.append(f"SHA1: {sha1_fp}")
                if md5_fingerprint:
                    result_lines.append(f"MD5: {md5_fingerprint}")
                result_lines.append("")
                
                # Public Key Info
                result_lines.append("Public Key Info")
                result_lines.append("Key Algorithm: RSA")
                if key_params:
                    result_lines.append(f"Key Parameters: {key_params}")
                if key_size:
                    result_lines.append(f"Key Size: {key_size}")
                if key_sha1:
                    result_lines.append(f"Key SHA1 Fingerprint: {key_sha1}")
                if public_key_asn1:
                    result_lines.append(f"Public Key: {public_key_asn1}")
                elif modulus_hex:
                    result_lines.append(f"Public Key: {modulus_hex}")
                
                # CTF Format
                if modulus_clean and exponent_dec:
                    n_decimal = str(int(modulus_clean, 16))
                    result_lines.append(f"n (modulus): {n_decimal}")
                    result_lines.append(f"e (exponent): {exponent_dec}")
                
                result_lines.append("")
                
                # Signature
                result_lines.append("Signature")
                if sig_alg:
                    result_lines.append(f"Signature Algorithm: {sig_alg}")
                if sig_params:
                    result_lines.append(f"Signature Parameters: {sig_params}")
                if signature:
                    result_lines.append(f"Signature: {signature}")
                
                self.progress_value.emit(100)
                self.progress.emit("Done!")
                
                return True, "\n".join(result_lines)
                
            except Exception as e:
                return False, f"Error processing certificate: {str(e)}"
            finally:
                if os.path.exists(temp_pem):
                    try:
                        os.unlink(temp_pem)
                    except:
                        pass
                    
        except Exception as e:
            return False, f"Error decoding certificate: {str(e)}"
    
    def run(self):
        try:
            success, result = self._decode_certificate(self.pem_content)
            self.finished.emit(success, result)
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class CTFRSACertificateDecoderPage(QWidget):
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.cert_path = ""
        self.openssl_ok = self._check_openssl()
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
            if filepath:
                self._load_certificate(filepath)
                break
    
    def _load_certificate(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if "-----BEGIN CERTIFICATE-----" in content and "-----END CERTIFICATE-----" in content:
                self.cert_path = filepath
                self.cert_path_input.setText(filepath)
                self._update_cert_preview()
                self.decode_btn.setEnabled(self.openssl_ok)
            else:
                QMessageBox.warning(self, "Invalid Certificate", "File does not contain a valid PEM certificate")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
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
        
        title = QLabel("RSA Certificate Decoder")
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
        
        self.cert_group = QGroupBox("1. PEM Certificate")
        cert_layout = QVBoxLayout()
        
        self.cert_preview = QLabel()
        self.cert_preview.setFixedHeight(120)
        self.cert_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cert_preview.setText("Drag & drop or click Browse\nto select a PEM certificate file")
        
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        cert_icon_path = os.path.join(icons_dir, "wordlist.png")
        if os.path.exists(cert_icon_path):
            self.cert_icon = QIcon(cert_icon_path)
        
        cert_layout.addWidget(self.cert_preview)
        
        cert_row = QHBoxLayout()
        self.cert_path_input = QLineEdit()
        self.cert_path_input.setReadOnly(True)
        self.cert_path_input.setPlaceholderText("Select certificate file (.pem, .crt, .cer)...")
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_certificate)
        
        cert_row.addWidget(self.cert_path_input, 1)
        cert_row.addWidget(browse_btn)
        cert_layout.addLayout(cert_row)
        
        self.cert_info = QLabel("")
        cert_layout.addWidget(self.cert_info)
        
        self.cert_group.setLayout(cert_layout)
        layout.addWidget(self.cert_group)
        
        self.decode_btn = QPushButton("Decode Certificate")
        self.decode_btn.setObjectName("actionButton")
        self.decode_btn.setMinimumHeight(48)
        self.decode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.decode_btn.clicked.connect(self._decode_certificate)
        self.decode_btn.setEnabled(False)
        layout.addWidget(self.decode_btn)
        
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
        
        results_header = QHBoxLayout()
        results_label = QLabel("Decoded Certificate:")
        copy_btn = QPushButton("Copy Results")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        
        export_btn = QPushButton("Export Results")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_results)
        
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        results_header.addWidget(export_btn)
        layout.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Decoded RSA parameters will appear here...")
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
        self.decode_btn.setEnabled(self.openssl_ok and bool(self.cert_path))
    
    def _update_cert_preview(self):
        if not self.cert_path or not os.path.exists(self.cert_path):
            self.cert_preview.setText("Drag & drop or click Browse\nto select a PEM certificate file")
            self.cert_info.setText("")
            return
        
        fn = os.path.basename(self.cert_path)
        sz = os.path.getsize(self.cert_path)
        ext = os.path.splitext(self.cert_path)[1].lower()
        ss = f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
        
        # Use wordlist.png icon instead of emoji
        if hasattr(self, 'cert_icon'):
            pixmap = self.cert_icon.pixmap(64, 64)
            self.cert_preview.setPixmap(pixmap)
            self.cert_preview.setText(f"\n{fn}")
            self.cert_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.cert_preview.setText(f"Certificate\n{fn}")
        
        self.cert_info.setText(f"Size: {ss} | Format: {ext.upper().replace('.','')}")
    
    def _browse_certificate(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "Select PEM Certificate", "",
            "PEM Files (*.pem *.crt *.cer);;All Files (*)"
        )
        if fp:
            self._load_certificate(fp)
    
    def _decode_certificate(self):
        if not self.cert_path:
            QMessageBox.warning(self, "No Certificate", "Please load a PEM certificate")
            return
        
        if not self.openssl_ok:
            QMessageBox.warning(self, "OpenSSL Missing", "OpenSSL is required for decoding certificates")
            return
        
        try:
            with open(self.cert_path, 'r', encoding='utf-8', errors='ignore') as f:
                cert_content = f.read()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read certificate: {str(e)}")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.decode_btn.setEnabled(False)
        
        self.worker = CertificateDecoderWorker(cert_content)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_decode_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_decode_finished(self, success, result):
        self.decode_btn.setEnabled(True)
        if success:
            self.status_output.append("Decoding completed!")
            self.status_progress.setValue(100)
            self.results_output.setText(result)
            cursor = self.results_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.results_output.setTextCursor(cursor)
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR:\n{result}")
            self.status_progress.setValue(100)
            QMessageBox.critical(self, "Decoding Failed", result)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied to clipboard!")
    
    def _export_results(self):
        text = self.results_output.toPlainText()
        if not text:
            QMessageBox.warning(self, "No Results", "Nothing to export")
            return
        
        fp, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "rsa_certificate_decoded.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if fp:
            try:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Exported", f"Results saved to:\n{fp}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def _apply_theme(self):
        t = self.theme.current
        
        # Tab styling
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
        if hasattr(self, 'cert_group'):
            self.cert_group.setStyleSheet(gs)
        if hasattr(self, 'req_group'):
            self.req_group.setStyleSheet(gs)
        
        if hasattr(self, 'cert_preview'):
            self.cert_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;"
            )
        
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
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        if hasattr(self, 'cert_path_input'):
            self.cert_path_input.setStyleSheet(input_style)
        
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
        
        # Button styling - back button matches ctf_rsa_common_modulus.py exactly
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
                    # Exact match with ctf_rsa_common_modulus.py
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
        
        # Label styling
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
        
        if hasattr(self, 'cert_info'):
            self.cert_info.setStyleSheet(f"color:{t['text_tertiary']};font-size:11px;background:transparent;")
    
    def refresh_theme(self):
        self._apply_theme()
        self._update_tool_badge()
        self._update_requirements()