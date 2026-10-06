# gui/sha_generate.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QFrame,
    QMessageBox, QProgressBar, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import hashlib
import os
import sys
from gui.layout_manager import layout_manager


class DraggableSHACard(QFrame):
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
        # Floor so "SHA-256" label is never clipped
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


class SHADropSlot(QFrame):
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
            while p and not isinstance(p, SHAGeneratePage):
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
        while p and not isinstance(p, SHAGeneratePage):
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


class SHAGeneratePage(QWidget):
    """SHA hash generator with drag-and-drop algorithm."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.algo_cards = []
        self._init_ui()
    
    def _paste_to(self, widget):
        c = QApplication.clipboard().text()
        if c:
            widget.setPlainText(c.strip())
    
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
        
        title = QLabel("SHA Hash - Generate")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        
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
        for attr in ['algo_grp', 'in_grp', 'res_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'gen_input') and self.gen_input is not None:
            try:
                self.gen_input.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'gen_progress') and self.gen_progress is not None:
            try:
                self.gen_progress.setStyleSheet(
                    f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
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
        self.in_grp.setVisible(True)
    
    def _on_algo_cleared(self):
        self.in_grp.setVisible(False)
    
    def _tab_setup(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.algo_grp = QGroupBox("1. Algorithm (Drag & Drop)")
        al = QVBoxLayout()
        al.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(10)
        t = self.theme.current
        for aid, an in [
            ("sha1", "SHA-1"), ("sha224", "SHA-224"),
            ("sha256", "SHA-256"), ("sha384", "SHA-384"), ("sha512", "SHA-512")
        ]:
            card = DraggableSHACard(aid, an, t)
            self.algo_cards.append(card)
            cr.addWidget(card)
        cr.addStretch()
        al.addLayout(cr)
        dr = QHBoxLayout()
        self.algo_slot = SHADropSlot(t)
        dr.addWidget(self.algo_slot)
        dr.addStretch()
        al.addLayout(dr)
        self.algo_grp.setLayout(al)
        l.addWidget(self.algo_grp)
        
        self.in_grp = QGroupBox("2. Input Text")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        il.setSpacing(10)
        self.gen_input = QTextEdit()
        self.gen_input.setPlaceholderText("Enter text to generate SHA hash...")
        self.gen_input.setMaximumHeight(100)
        self.gen_input.setMinimumHeight(80)
        il.addWidget(self.gen_input)
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.gen_input))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.gen_input.clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        il.addLayout(btn_row)
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        gen_btn = QPushButton("Generate SHA Hash")
        gen_btn.setObjectName("actionButton")
        gen_btn.setMinimumHeight(48)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(self._generate_hash)
        l.addWidget(gen_btn)
        l.addStretch()
        return w
    
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.gen_progress = QProgressBar()
        self.gen_progress.setRange(0, 100)
        self.gen_progress.setValue(0)
        self.gen_progress.setTextVisible(True)
        self.gen_progress.setFormat("%p%")
        self.gen_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        
        l.addWidget(self.gen_progress)
        l.addWidget(self.status_output)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.res_grp = QGroupBox("Result")
        rl = QVBoxLayout()
        
        rh = QHBoxLayout()
        rh.addWidget(QLabel("SHA Hash:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Generated SHA hash will appear here...")
        rl.addWidget(self.results_output, 1)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _copy_result(self):
        text = self.results_output.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Hash copied to clipboard!")
    
    def _generate_hash(self):
        text = self.gen_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Input", "Please enter text to hash.")
            return
        if not self.algo_slot.is_filled():
            QMessageBox.warning(self, "No Algorithm", "Please drag an algorithm first.")
            return
        
        algo = self.algo_slot.algo_id
        self.gen_progress.setValue(0)
        self.status_output.clear()
        self.status_output.append(f"Algorithm: {self.algo_slot.algo_name}")
        self.status_output.append("Generating hash...")
        self.gen_progress.setValue(50)
        
        if algo == "sha1":
            result = hashlib.sha1(text.encode('utf-8')).hexdigest()
        elif algo == "sha224":
            result = hashlib.sha224(text.encode('utf-8')).hexdigest()
        elif algo == "sha256":
            result = hashlib.sha256(text.encode('utf-8')).hexdigest()
        elif algo == "sha384":
            result = hashlib.sha384(text.encode('utf-8')).hexdigest()
        elif algo == "sha512":
            result = hashlib.sha512(text.encode('utf-8')).hexdigest()
        else:
            result = ""
        
        self.gen_progress.setValue(100)
        self.results_output.setText(result)
        self.status_output.append(f"Input: {text[:50]}{'...' if len(text) > 50 else ''}")
        self.status_output.append(f"Hash: {result}")
        self.tabs.setCurrentIndex(2)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()