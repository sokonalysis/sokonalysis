# gui/stego_visual_crypto_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QApplication
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
import os, sys, tempfile
import numpy as np
from PIL import Image


class VisualCryptoDecryptWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str)
    
    def __init__(self, share1_path, share2_path):
        super().__init__()
        self.share1_path = share1_path
        self.share2_path = share2_path
    
    def run(self):
        try:
            self.progress.emit("[*] Loading shares...")
            self.progress_value.emit(20)
            
            im1 = Image.open(self.share1_path)
            im2 = Image.open(self.share2_path)
            
            if im1.size != im2.size:
                self.finished.emit(False, "Shares must have the same dimensions!", "")
                return
            
            self.progress.emit("[*] Combining shares using NumPy addition...")
            self.progress_value.emit(50)
            
            im1np = np.array(im1)
            im2np = np.array(im2)
            result = im2np + im1np
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            self.progress_value.emit(80)
            self.progress.emit("[*] Saving result...")
            
            output_path = os.path.join(tempfile.gettempdir(), "visual_crypto_decrypted.png")
            Image.fromarray(result).save(output_path)
            
            self.progress_value.emit(100)
            self.progress.emit("[✓] Decryption complete!")
            
            self.finished.emit(True, f"Decrypted image saved to:\n{output_path}", output_path)
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "")


class StegoVisualCryptoDecryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.share1_path = ""
        self.share2_path = ""
        self.last_output = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and filepath.lower().endswith('.png'):
                if not self.share1_path:
                    self.share1_path = filepath
                    self.s1_input.setText(filepath)
                    self._update_share1_preview()
                elif not self.share2_path:
                    self.share2_path = filepath
                    self.s2_input.setText(filepath)
                    self._update_share2_preview()
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Visual Cryptography - Decrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['share1_grp', 'share2_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
            except RuntimeError:
                pass
        
        input_style = f"QLineEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['s1_input', 's2_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:13px;}}")
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}")
        
        preview_style = f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;"
        if hasattr(self, 's1_preview') and self.s1_preview is not None:
            self.s1_preview.setStyleSheet(preview_style)
        if hasattr(self, 's2_preview') and self.s2_preview is not None:
            self.s2_preview.setStyleSheet(preview_style)
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.share1_grp = QGroupBox("1. Share 1")
        s1_layout = QVBoxLayout()
        self.s1_preview = QLabel()
        self.s1_preview.setFixedHeight(100)
        self.s1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s1_preview.setText("Drag & drop or click Browse\nto select share 1")
        s1_layout.addWidget(self.s1_preview)
        s1_row = QHBoxLayout()
        self.s1_input = QLineEdit()
        self.s1_input.setReadOnly(True)
        self.s1_input.setPlaceholderText("Select share 1...")
        s1_row.addWidget(self.s1_input, 1)
        s1_browse = QPushButton("Browse")
        s1_browse.setObjectName("actionButton")
        s1_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        s1_browse.clicked.connect(lambda: self._browse_share(1))
        s1_row.addWidget(s1_browse)
        s1_clear = QPushButton("Clear")
        s1_clear.setObjectName("dangerButton")
        s1_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        s1_clear.clicked.connect(lambda: self._clear_share(1))
        s1_row.addWidget(s1_clear)
        s1_layout.addLayout(s1_row)
        self.share1_grp.setLayout(s1_layout)
        l.addWidget(self.share1_grp)
        
        self.share2_grp = QGroupBox("2. Share 2")
        s2_layout = QVBoxLayout()
        self.s2_preview = QLabel()
        self.s2_preview.setFixedHeight(100)
        self.s2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s2_preview.setText("Drag & drop or click Browse\nto select share 2")
        s2_layout.addWidget(self.s2_preview)
        s2_row = QHBoxLayout()
        self.s2_input = QLineEdit()
        self.s2_input.setReadOnly(True)
        self.s2_input.setPlaceholderText("Select share 2...")
        s2_row.addWidget(self.s2_input, 1)
        s2_browse = QPushButton("Browse")
        s2_browse.setObjectName("actionButton")
        s2_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        s2_browse.clicked.connect(lambda: self._browse_share(2))
        s2_row.addWidget(s2_browse)
        s2_clear = QPushButton("Clear")
        s2_clear.setObjectName("dangerButton")
        s2_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        s2_clear.clicked.connect(lambda: self._clear_share(2))
        s2_row.addWidget(s2_clear)
        s2_layout.addLayout(s2_row)
        self.share2_grp.setLayout(s2_layout)
        l.addWidget(self.share2_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.dec_btn = QPushButton("Overlay Shares")
        self.dec_btn.setObjectName("actionButton")
        self.dec_btn.setMinimumHeight(48)
        self.dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dec_btn.clicked.connect(self._decrypt)
        br.addWidget(self.dec_btn)
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        # Header with export button
        results_header = QHBoxLayout()
        results_label = QLabel("Result:")
        export_btn = QPushButton("Export Image")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_result)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(export_btn)
        l.addLayout(results_header)
        
        # Image preview filling all remaining space
        self.result_preview = QLabel()
        self.result_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_preview.setText("Decrypted image will appear here")
        self.result_preview.setScaledContents(False)
        self.result_preview.setMinimumSize(1, 1)
        l.addWidget(self.result_preview, 1)  # stretch factor 1 = fill all space
        
        # Size info at bottom
        self.result_info = QLabel("")
        self.result_info.setWordWrap(True)
        self.result_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.result_info)
        
        return w
    
    def _browse_share(self, num):
        fp, _ = QFileDialog.getOpenFileName(self, f"Select Share {num}", "", "Images (*.png);;All Files (*)")
        if fp:
            if num == 1:
                self.share1_path = fp
                self.s1_input.setText(fp)
                self._update_share1_preview()
            else:
                self.share2_path = fp
                self.s2_input.setText(fp)
                self._update_share2_preview()
    
    def _clear_share(self, num):
        if num == 1:
            self.share1_path = ""
            self.s1_input.clear()
            self.s1_preview.setText("Drag & drop or click Browse\nto select share 1")
        else:
            self.share2_path = ""
            self.s2_input.clear()
            self.s2_preview.setText("Drag & drop or click Browse\nto select share 2")
    
    def _update_share1_preview(self):
        if self.share1_path and os.path.exists(self.share1_path):
            pixmap = QPixmap(self.share1_path)
            if not pixmap.isNull():
                self.s1_preview.setPixmap(pixmap.scaledToHeight(90, Qt.TransformationMode.SmoothTransformation))
    
    def _update_share2_preview(self):
        if self.share2_path and os.path.exists(self.share2_path):
            pixmap = QPixmap(self.share2_path)
            if not pixmap.isNull():
                self.s2_preview.setPixmap(pixmap.scaledToHeight(90, Qt.TransformationMode.SmoothTransformation))
    
    def _decrypt(self):
        if not self.share1_path or not self.share2_path:
            QMessageBox.warning(self, "Missing Input", "Please select both shares.")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.dec_btn.setEnabled(False)
        
        self.worker = VisualCryptoDecryptWorker(self.share1_path, self.share2_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
    
    def _on_finished(self, success, message, output_path):
        self.dec_btn.setEnabled(True)
        if success:
            self.last_output = output_path
            self.status_progress.setValue(100)
            if os.path.exists(self.last_output):
                pixmap = QPixmap(self.last_output)
                if not pixmap.isNull():
                    # Scale to fit the available space while keeping aspect ratio
                    self.result_preview.setPixmap(pixmap.scaled(
                        self.result_preview.width(),
                        self.result_preview.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                size = os.path.getsize(self.last_output)
                self.result_info.setText(f"Size: {size/1024:.1f} KB")
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR: {message}")
    
    def _export_result(self):
        if not self.last_output or not os.path.exists(self.last_output):
            QMessageBox.warning(self, "No Result", "No decrypted image to export.")
            return
        export_path, _ = QFileDialog.getSaveFileName(
            self, "Export Decrypted Image", "decrypted.png",
            "PNG Images (*.png)"
        )
        if export_path:
            try:
                import shutil
                shutil.copy2(self.last_output, export_path)
                QMessageBox.information(self, "Exported", f"Saved to:\n{export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()