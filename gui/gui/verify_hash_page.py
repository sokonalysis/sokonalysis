# gui/verify_hash_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QProgressBar, QFileDialog, QFrame,
    QApplication, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QDrag, QPainter
import hashlib
import os
import sys
from gui.layout_manager import layout_manager


class DraggableAlgoCard(QFrame):
    def __init__(self, algo_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.algo_id = algo_id
        self.algo_name = name
        self.colors = theme_colors
        self.name_label = None
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(110, int(140 * scale))
        h = max(50, int(60 * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(30 * scale), h + int(16 * scale))
    
    def _build(self):
        t = self.colors
        scale = layout_manager.font_scale()
        if self.name_label is None:
            l = QVBoxLayout(self)
            l.setContentsMargins(
                int(10 * scale), int(10 * scale),
                int(10 * scale), int(10 * scale)
            )
            l.setSpacing(int(2 * scale))
            self.name_label = QLabel(self.algo_name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            l.addWidget(self.name_label)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(12 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        self._build()
        self.update()
        self.repaint()
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(e)
    
    def mouseReleaseEvent(self, e):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(e)
    
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"{self.algo_id}:{self.algo_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class AlgoDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.algo_id = None
        self.algo_name = None
        self._placeholder = "Drag algorithm here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(180, text_w)
        max_w = min_w + int(80 * scale)
        h = max(64, int(80 * scale))
        self.setMinimumSize(min_w, h)
        self.setMaximumSize(max_w, h + int(20 * scale))
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}"
        )
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}"
        )
    
    def is_filled(self):
        return self.algo_id is not None
    
    def clear_slot(self):
        self.algo_id = None
        self.algo_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    
    def dropEvent(self, e):
        data = e.mimeData().text()
        try:
            aid, an = data.split(':', 1)
            self.algo_id = aid
            self.algo_name = an
            self._style_filled()
            self.update()
            self.repaint()
            e.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, VerifyHashPage):
                p = p.parent()
            if p:
                p._on_algo_dropped()
        except:
            pass
    
    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(11, int(13 * scale))
            p.setPen(QColor(t['accent']))
            p.setFont(QFont("JetBrains Mono", font_size, QFont.Weight.Bold))
            text = self.algo_name
        else:
            font_size = max(9, int(10 * scale))
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", font_size))
            text = self._placeholder
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = p.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.clear_slot()
        p = self.parent()
        while p and not isinstance(p, VerifyHashPage):
            p = p.parent()
        if p:
            p._on_algo_cleared()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class HashVerifyWorker(QThread):
    """Worker for computing file hashes."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, filepath, algo):
        super().__init__()
        self.filepath = filepath
        self.algo = algo
    
    def run(self):
        try:
            file_size = os.path.getsize(self.filepath)
            self.progress.emit(f"File: {os.path.basename(self.filepath)} ({self._format_size(file_size)})")
            self.progress_value.emit(10)
            
            hash_func = getattr(hashlib, self.algo)()
            
            with open(self.filepath, 'rb') as f:
                chunk_size = 8192
                total_read = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hash_func.update(chunk)
                    total_read += len(chunk)
                    pct = 10 + int((total_read / file_size) * 80)
                    self.progress_value.emit(pct)
            
            result = hash_func.hexdigest()
            self.progress.emit("Hash computed")
            self.progress_value.emit(100)
            self.finished.emit(True, result)
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class VerifyHashPage(QWidget):
    """File integrity verification page with drag & drop."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.computed_hash = ""
        self.algo_cards = []
        self._init_ui()
        self.setAcceptDrops(True)
    
    def _paste_to(self, widget):
        c = QApplication.clipboard().text()
        if c:
            widget.setText(c.strip())
    
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
        
        title = QLabel("Verify File Integrity")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['algo_grp', 'file_group', 'expected_group', 'result_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'file_path') and self.file_path is not None:
            try:
                self.file_path.setStyleSheet(
                    f"QLineEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
                    f"font-size:{max(12, int(13 * scale))}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'expected_hash') and self.expected_hash is not None:
            try:
                self.expected_hash.setStyleSheet(
                    f"QLineEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px 14px;"
                    f"font-family:JetBrains Mono;font-size:{max(12, int(14 * scale))}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(
                    f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'drop_label') and self.drop_label is not None:
            try:
                self.drop_label.setStyleSheet(
                    f"border:2px dashed {t['border']};border-radius:12px;"
                    f"padding:{int(30 * scale)}px;color:{t['text_tertiary']};"
                    f"font-size:{int(13 * scale)}px;background:transparent;"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'file_preview') and self.file_preview is not None:
            try:
                self.file_preview.setStyleSheet(
                    f"color:{t['text_secondary']};font-size:{int(11 * scale)}px;"
                    f"background:transparent;padding:4px 0;"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'match_icon') and self.match_icon is not None:
            try:
                self.match_icon.setStyleSheet("background:transparent;")
            except RuntimeError:
                pass
        
        if hasattr(self, 'match_text') and self.match_text is not None:
            try:
                self.match_text.setStyleSheet(
                    f"font-size:{int(18 * scale)}px;font-weight:800;background:transparent;"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'algo_slot') and self.algo_slot is not None:
            self.algo_slot.update_colors(t)
        for card in self.algo_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
    
    def _on_algo_dropped(self):
        self.file_group.setVisible(True)
        self.expected_group.setVisible(True)
        self.verify_btn.setVisible(True)
    
    def _on_algo_cleared(self):
        self.file_group.setVisible(False)
        self.expected_group.setVisible(False)
        self.verify_btn.setVisible(False)
    
    def _create_setup_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.algo_grp = QGroupBox("1. Algorithm (Drag & Drop)")
        al = QVBoxLayout()
        al.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(10)
        t = self.theme.current
        for aid, an in [
            ("md5", "MD5"), ("sha1", "SHA-1"), ("sha224", "SHA-224"),
            ("sha256", "SHA-256"), ("sha384", "SHA-384"), ("sha512", "SHA-512")
        ]:
            card = DraggableAlgoCard(aid, an, t)
            self.algo_cards.append(card)
            cr.addWidget(card)
        cr.addStretch()
        al.addLayout(cr)
        dr = QHBoxLayout()
        self.algo_slot = AlgoDropSlot(t)
        dr.addWidget(self.algo_slot)
        dr.addStretch()
        al.addLayout(dr)
        self.algo_grp.setLayout(al)
        l.addWidget(self.algo_grp)
        
        self.file_group = QGroupBox("2. Select File")
        self.file_group.setVisible(False)
        fl = QVBoxLayout()
        self.drop_label = QLabel("Drag & drop a file here\nor click Browse to select")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setMinimumHeight(80)
        fl.addWidget(self.drop_label)
        self.file_preview = QLabel("")
        self.file_preview.setWordWrap(True)
        self.file_preview.hide()
        fl.addWidget(self.file_preview)
        fr = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("No file selected...")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_file)
        fr.addWidget(self.file_path)
        fr.addWidget(browse_btn)
        fl.addLayout(fr)
        self.file_group.setLayout(fl)
        l.addWidget(self.file_group)
        
        self.expected_group = QGroupBox("3. Expected Hash (optional)")
        self.expected_group.setVisible(False)
        el = QVBoxLayout()
        self.expected_hash = QLineEdit()
        self.expected_hash.setPlaceholderText("Paste expected hash to verify, or leave empty to just calculate...")
        self.expected_hash.setMinimumHeight(44)
        el.addWidget(self.expected_hash)
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.expected_hash))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.expected_hash.clear)
        btn_row = QHBoxLayout()
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        el.addLayout(btn_row)
        self.expected_group.setLayout(el)
        l.addWidget(self.expected_group)
        
        self.verify_btn = QPushButton("Calculate Hash")
        self.verify_btn.setObjectName("actionButton")
        self.verify_btn.setMinimumHeight(48)
        self.verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.verify_btn.clicked.connect(self._verify)
        self.verify_btn.setVisible(False)
        l.addWidget(self.verify_btn)
        l.addStretch()
        
        scroll.setWidget(content)
        
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return w
    
    def _create_status_tab(self):
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
    
    def _create_results_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        match_row = QHBoxLayout()
        match_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        match_row.setSpacing(12)
        
        self.match_icon = QLabel()
        self.match_icon.setFixedSize(48, 48)
        self.match_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_icon.hide()
        
        self.match_text = QLabel("")
        self.match_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.match_text.setWordWrap(True)
        
        match_row.addWidget(self.match_icon)
        match_row.addWidget(self.match_text)
        l.addLayout(match_row)
        
        self.result_group = QGroupBox("Result")
        rl = QVBoxLayout()
        
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Computed Hash:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Computed hash will appear here...")
        rl.addWidget(self.results_output, 1)
        self.result_group.setLayout(rl)
        l.addWidget(self.result_group, 1)
        return w
    
    def _copy_result(self):
        text = self.results_output.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Hash copied to clipboard!")
    
    def _update_file_preview(self, filepath):
        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            elif size < 1073741824:
                size_str = f"{size/1048576:.1f} MB"
            else:
                size_str = f"{size/1073741824:.1f} GB"
            
            self.file_preview.setText(f"{os.path.basename(filepath)} -- {size_str}")
            self.file_preview.show()
            self.drop_label.hide()
        else:
            self.file_preview.hide()
            self.drop_label.show()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp and os.path.isfile(fp):
                self.file_path.setText(fp)
                self._update_file_preview(fp)
                break
    
    def _browse_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if fp:
            self.file_path.setText(fp)
            self._update_file_preview(fp)
    
    def _verify(self):
        filepath = self.file_path.text().strip()
        
        if not filepath:
            QMessageBox.warning(self, "No File", "Please select a file.")
            return
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "File Not Found", "Selected file does not exist.")
            return
        if not self.algo_slot.is_filled():
            QMessageBox.warning(self, "No Algorithm", "Please drag an algorithm first.")
            return
        
        algo = self.algo_slot.algo_id
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.match_icon.hide()
        self.match_text.clear()
        self.status_progress.setValue(0)
        
        self.worker = HashVerifyWorker(filepath, algo)
        self.worker.progress.connect(lambda m: self.status_output.append(m))
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_finished(self, success, result):
        if success:
            self.computed_hash = result
            self.results_output.setText(result)
            self.tabs.setCurrentIndex(2)
            
            expected = self.expected_hash.text().strip().lower()
            if expected:
                icons_dir = os.path.join(
                    sys._MEIPASS if hasattr(sys, '_MEIPASS')
                    else os.path.join(os.path.dirname(__file__), '..'),
                    'assets', 'icons'
                )
                t = self.theme.current
                scale = layout_manager.font_scale()
                icon_sz = max(36, int(48 * scale))
                
                if result.lower() == expected:
                    yes_path = os.path.join(icons_dir, "yes.png")
                    if os.path.exists(yes_path):
                        self.match_icon.setPixmap(
                            QPixmap(yes_path).scaled(
                                icon_sz, icon_sz,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        )
                    self.match_text.setText("MATCH - File integrity verified!")
                    self.match_text.setStyleSheet(
                        f"color:{t['success']};font-size:{int(18 * scale)}px;"
                        f"font-weight:800;background:transparent;"
                    )
                else:
                    no_path = os.path.join(icons_dir, "no.png")
                    if os.path.exists(no_path):
                        self.match_icon.setPixmap(
                            QPixmap(no_path).scaled(
                                icon_sz, icon_sz,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                        )
                    self.match_text.setText("NO MATCH - File may be corrupted!")
                    self.match_text.setStyleSheet(
                        f"color:{t['error']};font-size:{int(18 * scale)}px;"
                        f"font-weight:800;background:transparent;"
                    )
                
                self.match_icon.show()
        else:
            self.results_output.setText(f"Error: {result}")
            self.tabs.setCurrentIndex(2)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()