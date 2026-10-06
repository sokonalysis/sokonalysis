# gui/caesar_friedman.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox,
    QApplication, QMessageBox, QFileDialog, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from collections import Counter
import re
import os
import sys

from PySide6.QtGui import QIcon, QFont, QColor
from gui.layout_manager import layout_manager

matplotlib_available = False
try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    matplotlib_available = True
except ImportError:
    pass


if matplotlib_available:
    class FrequencyChart(FigureCanvas):
        def __init__(self, parent=None):
            self.fig = Figure(figsize=(8, 3.5), dpi=100)
            self.ax = self.fig.add_subplot(111)
            super().__init__(self.fig)
            self.setParent(parent)
        
        def update_chart(self, text_clean, theme_colors):
            scale = layout_manager.font_scale()
            bar_label_font = max(7, int(8 * scale))
            xtick_font = max(7, int(9 * scale))
            tick_font = max(8, int(10 * scale))
            
            self.ax.clear()
            if not text_clean:
                self.draw()
                return
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            freq = Counter(text_clean)
            counts = [freq.get(letter, 0) for letter in alphabet]
            colors = [theme_colors['success'] if count > 0 else theme_colors['surface1'] for count in counts]
            bars = self.ax.bar(range(26), counts, color=colors, alpha=0.85)
            for i, count in enumerate(counts):
                if count > 0:
                    self.ax.text(
                        i, count + 0.1, str(count),
                        ha='center', va='bottom',
                        fontsize=bar_label_font, fontweight='bold',
                        color=theme_colors['text']
                    )
            self.ax.set_xticks(range(26))
            self.ax.set_xticklabels(alphabet, fontsize=xtick_font, fontfamily='monospace')
            self.ax.set_facecolor(theme_colors['crust'])
            self.fig.set_facecolor(theme_colors['crust'])
            self.ax.tick_params(colors=theme_colors['text'], labelsize=tick_font)
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.spines['left'].set_color(theme_colors['border'])
            self.ax.spines['bottom'].set_color(theme_colors['border'])
            self.ax.tick_params(axis='x', colors=theme_colors['text'])
            self.ax.tick_params(axis='y', colors=theme_colors['text'])
            self.ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            max_count = max(counts) if counts else 1
            self.ax.set_ylim(0, max_count + 1)
            self.fig.tight_layout(pad=2)
            self.draw()
else:
    # Fallback stub so the page still imports without matplotlib
    class FrequencyChart(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            l = QVBoxLayout(self)
            lbl = QLabel("Matplotlib not available")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
        
        def update_chart(self, text_clean, theme_colors):
            pass


class CaesarFriedmanPage(QWidget):
    
    FRIEDMAN_IC_PRECISE = [
        (0.0660, 1), (0.0520, 2), (0.0473, 3), (0.0449, 4), (0.0435, 5),
        (0.0426, 6), (0.0419, 7), (0.0414, 8), (0.0410, 9), (0.0407, 10),
    ]
    RANDOM_IC = 0.038
    ENGLISH_IC = 0.065
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.best_period = None
        self.overall_ic = None
        self.text_clean = None
        self.freq_sum = None
        self._init_ui()
    
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
        
        title = QLabel("Friedman Test")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_ic_table(), "IC Table")
        self.tabs.addTab(self._tab_stats(), "Statistics")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'input_grp') and self.input_grp is not None:
            try:
                self.input_grp.setStyleSheet(gs)
            except RuntimeError:
                pass
        
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
        
        if hasattr(self, 'cipher_input') and self.cipher_input is not None:
            self.cipher_input.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(
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
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'freq_chart') and self.freq_chart is not None and self.text_clean:
            self.freq_chart.update_chart(self.text_clean, t)
        
        if hasattr(self, 'ic_table') and self.ic_table is not None:
            self.ic_table.setStyleSheet(f"""
                QTableWidget {{background-color:{t['crust']};color:{t['text']};border:none;gridline-color:{t['border']};font-size:{int(13 * scale)}px;}}
                QTableWidget::item {{padding:{int(14 * scale)}px {int(12 * scale)}px;border-bottom:1px solid {t['border']};}}
                QHeaderView::section {{background-color:{t['surface0']};color:{t['text']};padding:{int(14 * scale)}px {int(12 * scale)}px;border:none;border-bottom:2px solid {t['border']};font-weight:700;font-size:{int(12 * scale)}px;}}
            """)
            # Re-populate so highlighted "MATCH" row reflects any new scale/padding
            if self.best_period:
                self._populate_ic_table()
    
    def _tab_setup(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.input_grp = QGroupBox("Cipher Text")
        il = QVBoxLayout()
        self.cipher_input = QTextEdit()
        self.cipher_input.setPlaceholderText("Enter cipher text for Friedman analysis...")
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
        self.input_grp.setLayout(il)
        br2 = QHBoxLayout()
        br2.addStretch()
        btn = QPushButton("Analyze")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._analyze)
        br2.addWidget(btn)
        l.addWidget(self.input_grp)
        l.addLayout(br2)
        l.addStretch()
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
        l.addWidget(self.status_output, 1)
        return w
    
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
        self.results_output.setPlaceholderText("Estimated key length will appear here...")
        l.addWidget(self.results_output, 1)
        return w
    
    def _tab_ic_table(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        self.ic_table = QTableWidget()
        self.ic_table.setColumnCount(3)
        self.ic_table.setHorizontalHeaderLabels(["Key Length", "IC Value", "Status"])
        self.ic_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ic_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.ic_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ic_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ic_table.verticalHeader().setVisible(False)
        self.ic_table.horizontalHeader().setStretchLastSection(True)
        self.ic_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        l.addWidget(self.ic_table, 1)
        return w
    
    def _tab_stats(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        hh = QHBoxLayout()
        hh.setContentsMargins(12, 8, 12, 4)
        export_btn = QPushButton("Export Graph")
        export_btn.setObjectName("actionButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_graph)
        hh.addStretch()
        hh.addWidget(export_btn)
        l.addLayout(hh)
        self.freq_chart = FrequencyChart()
        l.addWidget(self.freq_chart, 1)
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
        self.status_output.clear()
        self.results_output.clear()
        self.ic_table.setRowCount(0)
        self.status_progress.setValue(0)
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _export_graph(self):
        if not matplotlib_available or not hasattr(self, 'freq_chart'):
            QMessageBox.warning(self, "Not Available", "Matplotlib is not installed.")
            return
        fp, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", "frequency_chart.png", "PNG (*.png)"
        )
        if fp:
            self.freq_chart.fig.savefig(
                fp, dpi=150, bbox_inches='tight',
                facecolor=self.theme.current['crust']
            )
            QMessageBox.information(self, "Exported", f"Saved to:\n{fp}")
    
    def _index_of_coincidence(self, text):
        if len(text) <= 1:
            return 0, 0, len(text)
        freq = Counter(text.upper())
        n = len(text)
        freq_sum = sum(f * (f - 1) for f in freq.values() if f > 1)
        ic = freq_sum / (n * (n - 1)) if n > 1 else 0
        return ic, freq_sum, n
    
    def _find_key_from_ic_table(self, ic):
        closest_key, closest_ic, min_diff = None, None, float('inf')
        for table_ic, key_len in self.FRIEDMAN_IC_PRECISE:
            diff = abs(ic - table_ic)
            if diff < min_diff:
                min_diff = diff
                closest_ic = table_ic
                closest_key = key_len
        return closest_key, closest_ic
    
    def _populate_ic_table(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        self.ic_table.setRowCount(0)
        max_display = min(max(10, self.best_period + 2 if self.best_period else 10), 30)
        
        row_height = int(44 * scale)
        for key_len in range(1, max_display + 1):
            row = self.ic_table.rowCount()
            self.ic_table.insertRow(row)
            self.ic_table.setRowHeight(row, row_height)
            
            key_item = QTableWidgetItem(str(key_len))
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ic_table.setItem(row, 0, key_item)
            
            if key_len <= len(self.FRIEDMAN_IC_PRECISE):
                ic_value = self.FRIEDMAN_IC_PRECISE[key_len - 1][0]
            else:
                ic_value = (1 / key_len) * self.ENGLISH_IC + ((key_len - 1) / key_len) * self.RANDOM_IC
            
            ic_item = QTableWidgetItem(f"{ic_value:.3f}")
            ic_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ic_table.setItem(row, 1, ic_item)
            
            status_item = QTableWidgetItem("")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ic_table.setItem(row, 2, status_item)
        
        if self.best_period:
            for row in range(self.ic_table.rowCount()):
                key_item = self.ic_table.item(row, 0)
                if key_item and int(key_item.text()) == self.best_period:
                    for col in range(3):
                        item = self.ic_table.item(row, col)
                        if item:
                            item.setBackground(QColor(t['success']))
                    status_item = self.ic_table.item(row, 2)
                    if status_item:
                        status_item.setText("MATCH")
                    break
    
    def _analyze(self):
        text = self.cipher_input.toPlainText().strip()
        if not text:
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        
        t = self.theme.current
        self.text_clean = re.sub(r'[^A-Za-z]', '', text).upper()
        n = len(self.text_clean)
        
        self.status_output.append(f"[*] Analyzing {n} characters...")
        self.status_progress.setValue(20)
        
        self.overall_ic, self.freq_sum, _ = self._index_of_coincidence(self.text_clean)
        
        freq = Counter(self.text_clean)
        self.status_output.append(f"\n[*] Letter Frequencies:")
        for letter, count in sorted(freq.items()):
            if count > 1:
                self.status_output.append(f"  {letter}: F={count}, F(F-1)={count*(count-1)}")
        
        self.status_output.append(f"\n[*] IC Calculation:")
        self.status_output.append(f"  N = {n}")
        self.status_output.append(f"  Σ F(F-1) = {self.freq_sum}")
        self.status_output.append(f"  IC = Σ F(F-1) / N(N-1)")
        self.status_output.append(f"  IC = {self.freq_sum} / {n*(n-1)}")
        self.status_output.append(f"  IC = {self.overall_ic:.6f}")
        
        self.status_progress.setValue(50)
        
        self.best_period, table_ic = self._find_key_from_ic_table(self.overall_ic)
        self.status_output.append(f"\n[*] IC Table Lookup:")
        self.status_output.append(f"  IC = {self.overall_ic:.6f}")
        self.status_output.append(f"  Closest table value: {table_ic:.3f}")
        self.status_output.append(f"  Estimated key length: {self.best_period}")
        
        self.status_progress.setValue(80)
        
        friedman_k = (
            0.027 * n / ((n - 1) * self.overall_ic + self.ENGLISH_IC - self.RANDOM_IC * n)
            if self.overall_ic > 0 else 0
        )
        self.status_output.append(f"\n[*] Friedman's Formula:")
        self.status_output.append(f"  K ≈ 0.027N / [(N-1)IC + kp - krN]")
        self.status_output.append(f"  K ≈ {0.027*n:.4f} / [{(n-1)*self.overall_ic:.4f} + {self.ENGLISH_IC} - {self.RANDOM_IC}*{n}]")
        self.status_output.append(f"  K ≈ {friedman_k:.1f}")
        self.status_output.append(f"\n  kp (English IC) = {self.ENGLISH_IC}")
        self.status_output.append(f"  kr (Random IC) = {self.RANDOM_IC}")
        
        self._populate_ic_table()
        self.freq_chart.update_chart(self.text_clean, t)
        
        self.status_progress.setValue(100)
        self.status_output.append(f"\n[✓] Analysis complete")
        
        self.results_output.setPlainText(f"Estimated Key Length: {self.best_period}")
        self.tabs.setCurrentIndex(2)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()