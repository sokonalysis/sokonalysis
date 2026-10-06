# gui/caesar_hybrid.py
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
    class HybridChart(FigureCanvas):
        def __init__(self, parent=None):
            self.fig = Figure(figsize=(10, 4), dpi=100)
            self.ax1 = self.fig.add_subplot(121)
            self.ax2 = self.fig.add_subplot(122)
            super().__init__(self.fig)
            self.setParent(parent)
        
        def update_chart(self, kasiski_factors, kasiski_counts, friedman_periods, friedman_ics,
                         best_kasiski, best_friedman, consensus, theme_colors):
            scale = layout_manager.font_scale()
            title_font = max(9, int(11 * scale))
            label_font = max(8, int(9 * scale))
            tick_font = max(8, int(9 * scale))
            legend_font = max(7, int(8 * scale))
            
            self.ax1.clear()
            self.ax2.clear()
            
            if kasiski_factors:
                colors1 = []
                for f in kasiski_factors:
                    if str(f) == str(consensus):
                        colors1.append(theme_colors['accent'])
                    elif str(f) == str(best_kasiski):
                        colors1.append(theme_colors['success'])
                    else:
                        colors1.append(theme_colors['surface1'])
                self.ax1.bar(kasiski_factors, kasiski_counts, color=colors1, alpha=0.85)
                self.ax1.set_title(
                    'Kasiski Factor Distribution',
                    color=theme_colors['text'],
                    fontsize=title_font, fontweight='bold'
                )
                self.ax1.set_xlabel('Key Length Factor', color=theme_colors['text'], fontsize=label_font)
                self.ax1.set_ylabel('Frequency', color=theme_colors['text'], fontsize=label_font)
            
            if friedman_periods:
                colors2 = []
                for p in friedman_periods:
                    if int(p) == consensus:
                        colors2.append(theme_colors['accent'])
                    elif int(p) == best_friedman:
                        colors2.append(theme_colors['success'])
                    else:
                        colors2.append(theme_colors['surface1'])
                self.ax2.bar(friedman_periods, friedman_ics, color=colors2, alpha=0.85)
                self.ax2.axhline(
                    y=0.065, color=theme_colors['accent'],
                    linestyle='--', linewidth=1.5, alpha=0.7,
                    label='English IC (0.065)'
                )
                self.ax2.axhline(
                    y=0.038, color=theme_colors['error'],
                    linestyle=':', linewidth=1.5, alpha=0.5,
                    label='Random IC (0.038)'
                )
                self.ax2.set_title(
                    'Friedman IC by Period',
                    color=theme_colors['text'],
                    fontsize=title_font, fontweight='bold'
                )
                self.ax2.set_xlabel('Period (Key Length)', color=theme_colors['text'], fontsize=label_font)
                self.ax2.set_ylabel('Index of Coincidence', color=theme_colors['text'], fontsize=label_font)
                self.ax2.legend(fontsize=legend_font, loc='upper right')
            
            for ax in [self.ax1, self.ax2]:
                ax.set_facecolor(theme_colors['crust'])
                ax.tick_params(colors=theme_colors['text'], labelsize=tick_font)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color(theme_colors['border'])
                ax.spines['bottom'].set_color(theme_colors['border'])
                ax.tick_params(axis='x', colors=theme_colors['text'])
                ax.tick_params(axis='y', colors=theme_colors['text'])
            
            self.fig.set_facecolor(theme_colors['crust'])
            self.fig.tight_layout(pad=2)
            self.draw()
else:
    # Fallback stub so the page still imports without matplotlib
    class HybridChart(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            l = QVBoxLayout(self)
            lbl = QLabel("Matplotlib not available")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(lbl)
        
        def update_chart(self, *args, **kwargs):
            pass


class CaesarHybridPage(QWidget):
    
    RANDOM_IC = 0.038
    ENGLISH_IC = 0.065
    FRIEDMAN_IC_PRECISE = [
        (0.0660, 1), (0.0520, 2), (0.0473, 3), (0.0449, 4), (0.0435, 5),
        (0.0426, 6), (0.0419, 7), (0.0414, 8), (0.0410, 9), (0.0407, 10),
    ]
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
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
        
        title = QLabel("Hybrid Approach")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_stats(), "Visualization")
        
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
        
        if hasattr(self, 'hybrid_chart') and self.hybrid_chart is not None and hasattr(self, '_last_chart_data'):
            self.hybrid_chart.update_chart(*self._last_chart_data, t)
    
    def _tab_setup(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.input_grp = QGroupBox("Cipher Text")
        il = QVBoxLayout()
        self.cipher_input = QTextEdit()
        self.cipher_input.setPlaceholderText("Enter Vigenere cipher text for hybrid analysis...")
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
        btn = QPushButton("Analyze (Hybrid)")
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
        self.status_output.setPlaceholderText("Activity log and comparison...")
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
        self.results_output.setPlaceholderText("Consensus key length will appear here...")
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
        self.hybrid_chart = HybridChart()
        l.addWidget(self.hybrid_chart, 1)
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
        if not matplotlib_available or not hasattr(self, 'hybrid_chart'):
            QMessageBox.warning(self, "Not Available", "Matplotlib is not installed.")
            return
        fp, _ = QFileDialog.getSaveFileName(
            self, "Export Graph", "hybrid_chart.png", "PNG (*.png)"
        )
        if fp:
            self.hybrid_chart.fig.savefig(
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
    
    def _find_repeated_sequences(self, text, min_len=3, max_len=5):
        text = text.upper()
        sequences = defaultdict(list)
        for length in range(min_len, max_len + 1):
            for i in range(len(text) - length + 1):
                seq = text[i:i + length]
                if seq.isalpha():
                    sequences[seq].append(i)
        return {k: v for k, v in sequences.items() if len(v) > 1}
    
    def _find_key_from_ic_table(self, ic):
        closest_key, closest_ic, min_diff = None, None, float('inf')
        for table_ic, key_len in self.FRIEDMAN_IC_PRECISE:
            diff = abs(ic - table_ic)
            if diff < min_diff:
                min_diff = diff
                closest_ic = table_ic
                closest_key = key_len
        return closest_key, closest_ic
    
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
        n = len(text_clean)
        
        self.status_output.append(f"[*] Analyzing {n} characters...")
        self.status_progress.setValue(10)
        
        # Kasiski
        sequences = self._find_repeated_sequences(text_clean)
        all_distances = []
        for seq, positions in sequences.items():
            for i in range(len(positions) - 1):
                all_distances.append(positions[i + 1] - positions[i])
        all_factors = []
        for d in all_distances:
            for f in range(2, min(d + 1, 50)):
                if d % f == 0:
                    all_factors.append(f)
        factor_counts = Counter(all_factors)
        kasiski_factors = factor_counts.most_common(15)
        kasiski_best = kasiski_factors[0][0] if kasiski_factors else None
        
        self.status_output.append(f"\n[*] Kasiski: found {len(sequences)} repeated patterns")
        if kasiski_best:
            self.status_output.append(f"  Best factor: {kasiski_best}")
        self.status_progress.setValue(30)
        
        # Friedman
        overall_ic, freq_sum, _ = self._index_of_coincidence(text_clean)
        table_key, table_ic = self._find_key_from_ic_table(overall_ic)
        friedman_k = (
            0.027 * n / ((n - 1) * overall_ic + self.ENGLISH_IC - self.RANDOM_IC * n)
            if overall_ic > 0 else 0
        )
        friedman_best = table_key if table_key else round(friedman_k)
        
        self.status_output.append(f"\n[*] Friedman: IC = {overall_ic:.6f}")
        self.status_output.append(f"  Table lookup: {table_key}")
        self.status_output.append(f"  Formula: K = {friedman_k:.1f}")
        self.status_progress.setValue(50)
        
        # Period-by-period ICs
        max_period = min(20, n // 2 + 1)
        friedman_data = []
        for period in range(1, max_period + 1):
            sub_ics = []
            for i in range(period):
                sub_text = text_clean[i::period]
                if len(sub_text) > 1:
                    ic_val, _, _ = self._index_of_coincidence(sub_text)
                    sub_ics.append(ic_val)
            if sub_ics:
                friedman_data.append((period, sum(sub_ics) / len(sub_ics)))
        self.status_progress.setValue(70)
        
        # Consensus
        scores = {}
        if kasiski_factors:
            for factor, count in kasiski_factors[:10]:
                if count >= 2:
                    scores[factor] = scores.get(factor, 0) + (count / kasiski_factors[0][1]) * 20
        if friedman_data:
            for period, ic in friedman_data:
                proximity = 1.0 - abs(ic - 0.065) / 0.03
                if proximity > 0.3:
                    scores[period] = scores.get(period, 0) + max(0, proximity) * 20
        if friedman_best and kasiski_factors:
            for factor, count in kasiski_factors[:10]:
                diff = abs(factor - friedman_best)
                if diff <= 5:
                    scores[factor] = scores.get(factor, 0) + max(0, (5 - diff) / 5) * 80
        if friedman_best:
            scores[friedman_best] = scores.get(friedman_best, 0) + 40
        
        consensus = max(scores, key=scores.get) if scores else (friedman_best or kasiski_best or 1)
        conf_score = scores.get(consensus, 0)
        normalized_conf = min(100, (conf_score / 120) * 100)
        
        # Comparison under status
        self.status_output.append(f"\n{'='*50}")
        self.status_output.append(f"METHOD COMPARISON")
        self.status_output.append(f"{'='*50}")
        self.status_output.append(f"Kasiski Examination: {kasiski_best if kasiski_best else 'N/A'}")
        self.status_output.append(f"Friedman Test (Table): {table_key}")
        self.status_output.append(f"Friedman Test (Formula): {round(friedman_k) if friedman_k else 'N/A'}")
        self.status_output.append(f"\nConsensus: {consensus} ({normalized_conf:.0f}% confidence)")
        self.status_output.append(f"\nReference: English IC = {self.ENGLISH_IC:.3f}, Random IC = {self.RANDOM_IC:.3f}")
        self.status_progress.setValue(90)
        
        # Results
        self.results_output.setPlainText(f"Consensus Key Length: {consensus}")
        
        # Chart
        k_factors = [str(f) for f, _ in kasiski_factors[:10]] if kasiski_factors else []
        k_counts = [c for _, c in kasiski_factors[:10]] if kasiski_factors else []
        f_periods = [str(p) for p, _ in friedman_data[:20]] if friedman_data else []
        f_ics = [ic for _, ic in friedman_data[:20]] if friedman_data else []
        
        self._last_chart_data = (
            k_factors, k_counts, f_periods, f_ics,
            kasiski_best, friedman_best, consensus
        )
        self.hybrid_chart.update_chart(
            k_factors, k_counts, f_periods, f_ics,
            kasiski_best, friedman_best, consensus, t
        )
        
        self.status_progress.setValue(100)
        self.status_output.append(f"\n[✓] Analysis complete")
        self.tabs.setCurrentIndex(2)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()