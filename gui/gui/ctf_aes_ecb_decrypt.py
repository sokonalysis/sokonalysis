# gui/ctf_aes_ecb_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QProgressBar, QScrollArea, QFrame, QApplication,
    QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon
import os
import sys

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_PYCRYPTODOME = True
except ImportError:
    HAS_PYCRYPTODOME = False


class AESECBDecryptWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, dict)

    def __init__(self, key_hex, ciphertext, padding):
        super().__init__()
        self.key_hex = key_hex
        self.ciphertext = ciphertext
        self.padding = padding

    def _decode_ciphertext(self):
        import base64
        raw = self.ciphertext.strip().replace(" ", "").replace("\n", "").replace("\r", "")
        try:
            return base64.b64decode(raw, validate=True)
        except Exception:
            return bytes.fromhex(raw)

    def run(self):
        try:
            self.progress.emit("Parsing inputs...")
            self.progress_value.emit(10)

            if not HAS_PYCRYPTODOME:
                raise RuntimeError(
                    "pycryptodome is not installed. Run: pip install pycryptodome"
                )

            key = bytes.fromhex(self.key_hex.strip())
            if len(key) not in (16, 24, 32):
                raise ValueError(
                    f"Key must be 16, 24, or 32 bytes (got {len(key)})"
                )
            self.progress.emit(f"Key: {len(key) * 8}-bit AES")
            self.progress_value.emit(30)

            ct = self._decode_ciphertext()
            if len(ct) == 0 or len(ct) % 16 != 0:
                raise ValueError(
                    f"Ciphertext length must be a positive multiple of 16 (got {len(ct)})"
                )
            self.progress.emit(f"Ciphertext: {len(ct)} bytes ({len(ct) // 16} blocks)")
            self.progress_value.emit(50)

            self.progress.emit("Decrypting with AES-ECB...")
            cipher = AES.new(key, AES.MODE_ECB)
            pt = cipher.decrypt(ct)

            if self.padding:
                self.progress.emit("Removing PKCS#7 padding...")
                pt = unpad(pt, 16)

            self.progress_value.emit(90)

            try:
                plaintext = pt.decode("utf-8")
                is_text = True
            except UnicodeDecodeError:
                plaintext = pt.hex()
                is_text = False

            self.progress.emit("Plaintext recovered.")
            self.progress_value.emit(100)
            self.finished.emit(True, plaintext, {
                "key_bits": len(key) * 8,
                "ct_bytes": len(ct),
                "pt_bytes": len(pt),
                "is_text": is_text,
                "mode": "AES-ECB",
            })

        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), {})


class CTF_AES_ECB_DecryptPage(QWidget):

    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, "_MEIPASS")
            else os.path.join(os.path.dirname(__file__), ".."),
            "assets", "icons"
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)

        title = QLabel("AES — ECB — Decrypt")
        title.setObjectName("pageTitle")

        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")

        layout.addLayout(header)
        layout.addWidget(self.tabs)

        self._apply_theme()

    # ---------- Setup tab ----------

    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # --- Key (hex) ---
        self.key_group = QGroupBox("Key (hex)")
        self.key_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        key_layout = QVBoxLayout()
        key_layout.setContentsMargins(12, 24, 12, 12)   # 24 top = room for title
        key_layout.setSpacing(8)
        self.key_input = QLineEdit()                        # no placeholder
        key_layout.addWidget(self.key_input)

        key_btn = QHBoxLayout()
        key_paste = QPushButton("Paste")
        key_paste.setObjectName("actionButton")
        key_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        key_paste.clicked.connect(lambda: self._paste_to(self.key_input))
        key_clear = QPushButton("Clear")
        key_clear.setObjectName("dangerButton")
        key_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        key_clear.clicked.connect(self.key_input.clear)
        key_btn.addWidget(key_paste)
        key_btn.addWidget(key_clear)
        key_btn.addStretch()
        key_layout.addLayout(key_btn)
        self.key_group.setLayout(key_layout)
        layout.addWidget(self.key_group)

        # --- Ciphertext ---
        self.ct_group = QGroupBox("Ciphertext (Base64)")
        self.ct_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        ct_layout = QVBoxLayout()
        ct_layout.setContentsMargins(12, 24, 12, 12)   # 24 top = room for title
        ct_layout.setSpacing(8)
        self.ct_input = QTextEdit()                         # no placeholder
        self.ct_input.setMinimumHeight(60)
        self.ct_input.setMaximumHeight(90)
        self.ct_input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ct_layout.addWidget(self.ct_input)

        ct_btn = QHBoxLayout()
        ct_paste = QPushButton("Paste")
        ct_paste.setObjectName("actionButton")
        ct_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        ct_paste.clicked.connect(lambda: self._paste_to(self.ct_input))
        ct_clear = QPushButton("Clear")
        ct_clear.setObjectName("dangerButton")
        ct_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        ct_clear.clicked.connect(self.ct_input.clear)
        ct_btn.addWidget(ct_paste)
        ct_btn.addWidget(ct_clear)
        ct_btn.addStretch()
        ct_layout.addLayout(ct_btn)
        self.ct_group.setLayout(ct_layout)
        layout.addWidget(self.ct_group)

        # --- Padding (inline) ---
        pad_row = QHBoxLayout()
        pad_label = QLabel("Padding:")
        self.pad_combo = QComboBox()
        self.pad_combo.addItems(["PKCS#7", "None"])
        self.pad_combo.setMinimumWidth(160)
        pad_row.addWidget(pad_label)
        pad_row.addWidget(self.pad_combo)
        pad_row.addStretch()
        layout.addLayout(pad_row)

        # --- Run ---
        self.execute_btn = QPushButton("Decrypt")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setMinimumHeight(48)
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        layout.addWidget(self.execute_btn)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget

    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            if isinstance(widget, QTextEdit):
                widget.setPlainText(clipboard)
            else:
                widget.setText(clipboard)

    # ---------- Status tab ----------

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

        layout.addWidget(self.status_progress)
        layout.addWidget(self.status_output)
        return widget

    # ---------- Results tab ----------

    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        results_header = QHBoxLayout()
        results_label = QLabel("Plaintext:")
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
        layout.addWidget(self.results_output, 1)

        self.results_info = QLabel("")
        layout.addWidget(self.results_info)
        return widget

    # ---------- Execution ----------

    def _execute(self):
        key_hex = self.key_input.text().strip()
        if not key_hex:
            QMessageBox.warning(self, "Missing Input", "Please enter the AES key (hex).")
            return

        ct = self.ct_input.toPlainText().strip()
        if not ct:
            QMessageBox.warning(self, "Missing Input", "Please enter the ciphertext.")
            return

        padding = self.pad_combo.currentText() == "PKCS#7"

        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)

        self.worker = AESECBDecryptWorker(key_hex, ct, padding)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, msg):
        self.status_output.append(msg)

    def _on_finished(self, success, message, info):
        self.execute_btn.setEnabled(True)
        if success:
            self.status_output.append("\u2713 SUCCESS!")
            self.status_progress.setValue(100)
            self.results_output.setText(message)
            if info:
                parts = [
                    f"Mode: {info.get('mode', 'N/A')}",
                    f"Key: {info.get('key_bits', 'N/A')}-bit",
                    f"CT: {info.get('ct_bytes', 'N/A')} B",
                    f"PT: {info.get('pt_bytes', 'N/A')} B",
                ]
                self.results_info.setText(" | ".join(str(p) for p in parts))
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append("\u2717 FAILED")
            self.results_output.setText(message)

    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")

    # ---------- Theme ----------

    def _apply_theme(self):
        t = self.theme.current

        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)

        # NOTE: dropped `margin-top` and shrank vertical padding — the inner
        # layouts now carry the title clearance via setContentsMargins(top=24).
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};"
            f"border-radius:8px;padding:0px;font-weight:600;font-size:13px;}} "
            f"QGroupBox::title{{subcontrol-origin:margin;subcontrol-position:top left;"
            f"left:14px;padding:0 8px;color:{t['text']};background-color:transparent;}}"
        )
        for attr in ["key_group", "ct_group"]:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass

        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:14px;"
                        f"font-weight:700;font-size:15px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:14px;"
                        f"font-weight:700;font-size:15px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass

        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:13px;}}"
        )
        for attr in ["ct_input", "status_output"]:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(ts)
                except RuntimeError:
                    pass

        if hasattr(self, "results_output") and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;}}"
                )
            except RuntimeError:
                pass

        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        )
        if hasattr(self, "key_input") and self.key_input is not None:
            try:
                self.key_input.setStyleSheet(input_style)
            except RuntimeError:
                pass

        combo_style = (
            f"QComboBox{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}} "
            f"QComboBox::drop-down{{border:none;}} "
            f"QComboBox QAbstractItemView{{background-color:{t['base']};color:{t['text']};"
            f"selection-background-color:{t['surface0']};}}"
        )
        if hasattr(self, "pad_combo") and self.pad_combo is not None:
            try:
                self.pad_combo.setStyleSheet(combo_style)
            except RuntimeError:
                pass

        if hasattr(self, "status_progress") and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(
                    f"QProgressBar{{background-color:{t['surface0']};border:none;"
                    f"border-radius:4px;height:14px;text-align:center;"
                    f"font-size:10px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
                )
            except RuntimeError:
                pass

        if hasattr(self, "results_info") and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(
                    f"color:{t['text_secondary']};font-size:12px;"
                )
            except RuntimeError:
                pass

    def refresh_theme(self):
        self._apply_theme()