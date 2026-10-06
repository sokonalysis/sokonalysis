# gui/stego_visual_crypto_encrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QApplication,
    QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QImage
import os, sys, tempfile, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


class VisualCryptoEncryptWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str, str)
    
    def __init__(self, image_path, output_dir, encrypt_mode="image"):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.encrypt_mode = encrypt_mode
    
    def run(self):
        try:
            self.progress.emit("[*] Loading image...")
            self.progress_value.emit(10)
            
            # Load and convert to pure black & white
            img = Image.open(self.image_path).convert('L')
            # Threshold to pure black and white (no grayscale)
            img = img.point(lambda p: 255 if p > 128 else 0)
            img = img.convert('1')
            
            width, height = img.size
            self.progress.emit(f"[*] Image size: {width}x{height}")
            self.progress_value.emit(30)
            
            # Create shares with 2x2 subpixels per original pixel
            share1 = Image.new('1', (width * 2, height * 2), 0)
            share2 = Image.new('1', (width * 2, height * 2), 0)
            
            self.progress.emit("[*] Generating visual crypto shares...")
            self.progress_value.emit(50)
            
            pixels = img.load()
            s1_pixels = share1.load()
            s2_pixels = share2.load()
            
            # Proper (2,2) visual cryptography scheme
            # Each original pixel becomes a 2x2 block
            # For each pixel, randomly choose one of the 6 possible 2x2 patterns with 2 black subpixels
            patterns_2black = [
                [[1, 1], [0, 0]],  # top row black
                [[0, 0], [1, 1]],  # bottom row black
                [[1, 0], [1, 0]],  # left column black
                [[0, 1], [0, 1]],  # right column black
                [[1, 0], [0, 1]],  # diagonal \
                [[0, 1], [1, 0]],  # diagonal /
            ]
            
            for y in range(height):
                for x in range(width):
                    pixel = pixels[x, y]
                    base_x, base_y = x * 2, y * 2
                    
                    # Share 1 always gets a random pattern
                    pattern1 = random.choice(patterns_2black)
                    
                    if pixel == 255:  # White pixel - shares must be identical
                        pattern2 = pattern1
                    else:  # Black pixel - shares must be complementary
                        # For black, share 2 gets the inverse of share 1
                        pattern2 = [[1 - pattern1[0][0], 1 - pattern1[0][1]],
                                   [1 - pattern1[1][0], 1 - pattern1[1][1]]]
                    
                    for dy in range(2):
                        for dx in range(2):
                            s1_pixels[base_x + dx, base_y + dy] = pattern1[dy][dx] * 255
                            s2_pixels[base_x + dx, base_y + dy] = pattern2[dy][dx] * 255
                
                if y % 10 == 0:
                    progress = 50 + int((y * width) / (width * height) * 40)
                    self.progress_value.emit(progress)
            
            self.progress_value.emit(90)
            self.progress.emit("[*] Saving shares...")
            
            # Get base filename without extension
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            share1_path = os.path.join(self.output_dir, f"{base_name}_share1.png")
            share2_path = os.path.join(self.output_dir, f"{base_name}_share2.png")
            share1.save(share1_path)
            share2.save(share2_path)
            
            self.progress_value.emit(100)
            self.progress.emit("[✓] Shares generated!")
            
            result = (f"Visual Cryptography Shares Generated\n\n"
                     f"Original: {width}x{height}\n"
                     f"Shares: {width*2}x{height*2}\n\n"
                     f"Share 1: {share1_path}\n"
                     f"Share 2: {share2_path}\n\n"
                     f"Each share is random noise.\n"
                     f"Overlay both to reveal the image.")
            
            self.finished.emit(True, result, share1_path, share2_path)
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "", "")


class StegoVisualCryptoEncryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.share1_path = ""
        self.share2_path = ""
        self.image_path = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.image_path = filepath
                self.img_input.setText(filepath)
                self._update_image_preview()
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
        
        title = QLabel("Visual Cryptography - Encrypt")
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
        for attr in ['img_grp', 'options_grp']:
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
        for attr in ['img_input', 'out_input']:
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
        if hasattr(self, 'img_preview') and self.img_preview is not None:
            self.img_preview.setStyleSheet(preview_style)
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.img_grp = QGroupBox("1. Source Image")
        il = QVBoxLayout()
        
        self.img_preview = QLabel()
        self.img_preview.setFixedHeight(150)
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setText("Drag & drop or click Browse\nto select a black & white image")
        il.addWidget(self.img_preview)
        
        img_row = QHBoxLayout()
        self.img_input = QLineEdit()
        self.img_input.setReadOnly(True)
        self.img_input.setPlaceholderText("Select image file (PNG, JPG, BMP)...")
        img_row.addWidget(self.img_input, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_image)
        img_row.addWidget(browse_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_image)
        img_row.addWidget(clear_btn)
        il.addLayout(img_row)
        
        self.img_info = QLabel("")
        il.addWidget(self.img_info)
        
        self.img_grp.setLayout(il)
        l.addWidget(self.img_grp)
        
        self.options_grp = QGroupBox("2. Output")
        ol = QVBoxLayout()
        ol.setSpacing(10)
        
        out_row = QHBoxLayout()
        self.out_input = QLineEdit()
        self.out_input.setReadOnly(True)
        self.out_input.setPlaceholderText("Select output directory for shares...")
        out_row.addWidget(self.out_input, 1)
        out_browse = QPushButton("Browse")
        out_browse.setObjectName("actionButton")
        out_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(out_browse)
        ol.addWidget(QLabel("Output Directory:"))
        ol.addLayout(out_row)
        
        self.options_grp.setLayout(ol)
        l.addWidget(self.options_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.enc_btn = QPushButton("Generate Shares")
        self.enc_btn.setObjectName("actionButton")
        self.enc_btn.setMinimumHeight(48)
        self.enc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enc_btn.clicked.connect(self._encrypt)
        br.addWidget(self.enc_btn)
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
        
        results_header = QHBoxLayout()
        results_label = QLabel("Generated Shares (each is random noise):")
        export_btn = QPushButton("Export Shares")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_shares)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(export_btn)
        l.addLayout(results_header)
        
        shares_row = QHBoxLayout()
        shares_row.setSpacing(12)
        
        s1_container = QVBoxLayout()
        s1_label = QLabel("Share 1")
        s1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s1_preview = QLabel()
        self.s1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s1_preview.setMinimumSize(1, 1)
        self.s1_preview.setText("Share 1")
        s1_container.addWidget(s1_label)
        s1_container.addWidget(self.s1_preview, 1)
        shares_row.addLayout(s1_container, 1)
        
        s2_container = QVBoxLayout()
        s2_label = QLabel("Share 2")
        s2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s2_preview = QLabel()
        self.s2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s2_preview.setMinimumSize(1, 1)
        self.s2_preview.setText("Share 2")
        s2_container.addWidget(s2_label)
        s2_container.addWidget(self.s2_preview, 1)
        shares_row.addLayout(s2_container, 1)
        
        l.addLayout(shares_row, 1)
        
        self.result_info = QLabel("")
        self.result_info.setWordWrap(True)
        self.result_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.result_info)
        
        return w
    
    def _browse_image(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if fp:
            self.image_path = fp
            self.img_input.setText(fp)
            self._update_image_preview()
    
    def _clear_image(self):
        self.image_path = ""
        self.img_input.clear()
        self.img_preview.setText("Drag & drop or click Browse\nto select a black & white image")
        self.img_info.setText("")
    
    def _update_image_preview(self):
        if self.image_path and os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                self.img_preview.setPixmap(pixmap.scaledToHeight(140, Qt.TransformationMode.SmoothTransformation))
                size = os.path.getsize(self.image_path)
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                self.img_info.setText(f"Size: {size_str}")
    
    def _browse_output(self):
        dp = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dp:
            self.out_input.setText(dp)
    
    def _encrypt(self):
        if not self.image_path:
            QMessageBox.warning(self, "Missing Input", "Please select an image to encrypt.")
            return
        
        out_dir = self.out_input.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Missing Output", "Please select an output directory.")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.enc_btn.setEnabled(False)
        
        self.worker = VisualCryptoEncryptWorker(self.image_path, out_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
    
    def _on_finished(self, success, message, s1_path, s2_path):
        self.enc_btn.setEnabled(True)
        if success:
            self.share1_path = s1_path
            self.share2_path = s2_path
            self.status_progress.setValue(100)
            
            if os.path.exists(self.share1_path):
                pixmap1 = QPixmap(self.share1_path)
                if not pixmap1.isNull():
                    self.s1_preview.setPixmap(pixmap1.scaled(
                        self.s1_preview.width(), self.s1_preview.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
            
            if os.path.exists(self.share2_path):
                pixmap2 = QPixmap(self.share2_path)
                if not pixmap2.isNull():
                    self.s2_preview.setPixmap(pixmap2.scaled(
                        self.s2_preview.width(), self.s2_preview.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
            
            self.result_info.setText(message)
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"ERROR: {message}")
    
    def _export_shares(self):
        if not self.share1_path or not os.path.exists(self.share1_path):
            QMessageBox.warning(self, "No Shares", "No shares to export. Generate shares first.")
            return
        
        export_dir = QFileDialog.getExistingDirectory(self, "Export Shares To")
        if export_dir:
            try:
                import shutil
                base_name = os.path.splitext(os.path.basename(self.image_path))[0]
                shutil.copy2(self.share1_path, os.path.join(export_dir, f"{base_name}_share1.png"))
                shutil.copy2(self.share2_path, os.path.join(export_dir, f"{base_name}_share2.png"))
                QMessageBox.information(self, "Exported", f"Shares saved to:\n{export_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()