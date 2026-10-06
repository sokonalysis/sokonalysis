# gui/ctf_pigpen_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QScrollArea,
    QFrame, QApplication, QGridLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
import os
import sys


PIGPEN_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class ClickableSymbolLabel(QLabel):
    """Click a symbol to add its letter to the decoded text."""
    def __init__(self, letter, parent_page):
        super().__init__()
        self.letter = letter
        self.parent_page = parent_page
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip(f"Click to add '{letter}'")
        self.setStyleSheet("""
            QLabel {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel:hover {
                border: 1px solid rgba(128, 128, 128, 60);
                background: rgba(128, 128, 128, 15);
            }
        """)
    
    def mousePressEvent(self, event):
        current = self.parent_page.ciphertext_input.toPlainText()
        self.parent_page.ciphertext_input.setPlainText(current + self.letter)


class PigpenDecryptPage(QWidget):
    """Pigpen Cipher Decrypt page with image upload and symbol clicking."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.symbols_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'symbols', 'pigpen'
        )
        self.image_path = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath:
                self.image_path = filepath
                self.image_path_input.setText(filepath)
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
        
        title = QLabel("Pigpen Decrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_results_tab(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
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
        
        # Step 1: Image upload with drag & drop preview
        self.image_group = QGroupBox("1. Upload Image with Pigpen Symbols")
        image_layout = QVBoxLayout()
        
        self.image_preview = QLabel()
        self.image_preview.setFixedHeight(150)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setText("Drag & drop an image here\nor click Browse to select")
        image_layout.addWidget(self.image_preview)
        
        img_row = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setReadOnly(True)
        self.image_path_input.setPlaceholderText("Select image file (jpg, png, bmp)...")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_image)
        img_row.addWidget(self.image_path_input, 1)
        img_row.addWidget(browse_btn)
        image_layout.addLayout(img_row)
        
        self.image_info = QLabel("")
        image_layout.addWidget(self.image_info)
        self.image_group.setLayout(image_layout)
        layout.addWidget(self.image_group)
        
        # Step 2: Symbol reference (clickable)
        self.symbols_group = QGroupBox("2. Click Symbols in Order (as they appear in the image)")
        symbols_layout = QGridLayout()
        symbols_layout.setSpacing(6)
        
        # Row 1: A-M (letters on top)
        for i, letter in enumerate('ABCDEFGHIJKLM'):
            col = i
            letter_lbl = QLabel(letter)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_lbl.setStyleSheet(f"font-weight:700; font-size:13px; color:{self.theme.current['text']}; background:transparent;")
            symbols_layout.addWidget(letter_lbl, 0, col)
            
            img_path = os.path.join(self.symbols_dir, f"{letter}.png")
            symbol = ClickableSymbolLabel(letter, self)
            symbol.setFixedSize(56, 56)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                symbol.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                symbol.setText(letter)
            symbols_layout.addWidget(symbol, 1, col)
        
        # Row 2: N-Z (symbols on top)
        for i, letter in enumerate('NOPQRSTUVWXYZ'):
            col = i
            img_path = os.path.join(self.symbols_dir, f"{letter}.png")
            symbol = ClickableSymbolLabel(letter, self)
            symbol.setFixedSize(56, 56)
            if os.path.exists(img_path):
                pixmap = QPixmap(img_path)
                symbol.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                symbol.setText(letter)
            symbols_layout.addWidget(symbol, 2, col)
            
            letter_lbl = QLabel(letter)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            letter_lbl.setStyleSheet(f"font-weight:700; font-size:13px; color:{self.theme.current['text']}; background:transparent;")
            symbols_layout.addWidget(letter_lbl, 3, col)
        
        self.symbols_group.setLayout(symbols_layout)
        layout.addWidget(self.symbols_group)
        
        # Step 3: Ciphertext (decoded letters)
        self.input_group = QGroupBox("3. Decoded Letters (click symbols above)")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        
        self.ciphertext_input = QTextEdit()
        self.ciphertext_input.setPlaceholderText("Click the symbols above in the order they appear in the image...")
        self.ciphertext_input.setMinimumHeight(80)
        self.ciphertext_input.setMaximumHeight(120)
        input_layout.addWidget(self.ciphertext_input)
        
        btn_row = QHBoxLayout()
        space_btn = QPushButton("Add Space")
        space_btn.setObjectName("actionButton")
        space_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        space_btn.clicked.connect(lambda: self.ciphertext_input.setPlainText(self.ciphertext_input.toPlainText() + ' '))
        
        undo_btn = QPushButton("Undo")
        undo_btn.setObjectName("actionButton")
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.clicked.connect(lambda: self.ciphertext_input.setPlainText(self.ciphertext_input.toPlainText()[:-1]))
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.ciphertext_input.clear)
        
        btn_row.addWidget(space_btn)
        btn_row.addWidget(undo_btn)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        input_layout.addLayout(btn_row)
        self.input_group.setLayout(input_layout)
        layout.addWidget(self.input_group)
        
        # Decrypt button
        self.execute_btn = QPushButton("Show Decrypted Text")
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
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Decrypted Output:")
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
        self.results_output.setPlaceholderText("Decrypted text will appear here...")
        layout.addWidget(self.results_output, 1)
        
        self.results_info = QLabel("")
        layout.addWidget(self.results_info)
        return widget
    
    def _browse_image(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if fp:
            self.image_path = fp
            self.image_path_input.setText(fp)
            self._update_image_preview()
    
    def _update_image_preview(self):
        if not self.image_path or not os.path.exists(self.image_path):
            self.image_preview.setText("Drag & drop an image here\nor click Browse to select")
            self.image_info.setText("")
            return
        
        fn = os.path.basename(self.image_path)
        sz = os.path.getsize(self.image_path)
        ss = f"{sz} B" if sz < 1024 else f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"
        
        pm = QPixmap(self.image_path)
        if not pm.isNull():
            self.image_preview.setPixmap(pm.scaledToHeight(140, Qt.TransformationMode.SmoothTransformation))
        else:
            self.image_preview.setText(f"Image File\n{fn}")
        
        self.image_info.setText(f"File: {fn} | Size: {ss}")
    
    def _execute(self):
        ciphertext = self.ciphertext_input.toPlainText().strip()
        if not ciphertext:
            QMessageBox.warning(self, "No Input", "Please click symbols to build the ciphertext.")
            return
        
        self.results_output.setText(ciphertext.upper())
        self.results_info.setText(f"Decoded {len(ciphertext)} characters")
        self.tabs.setCurrentIndex(1)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['image_group', 'symbols_group', 'input_group']:
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
        
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        if hasattr(self, 'ciphertext_input') and self.ciphertext_input is not None:
            try:
                self.ciphertext_input.setStyleSheet(ts)
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;}}")
            except RuntimeError:
                pass
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        if hasattr(self, 'image_path_input') and self.image_path_input is not None:
            try:
                self.image_path_input.setStyleSheet(input_style)
            except RuntimeError:
                pass
        
        if hasattr(self, 'image_preview') and self.image_preview is not None:
            self.image_preview.setStyleSheet(f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;")
        
        if hasattr(self, 'image_info') and self.image_info is not None:
            self.image_info.setStyleSheet(f"color:{t['text_tertiary']};font-size:11px;background:transparent;")
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()