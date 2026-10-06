# gui/caesar_bruteforce.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QGridLayout, QScrollArea, QSizePolicy, QApplication,
    QMessageBox, QFileDialog, QFrame
)
from PySide6.QtCore import Qt, QSize, QMimeData, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QDrag, QPainter
import string
from collections import Counter
import os, sys, re
from gui.layout_manager import layout_manager

matplotlib_available = False
try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    matplotlib_available = True
except ImportError:
    pass


class MplChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def update_chart(self, text, theme_colors):
        scale = layout_manager.font_scale()
        base_font = max(7, int(8 * scale))
        tick_font = max(8, int(10 * scale))
        
        self.ax.clear()
        freq = Counter(c.upper() for c in text if c.isalpha())
        letters = list(string.ascii_uppercase)
        counts = [freq.get(l, 0) for l in letters]
        
        bars = self.ax.bar(letters, counts, color=theme_colors['success'], alpha=0.85)
        self.ax.bar_label(
            bars,
            labels=[str(c) if c > 0 else '' for c in counts],
            fontsize=base_font,
            color=theme_colors['text'],
            fontfamily='monospace'
        )
        
        self.ax.set_facecolor(theme_colors['crust'])
        self.fig.set_facecolor(theme_colors['crust'])
        self.ax.tick_params(colors=theme_colors['text'], labelsize=tick_font)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(theme_colors['border'])
        self.ax.spines['bottom'].set_color(theme_colors['border'])
        self.ax.tick_params(axis='x', colors=theme_colors['text'])
        self.ax.tick_params(axis='y', colors=theme_colors['text'])
        self.fig.tight_layout(pad=1.5)
        self.draw()


class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        self.setMinimumSize(int(140 * scale), int(56 * scale))
        self.setMaximumSize(int(220 * scale), int(84 * scale))
    
    def _build(self):
        t = self.colors
        scale = layout_manager.font_scale()
        if self.name_label is None:
            l = QVBoxLayout(self)
            l.setContentsMargins(
                int(14 * scale), int(12 * scale),
                int(14 * scale), int(12 * scale)
            )
            l.setSpacing(int(4 * scale))
            self.name_label = QLabel(self.mode_name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            l.addWidget(self.name_label)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {int(13 * scale)}px; "
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
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self._placeholder = "Drag mapping here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        # Ensure slot is wide enough for the placeholder text at the current scale
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(200, text_w)
        max_w = min_w + int(80 * scale)
        self.setMinimumSize(min_w, int(80 * scale))
        self.setMaximumSize(max_w, int(110 * scale))
    
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
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    
    def dropEvent(self, e):
        data = e.mimeData().text()
        try:
            mid, mn = data.split(':', 1)
            self.mode_id = int(mid)
            self.mode_name = mn
            self._style_filled()
            self.update()
            self.repaint()
            e.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, CaesarBruteForcePage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(10, int(13 * scale))
            p.setPen(QColor(t['accent']))
            p.setFont(QFont("JetBrains Mono", font_size, QFont.Weight.Bold))
            text = self.mode_name
        else:
            font_size = max(9, int(10 * scale))
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", font_size))
            text = self._placeholder
        
        # Inset rect so text never clips against the border
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        
        # Safety: elide if it still doesn't fit
        fm = p.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.clear_slot()
        p = self.parent()
        while p and not isinstance(p, CaesarBruteForcePage):
            p = p.parent()
        if p:
            p._on_mode_cleared()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class ShiftTableGrid(QScrollArea):
    def __init__(self, theme_colors):
        super().__init__()
        self.colors = theme_colors
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(1)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self.container)
    
    def update_colors(self, tc):
        self.colors = tc
    
    def update_table(self, mapping):
        t = self.colors
        scale = layout_manager.font_scale()
        
        cell_w = max(24, int(34 * scale))
        cell_h = max(20, int(28 * scale))
        header_h = max(26, int(34 * scale))
        corner_w = max(42, int(55 * scale))
        base_font = max(9, int(13 * scale))
        small_font = max(8, int(12 * scale))
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        alphabet = string.ascii_uppercase
        
        corner = QLabel("Shift")
        corner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        corner.setStyleSheet(
            f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:6px;"
            f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:4px;"
        )
        corner.setFixedSize(corner_w, header_h)
        self.grid.addWidget(corner, 0, 0)
        
        for col, letter in enumerate(alphabet):
            lbl = QLabel(letter)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:4px;"
                f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:4px;"
            )
            lbl.setFixedSize(cell_w, header_h)
            self.grid.addWidget(lbl, 0, col + 1)
        
        for shift in range(1, 26):
            row_lbl = QLabel(f"{shift:02d}")
            row_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text_secondary']};font-weight:bold;"
                f"padding:3px;font-family:JetBrains Mono;font-size:{small_font}px;border-radius:4px;"
            )
            row_lbl.setFixedSize(corner_w, cell_h)
            self.grid.addWidget(row_lbl, shift, 0)
            
            shifted = alphabet[shift:] + alphabet[:shift]
            for col, char in enumerate(shifted):
                cell = QLabel(char)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if char == alphabet[col]:
                    cell.setStyleSheet(
                        f"background:{t['success']}22;color:{t['success']};font-weight:bold;"
                        f"padding:3px;font-family:JetBrains Mono;font-size:{base_font}px;"
                        f"border-radius:3px;border:1px solid {t['success']}44;"
                    )
                else:
                    cell.setStyleSheet(
                        f"background:transparent;color:{t['text']};padding:3px;"
                        f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:3px;"
                    )
                cell.setFixedSize(cell_w, cell_h)
                self.grid.addWidget(cell, shift, col + 1)


class CaesarBruteForcePage(QWidget):
    
    def __init__(self, theme_manager, back_callback, wordlist_path=""):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.wordlist_words = set()
        self.wordlist_loaded = False
        self.mode_cards = []
        self._last_ct = ""
        self._init_ui()
        # Defer wordlist loading — page opens instantly, loads in background
        QTimer.singleShot(200, self._load_wordlist_async)
    
    def _load_wordlist_async(self):
        """Load wordlist lazily after UI is shown so page opens fast."""
        if self.wordlist_loaded:
            return
        if self.wordlist_path and os.path.exists(self.wordlist_path):
            try:
                words = set()
                with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word and len(word) >= 2:
                            words.add(word)
                            if len(words) > 100000:
                                break
                self.wordlist_words = words
            except:
                pass
        self.wordlist_loaded = True
        self._update_badge()
    
    def set_wordlist_config(self, wordlist_path, split_parts):
        self.wordlist_path = wordlist_path
        self.wordlist_words.clear()
        self.wordlist_loaded = False
        QTimer.singleShot(100, self._load_wordlist_async)
        self._update_badge()
    
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
        
        title = QLabel("Caesar Cipher - Brute Force")
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
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_shift_table(), "Shift Table")
        self.tabs.addTab(self._tab_stats(), "Statistics")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        self._apply_theme()
    
    def _update_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.wordlist_path and os.path.exists(self.wordlist_path):
            self.wordlist_badge.setText("Wordlist Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.wordlist_badge.setText("No Wordlist")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        self.wordlist_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background-color:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'wl_icon'):
            self.wl_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['map_grp', 'in_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'cipher_input') and self.cipher_input is not None:
            self.cipher_input.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
            )
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            self.mode_slot.update_colors(t)
        if hasattr(self, 'shift_grid') and self.shift_grid is not None:
            self.shift_grid.update_colors(t)
            self.shift_grid.update_table(0)
        if hasattr(self, 'mpl_chart') and self.mpl_chart is not None and self._last_ct:
            self.mpl_chart.update_chart(self._last_ct, t)
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        self._update_badge()
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.map_grp = QGroupBox("1. Mapping Style (Drag & Drop)")
        ml = QVBoxLayout()
        ml.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        t = self.theme.current
        for mid, mn in [(0, "A=0, B=1..."), (1, "A=1, B=2...")]:
            card = DraggableModeCard(mid, mn, t)
            self.mode_cards.append(card)
            cr.addWidget(card)
        cr.addStretch()
        ml.addLayout(cr)
        dr = QHBoxLayout()
        self.mode_slot = ModeDropSlot(t)
        dr.addWidget(self.mode_slot)
        dr.addStretch()
        ml.addLayout(dr)
        self.map_grp.setLayout(ml)
        l.addWidget(self.map_grp)
        
        self.in_grp = QGroupBox("2. Cipher Text")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        self.cipher_input = QTextEdit()
        self.cipher_input.setPlaceholderText("Enter Caesar cipher text...")
        self.cipher_input.setMaximumHeight(100)
        il.addWidget(self.cipher_input)
        br = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.cipher_input))
        br.addWidget(paste_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        br.addWidget(clear_btn)
        br.addStretch()
        il.addLayout(br)
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        self.run_btn = QPushButton("Brute Force Decrypt")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setMinimumHeight(48)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._brute)
        self.run_btn.setVisible(False)
        br2 = QHBoxLayout()
        br2.addStretch()
        br2.addWidget(self.run_btn)
        l.addLayout(br2)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _on_mode_dropped(self):
        self.in_grp.setVisible(True)
        self.run_btn.setVisible(True)
    
    def _on_mode_cleared(self):
        self.in_grp.setVisible(False)
        self.run_btn.setVisible(False)
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Result:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        rh.addWidget(copy_btn)
        l.addLayout(rh)
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Decryption results will appear here...")
        l.addWidget(self.results_output, 1)
        return w
    
    def _tab_shift_table(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        self.shift_grid = ShiftTableGrid(self.theme.current)
        # Build table after event loop starts so page opens instantly
        QTimer.singleShot(0, lambda: self.shift_grid.update_table(0))
        l.addWidget(self.shift_grid, 1)
        return w
    
    def _tab_stats(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        if matplotlib_available:
            hh = QHBoxLayout()
            hh.setContentsMargins(12, 8, 12, 4)
            export_btn = QPushButton("Export Graph")
            export_btn.setObjectName("actionButton")
            export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            export_btn.clicked.connect(self._export_graph)
            hh.addStretch()
            hh.addWidget(export_btn)
            l.addLayout(hh)
            self.mpl_chart = MplChart()
            l.addWidget(self.mpl_chart, 1)
        else:
            self.mpl_chart = None
            lbl = QLabel("Matplotlib not available")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
        return w
    
    def _paste_to(self, w):
        c = QApplication.clipboard().text()
        if c:
            if isinstance(w, QTextEdit):
                w.setPlainText(c)
            else:
                w.setText(c)
    
    def _clear_all(self):
        self.cipher_input.clear()
        self.results_output.clear()
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _export_graph(self):
        if not self.mpl_chart:
            return
        fp, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", "frequency_chart.png", "PNG (*.png)"
        )
        if fp:
            self.mpl_chart.fig.savefig(
                fp, dpi=150, bbox_inches='tight',
                facecolor=self.theme.current['crust']
            )
            QMessageBox.information(self, "Exported", f"Saved to:\n{fp}")
    
    def _caesar_decrypt(self, text, shift):
        r = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                r.append(chr((ord(c) - base - shift) % 26 + base))
            else:
                r.append(c)
        return ''.join(r)
    
    def _score_text(self, text):
        if not self.wordlist_words:
            return 0
        words = re.findall(r'[a-zA-Z]+', text.lower())
        if not words:
            return 0
        matches = sum(1 for w in words if w in self.wordlist_words)
        return matches / len(words)
    
    def _brute(self):
        ct = self.cipher_input.toPlainText().strip()
        if not ct:
            return
        self._last_ct = ct
        t = self.theme.current
        mapping = self.mode_slot.mode_id if self.mode_slot.is_filled() else 0
        
        results = []
        for s in range(1, 26):
            decrypted = self._caesar_decrypt(ct, s)
            score = self._score_text(decrypted)
            results.append((s, decrypted, score))
        results.sort(key=lambda x: x[2], reverse=True)
        
        matched = [r for r in results if r[2] > 0]
        
        if matched:
            output = f"Found {len(matched)} match(es)\n\n"
            for s, dec, score in matched:
                output += f"{dec} (Shift {s:02d})\n"
        else:
            output = ""
            for s, dec, score in results:
                output += f"Shift {s:02d}: {dec}\n"
        
        self.results_output.setPlainText(output)
        self.shift_grid.update_colors(t)
        self.shift_grid.update_table(mapping)
        if self.mpl_chart:
            self.mpl_chart.update_chart(ct, t)
        self.tabs.setCurrentIndex(1)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()