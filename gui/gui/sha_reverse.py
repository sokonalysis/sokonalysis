# gui/sha_reverse.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QFrame,
    QMessageBox, QProgressBar, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import hashlib
import os
import threading
import time
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
            while p and not isinstance(p, SHAReversePage):
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
        while p and not isinstance(p, SHAReversePage):
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


class SHAWorker(QThread):
    """Worker for SHA hash reversal using wordlist splitting."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, hash_to_reverse, wordlist_path, split_parts, algo):
        super().__init__()
        self.hash_to_reverse = hash_to_reverse.lower().strip()
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.algo = algo
        self.stop_flag = threading.Event()
        self.found_password = None
        self.lock = threading.Lock()
    
    def _count_words(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def _sha_hash(self, text):
        if self.algo == "sha1":
            return hashlib.sha1(text.encode('utf-8')).hexdigest()
        elif self.algo == "sha224":
            return hashlib.sha224(text.encode('utf-8')).hexdigest()
        elif self.algo == "sha256":
            return hashlib.sha256(text.encode('utf-8')).hexdigest()
        elif self.algo == "sha384":
            return hashlib.sha384(text.encode('utf-8')).hexdigest()
        elif self.algo == "sha512":
            return hashlib.sha512(text.encode('utf-8')).hexdigest()
        return ""
    
    def _search_part(self, part_file, target_hash):
        try:
            with open(part_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if self.stop_flag.is_set():
                        return
                    word = line.strip()
                    if word:
                        if self._sha_hash(word) == target_hash:
                            with self.lock:
                                if not self.stop_flag.is_set():
                                    self.found_password = word
                                    self.stop_flag.set()
                            return
        except:
            pass
    
    def run(self):
        import tempfile, shutil
        temp_dir = None
        try:
            if not self.wordlist_path or not os.path.exists(self.wordlist_path):
                self.finished.emit(False, "No wordlist configured")
                return
            
            word_count = self._count_words(self.wordlist_path)
            if word_count == 0:
                self.finished.emit(False, "Wordlist is empty")
                return
            
            self.progress.emit(f"Wordlist: {word_count:,} words")
            self.progress_value.emit(10)
            
            temp_dir = tempfile.mkdtemp(prefix="sokonalysis_sha_")
            lines_per_part = word_count // self.split_parts
            remainder = word_count % self.split_parts
            
            self.progress.emit(f"Splitting into {self.split_parts} parts...")
            self.progress_value.emit(25)
            
            part_files = []
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as infile:
                for i in range(self.split_parts):
                    if self.stop_flag.is_set():
                        break
                    part_file = os.path.join(temp_dir, f"part_{i+1}.txt")
                    n = lines_per_part + (1 if i < remainder else 0)
                    with open(part_file, 'w', encoding='utf-8') as out:
                        for _ in range(n):
                            line = infile.readline()
                            if not line:
                                break
                            out.write(line)
                    if os.path.getsize(part_file) > 0:
                        part_files.append(part_file)
            
            self.progress.emit(f"Searching with {len(part_files)} threads...")
            self.progress_value.emit(40)
            
            threads = []
            done = [0]
            
            def worker(pf):
                if self.stop_flag.is_set():
                    return
                self._search_part(pf, self.hash_to_reverse)
                with self.lock:
                    done[0] += 1
                    pct = 40 + int((done[0] / len(part_files)) * 55)
                    self.progress_value.emit(pct)
            
            for pf in part_files:
                t = threading.Thread(target=worker, args=(pf,))
                threads.append(t)
                t.start()
                time.sleep(0.05)
            
            for t in threads:
                while t.is_alive():
                    if self.stop_flag.is_set():
                        break
                    t.join(timeout=1)
            
            self.progress_value.emit(100)
            
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            
            if self.found_password:
                self.progress.emit("Match found!")
                self.finished.emit(True, self.found_password)
            else:
                self.progress.emit("No match found")
                self.finished.emit(True, "No match found")
                
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def stop(self):
        self.stop_flag.set()


class SHAReversePage(QWidget):
    """SHA hash reverser with drag-and-drop algorithm."""
    
    SHA_LENGTHS = {"sha1": 40, "sha224": 56, "sha256": 64, "sha384": 96, "sha512": 128}
    
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.worker = None
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
        
        title = QLabel("SHA Hash - Reverse")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        wl_container = QHBoxLayout()
        wl_container.setSpacing(4)
        self.wl_icon = QLabel()
        self.wl_icon.setFixedSize(18, 18)
        self.wl_icon.setStyleSheet("background:transparent;")
        self.wordlist_badge = QLabel()
        self._update_badge()
        wl_container.addWidget(self.wl_icon)
        wl_container.addWidget(self.wordlist_badge)
        header.addLayout(wl_container)
        
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
        
        if hasattr(self, 'rev_hash_input') and self.rev_hash_input is not None:
            try:
                self.rev_hash_input.setStyleSheet(
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
        
        if hasattr(self, 'rev_progress') and self.rev_progress is not None:
            try:
                self.rev_progress.setStyleSheet(
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
        
        self._update_badge()
    
    def _update_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.wordlist_path:
            self.wordlist_badge.setText("Wordlist Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.wordlist_badge.setText("No Wordlist")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        self.wordlist_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'wl_icon'):
            self.wl_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _on_algo_dropped(self):
        self.in_grp.setVisible(True)
        self.rev_start_btn.setVisible(True)
        self.rev_stop_btn.setVisible(True)
    
    def _on_algo_cleared(self):
        self.in_grp.setVisible(False)
        self.rev_start_btn.setVisible(False)
        self.rev_stop_btn.setVisible(False)
    
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
        
        self.in_grp = QGroupBox("2. SHA Hash to Reverse")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        il.setSpacing(10)
        self.rev_hash_input = QTextEdit()
        self.rev_hash_input.setPlaceholderText("Paste SHA hash here...")
        self.rev_hash_input.setMaximumHeight(100)
        self.rev_hash_input.setMinimumHeight(80)
        il.addWidget(self.rev_hash_input)
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.rev_hash_input))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.rev_hash_input.clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        il.addLayout(btn_row)
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        self.rev_stop_btn = QPushButton("Stop")
        self.rev_stop_btn.setObjectName("dangerButton")
        self.rev_stop_btn.setMinimumHeight(42)
        self.rev_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rev_stop_btn.clicked.connect(self._stop_reversal)
        self.rev_stop_btn.setEnabled(False)
        self.rev_stop_btn.setVisible(False)
        
        self.rev_start_btn = QPushButton("Reverse")
        self.rev_start_btn.setObjectName("actionButton")
        self.rev_start_btn.setMinimumHeight(42)
        self.rev_start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rev_start_btn.clicked.connect(self._start_reversal)
        self.rev_start_btn.setVisible(False)
        
        btn_row2.addWidget(self.rev_stop_btn)
        btn_row2.addWidget(self.rev_start_btn)
        l.addLayout(btn_row2)
        l.addStretch()
        return w
    
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.rev_progress = QProgressBar()
        self.rev_progress.setRange(0, 100)
        self.rev_progress.setValue(0)
        self.rev_progress.setTextVisible(True)
        self.rev_progress.setFormat("%p%")
        self.rev_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        
        l.addWidget(self.rev_progress)
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
        rh.addWidget(QLabel("Cracked Password:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Reversed password will appear here...")
        rl.addWidget(self.results_output, 1)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _copy_result(self):
        text = self.results_output.toPlainText().strip()
        if text and text != "No match found in wordlist":
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Password copied to clipboard!")
    
    def set_wordlist_config(self, wordlist_path, split_parts):
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self._update_badge()
    
    def _start_reversal(self):
        hash_value = self.rev_hash_input.toPlainText().strip()
        if not hash_value:
            QMessageBox.warning(self, "No Hash", "Please enter a SHA hash.")
            return
        if not self.algo_slot.is_filled():
            QMessageBox.warning(self, "No Algorithm", "Please drag an algorithm first.")
            return
        if not self.wordlist_path:
            QMessageBox.warning(self, "No Wordlist", "Please configure a wordlist from Configurations menu.")
            return
        
        algo = self.algo_slot.algo_id
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.rev_progress.setValue(0)
        self.rev_start_btn.setEnabled(False)
        self.rev_stop_btn.setEnabled(True)
        
        self.worker = SHAWorker(hash_value, self.wordlist_path, self.split_parts, algo)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.rev_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _stop_reversal(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
            self.status_output.append("Stopped")
            self.rev_start_btn.setEnabled(True)
            self.rev_stop_btn.setEnabled(False)
    
    def _on_progress(self, message):
        self.status_output.append(message)
    
    def _on_finished(self, success, message):
        self.rev_start_btn.setEnabled(True)
        self.rev_stop_btn.setEnabled(False)
        if success:
            if message == "No match found":
                self.results_output.setText("No match found in wordlist")
            else:
                self.results_output.setText(message)
                self.tabs.setCurrentIndex(2)
        else:
            self.results_output.setText(f"Error: {message}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()