# gui/caesar_kasiski.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox,
    QApplication, QMessageBox, QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QSize
from collections import defaultdict, Counter
import re
import os
import sys

from PySide6.QtGui import QIcon
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


if matplotlib_available:
    class KasiskiChart(FigureCanvas):
        def __init__(self, parent=None):
            self.fig = Figure(figsize=(8, 3), dpi=100)
            self.ax = self.fig.add_subplot(111)
            super().__init__(self.fig)
            self.setParent(parent)
        
        def update_chart(self, factors, counts, theme_colors):
            scale = layout_manager.font_scale()
            label_font = max(7, int(9 * scale))
            tick_font = max(8, int(10 * scale))
            
            self.ax.clear()
            if not factors:
                self.draw()
                return
            bars = self.ax.bar(factors, counts, color=theme_colors['success'], alpha=0.85)
            self.ax.bar_label(
                bars,
                labels=[str(c) for c in counts],
                fontsize=label_font,
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
            self.fig.tight_layout(pad=2)
            self.draw()
else:
    # Fallback stub so the page still imports and runs without matplotlib
    class KasiskiChart(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            l = QVBoxLayout(self)
            lbl = QLabel("Matplotlib not available")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
        
        def update_chart(self, factors, counts, theme_colors):
            pass


class CaesarKasiskiPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._factors_list = []
        self._counts_list = []
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
        
        title = QLabel("Kasiski Examination")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
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
        if hasattr(self, 'kasiski_chart') and self.kasiski_chart is not None:
            self.kasiski_chart.update_chart(self._factors_list, self._counts_list, t)
    
    def _tab_setup(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.input_grp = QGroupBox("Cipher Text")
        il = QVBoxLayout()
        self.cipher_input = QTextEdit()
        self.cipher_input.setPlaceholderText("Enter Vigenère cipher text to analyze...")
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
        self.results_output.setPlaceholderText("Final answer will appear here...")
        l.addWidget(self.results_output, 1)
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
        self.kasiski_chart = KasiskiChart()
        l.addWidget(self.kasiski_chart, 1)
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
        self.status_progress.setValue(0)
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _export_graph(self):
        if not matplotlib_available or not hasattr(self, 'kasiski_chart'):
            QMessageBox.warning(self, "Not Available", "Matplotlib is not installed.")
            return
        fp, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", "kasiski_chart.png", "PNG (*.png)"
        )
        if fp:
            self.kasiski_chart.fig.savefig(
                fp, dpi=150, bbox_inches='tight',
                facecolor=self.theme.current['crust']
            )
            QMessageBox.information(self, "Exported", f"Saved to:\n{fp}")
    
    def _find_repeated_sequences(self, text, min_len=3, max_len=5):
        text = text.upper()
        sequences = defaultdict(list)
        for length in range(min_len, max_len + 1):
            for i in range(len(text) - length + 1):
                seq = text[i:i + length]
                if seq.isalpha():
                    sequences[seq].append(i)
        return {k: v for k, v in sequences.items() if len(v) > 1}
    
    def _analyze(self):
        text = self.cipher_input.toPlainText().strip()
        if not text:
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        
        t = self.theme.current
        text_clean = re.sub(r'[^A-Za-z]', '', text).upper()
        text_len = len(text_clean)
        
        self.status_output.append(f"[*] Analyzing {text_len} characters...")
        self.status_progress.setValue(20)
        
        sequences = self._find_repeated_sequences(text_clean)
        self.status_progress.setValue(50)
        
        if not sequences:
            self.status_output.append("[!] No repeated sequences found")
            self.results_output.setPlainText("No repeated sequences of length 3+ found.")
            self._factors_list, self._counts_list = [], []
        else:
            self.status_output.append(f"[*] Found {len(sequences)} repeated patterns")
            
            all_distances = []
            all_factor_sets = []
            
            for seq, positions in sorted(sequences.items(), key=lambda x: (-len(x[0]), x[0])):
                distances = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
                all_distances.extend(distances)
                factors = set()
                for d in distances:
                    for f in range(2, d + 1):
                        if d % f == 0:
                            factors.add(f)
                all_factor_sets.append(factors)
                self.status_output.append(f"  {seq}: positions={positions}, distances={distances}")
            
            self.status_progress.setValue(70)
            
            result_text = ""
            if all_distances:
                all_factors = []
                for d in all_distances:
                    for f in range(2, d + 1):
                        if d % f == 0:
                            all_factors.append(f)
                factor_counts = Counter(all_factors)
                top_factors = [(f, c) for f, c in factor_counts.most_common(15) if c >= 2]
                
                if top_factors:
                    self._factors_list = [str(f) for f, _ in top_factors[:10]]
                    self._counts_list = [c for _, c in top_factors[:10]]
                
                intersection = set()
                if all_factor_sets:
                    intersection = all_factor_sets[0].copy()
                    for fs in all_factor_sets[1:]:
                        intersection &= fs
                    intersection = sorted(intersection)
                
                if intersection:
                    realistic = [f for f in intersection if 2 <= f <= 20]
                    if realistic:
                        result_text = f"Most likely keyword length: {realistic[0]}"
                    else:
                        result_text = f"Most likely keyword length: {intersection[0]}"
                    self.status_output.append(f"[✓] Common factors: {intersection}")
                elif top_factors:
                    result_text = f"Most frequent factor: {top_factors[0][0]}"
                    self.status_output.append(f"[✓] Best factor: {top_factors[0][0]}")
            else:
                self._factors_list, self._counts_list = [], []
                result_text = "Insufficient data"
            
            self.results_output.setPlainText(result_text)
        
        self.status_progress.setValue(100)
        self.status_output.append("[✓] Analysis complete")
        self.kasiski_chart.update_chart(self._factors_list, self._counts_list, t)
        self.tabs.setCurrentIndex(2)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()