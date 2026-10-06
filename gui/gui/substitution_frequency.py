# gui/substitution_frequency.py
"""
Substitution Cipher Solver using hill-climbing algorithm.
Uses quadgram data (EN.json) for fitness scoring.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QProgressBar,
    QSpinBox, QMessageBox, QComboBox, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
import os, sys, json, math, random, time
from gui.layout_manager import layout_manager


class SubstitutionSolverWorker(QThread):
    """Worker thread for breaking substitution ciphers using hill-climbing."""
    
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str, float, float)
    
    def __init__(self, ciphertext, quadgram_file, max_rounds=10000, consolidate=3):
        super().__init__()
        self.ciphertext = ciphertext
        self.quadgram_file = quadgram_file
        self.max_rounds = max_rounds
        self.consolidate = consolidate
        self._running = True
    
    def stop(self):
        self._running = False
    
    def _load_quadgrams(self):
        """Load quadgram data from JSON file."""
        # Try to find the file if it doesn't exist at the given path
        if not os.path.exists(self.quadgram_file):
            base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
            alt_paths = [
                os.path.join(base, 'EN.json'),
                os.path.join(base, '..', 'EN.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'EN.json'),
            ]
            for p in alt_paths:
                if os.path.exists(p):
                    self.quadgram_file = p
                    break
            else:
                raise FileNotFoundError(f"EN.json not found. Searched: {alt_paths}")
        
        with open(self.quadgram_file, 'r') as f:
            obj = json.load(f)
        
        self.alphabet = obj["alphabet"]
        self.alphabet_len = len(self.alphabet)
        self.quadgrams = obj["quadgrams"]
        self.info = {
            "alphabet": obj["alphabet"],
            "nbr_quadgrams": obj["nbr_quadgrams"],
            "most_frequent_quadgram": obj["most_frequent_quadgram"],
            "average_fitness": obj["average_fitness"] / 10,
            "max_fitness": obj["max_fitness"] / 10,
        }
    
    def _text_iterator(self, txt):
        """Yield character indices for characters in alphabet."""
        trans = {val: key for key, val in enumerate(self.alphabet.lower())}
        for char in txt.lower():
            val = trans.get(char)
            if val is not None:
                yield val
    
    def _hill_climbing(self, key, cipher_bin, char_positions):
        """Hill climbing search for best key."""
        plaintext = [key.index(idx) for idx in cipher_bin]
        quadgrams = self.quadgrams
        key_len = self.alphabet_len
        nbr_keys = 0
        max_fitness = 0
        better_key = True
        
        while better_key and self._running:
            better_key = False
            for idx1 in range(key_len - 1):
                for idx2 in range(idx1 + 1, key_len):
                    if not self._running:
                        return max_fitness, nbr_keys
                    
                    ch1 = key[idx1]
                    ch2 = key[idx2]
                    
                    for idx in char_positions[ch1]:
                        plaintext[idx] = idx2
                    for idx in char_positions[ch2]:
                        plaintext[idx] = idx1
                    
                    nbr_keys += 1
                    tmp_fitness = 0
                    quad_idx = (plaintext[0] << 10) + (plaintext[1] << 5) + plaintext[2]
                    for char in plaintext[3:]:
                        quad_idx = ((quad_idx & 0x7FFF) << 5) + char
                        tmp_fitness += quadgrams[quad_idx]
                    
                    if tmp_fitness > max_fitness:
                        max_fitness = tmp_fitness
                        better_key = True
                        key[idx1] = ch2
                        key[idx2] = ch1
                    else:
                        for idx in char_positions[ch1]:
                            plaintext[idx] = idx1
                        for idx in char_positions[ch2]:
                            plaintext[idx] = idx2
        
        return max_fitness, nbr_keys
    
    def run(self):
        try:
            self.progress.emit("Loading quadgram data...")
            self._load_quadgrams()
            self.progress_value.emit(5)
            
            self.progress.emit(
                f"Alphabet: {self.info['alphabet']}\n"
                f"Most frequent quadgram: {self.info['most_frequent_quadgram']}\n"
                f"Starting hill-climbing (max {self.max_rounds} rounds)..."
            )
            self.progress_value.emit(10)
            
            cipher_bin = list(self._text_iterator(self.ciphertext))
            
            if len(cipher_bin) < 4:
                self.finished.emit(False, "", "Ciphertext too short", 0, 0)
                return
            
            char_positions = []
            for idx in range(self.alphabet_len):
                char_positions.append([i for i, x in enumerate(cipher_bin) if x == idx])
            
            key_len = self.alphabet_len
            local_maximum = 0
            local_maximum_hit = 1
            key = list(range(key_len))
            best_key = key.copy()
            nbr_keys = 0
            start_time = time.time()
            
            for round_cntr in range(self.max_rounds):
                if not self._running:
                    return
                
                random.shuffle(key)
                fitness, tmp_nbr_keys = self._hill_climbing(key, cipher_bin, char_positions)
                nbr_keys += tmp_nbr_keys
                
                if fitness > local_maximum:
                    local_maximum = fitness
                    local_maximum_hit = 1
                    best_key = key.copy()
                    
                    preview = self._decrypt_with_key(best_key)[:200]
                    self.progress.emit(
                        f"Round {round_cntr + 1}: New best!\n"
                        f"Fitness: {local_maximum / (len(cipher_bin) - 3) / 10:.2f}\n"
                        f"Preview: {preview}..."
                    )
                elif fitness == local_maximum:
                    local_maximum_hit += 1
                    if local_maximum_hit == self.consolidate:
                        break
                
                progress = 10 + int((round_cntr / self.max_rounds) * 80)
                self.progress_value.emit(progress)
                
                if round_cntr % 100 == 0:
                    self.progress.emit(
                        f"Round {round_cntr + 1}/{self.max_rounds} - "
                        f"Fitness: {local_maximum / (len(cipher_bin) - 3) / 10:.2f}"
                    )
            
            key_str = ''.join([self.alphabet[x] for x in best_key])
            plaintext = self._decrypt_with_key(best_key)
            final_fitness = local_maximum / (len(cipher_bin) - 3) / 10
            seconds = time.time() - start_time
            keys_per_second = round(nbr_keys / seconds) if seconds > 0 else 0
            
            key_display = f"Alphabet: {self.alphabet}\nKey:      {key_str}"
            
            self.progress.emit(
                f"\n{'='*50}\nSOLVED!\n"
                f"Fitness: {final_fitness:.2f}\n"
                f"Keys tried: {nbr_keys:,}\n"
                f"Rounds: {round_cntr + 1}\n"
                f"Speed: {keys_per_second:,} keys/sec\n"
                f"Time: {seconds:.2f}s"
            )
            self.progress_value.emit(100)
            
            self.finished.emit(True, plaintext, key_display, 0.0, final_fitness)
            
        except Exception as e:
            import traceback
            self.finished.emit(False, "", f"{str(e)}\n{traceback.format_exc()}", 0, 0)
    
    def _decrypt_with_key(self, key):
        """Decrypt ciphertext using the given key."""
        camel_key = self.alphabet.upper() + self.alphabet.lower()
        key_upper = ''.join([self.alphabet[x].upper() for x in key])
        key_lower = ''.join([self.alphabet[x].lower() for x in key])
        camel_trans = key_upper + key_lower
        trans = str.maketrans(camel_trans, camel_key)
        return self.ciphertext.translate(trans)


class SubstitutionFrequencyPage(QWidget):
    """GUI page for substitution cipher solving using frequency analysis."""
    
    def __init__(self, theme_manager, back_callback, quadgram_file=""):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        
        # System default EN.json path - works for both dev and bundled
        if hasattr(sys, '_MEIPASS'):
            self.system_json = os.path.join(sys._MEIPASS, 'EN.json')
        else:
            self.system_json = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', 'EN.json'
            )
        
        self.custom_json = ""
        self.quadgram_file = self.system_json
        
        if quadgram_file and os.path.exists(quadgram_file) and quadgram_file != self.system_json:
            self.custom_json = quadgram_file
            self.quadgram_file = quadgram_file
        
        self._init_ui()
    
    def set_quadgram_file(self, filepath):
        """Update the quadgram file path (called from main_window when config changes)."""
        if filepath and os.path.exists(filepath) and filepath != self.system_json:
            self.custom_json = filepath
            self.quadgram_file = filepath
            self.json_combo.setCurrentIndex(1)
        else:
            self.custom_json = ""
            self.quadgram_file = self.system_json
            self.json_combo.setCurrentIndex(0)
        self._update_json_badge()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.', 'assets', 'icons'
        )
        back_icon = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon):
            back_btn.setIcon(QIcon(back_icon))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Substitution Cipher - Frequency Analysis")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        json_container = QHBoxLayout()
        json_container.setSpacing(6)
        
        self.json_combo = QComboBox()
        self.json_combo.addItems(["Default (EN.json)", "Custom JSON"])
        self.json_combo.setCurrentIndex(0 if not self.custom_json else 1)
        self.json_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.json_combo.currentIndexChanged.connect(self._on_json_source_changed)
        json_container.addWidget(self.json_combo)
        
        self.json_icon = QLabel()
        self.json_icon.setFixedSize(18, 18)
        self.json_icon.setStyleSheet("background:transparent;")
        self.json_badge = QLabel()
        self._update_json_badge()
        
        json_container.addWidget(self.json_icon)
        json_container.addWidget(self.json_badge)
        header.addLayout(json_container)
        
        settings = QGroupBox("Hill-Climbing Settings")
        sl = QHBoxLayout()
        
        vl1 = QVBoxLayout()
        vl1.addWidget(QLabel("Max Rounds:"))
        self.rounds_input = QSpinBox()
        self.rounds_input.setRange(100, 100000)
        self.rounds_input.setValue(10000)
        self.rounds_input.setSingleStep(1000)
        self.rounds_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rounds_input.setMinimumWidth(90)
        self.rounds_input.setMaximumWidth(140)
        vl1.addWidget(self.rounds_input)
        sl.addLayout(vl1)
        
        vl2 = QVBoxLayout()
        vl2.addWidget(QLabel("Consolidate:"))
        self.consolidate_input = QSpinBox()
        self.consolidate_input.setRange(1, 30)
        self.consolidate_input.setValue(3)
        self.consolidate_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.consolidate_input.setMinimumWidth(90)
        self.consolidate_input.setMaximumWidth(140)
        vl2.addWidget(self.consolidate_input)
        sl.addLayout(vl2)
        
        sl.addStretch()
        settings.setLayout(sl)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._input_tab(), "Input")
        self.tabs.addTab(self._status_tab(), "Status")
        self.tabs.addTab(self._results_tab(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(settings)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _on_json_source_changed(self, index):
        if index == 0:
            self.custom_json = ""
            self.quadgram_file = self.system_json
        self._update_json_badge()
    
    def _update_json_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else '.', 'assets', 'icons'
        )
        
        if self.json_combo.currentIndex() == 0:
            self.json_badge.setText("Default")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        elif self.custom_json and os.path.exists(self.custom_json):
            self.json_badge.setText(os.path.basename(self.custom_json))
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.json_badge.setText("No JSON")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        
        self.json_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;"
            f"background-color:{c}22;color:{c};"
        )
        
        if hasattr(self, 'json_icon') and os.path.exists(icon_path):
            self.json_icon.setPixmap(
                QPixmap(icon_path).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            )
    
    def _input_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        in_grp = QGroupBox("Ciphertext")
        il = QVBoxLayout()
        il.setSpacing(10)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste ciphertext here to break...")
        self.input_text.setMaximumHeight(140)
        self.input_text.setMinimumHeight(100)
        il.addWidget(self.input_text)
        
        # Paste / Clear row
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.input_text))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        il.addLayout(btn_row)
        
        in_grp.setLayout(il)
        
        hint = QLabel("Configure custom quadgram JSON via Config > Quadgram Settings.")
        hint.setStyleSheet(
            f"color:{self.theme.current['text_tertiary']};font-size:11px;"
            f"background:transparent;padding:0 4px;"
        )
        
        btn = QHBoxLayout()
        btn.addStretch()
        solve = QPushButton("Break Cipher")
        solve.setObjectName("actionButton")
        solve.setCursor(Qt.CursorShape.PointingHandCursor)
        solve.clicked.connect(self._solve)
        btn.addWidget(solve)
        
        l.addWidget(in_grp)
        l.addWidget(hint)
        l.addLayout(btn)
        l.addStretch()
        return w
    
    def _status_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Solver status...")
        self.status_output.setMinimumHeight(200)
        
        l.addWidget(self.progress_bar)
        l.addWidget(self.status_output)
        return w
    
    def _results_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        res_grp = QGroupBox("Decryption Results")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        
        # Recovered key row with Copy button
        key_hdr = QHBoxLayout()
        key_hdr.addWidget(QLabel("Recovered Key:"))
        key_hdr.addStretch()
        copy_key_btn = QPushButton("Copy Key")
        copy_key_btn.setObjectName("actionButton")
        copy_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_key_btn.clicked.connect(self._copy_key)
        key_hdr.addWidget(copy_key_btn)
        rl.addLayout(key_hdr)
        
        self.key_output = QLineEdit()
        self.key_output.setReadOnly(True)
        self.key_output.setPlaceholderText("Recovered key will appear here...")
        rl.addWidget(self.key_output)
        
        # Decrypted text row with Copy button
        text_hdr = QHBoxLayout()
        text_hdr.addWidget(QLabel("Decrypted Text:"))
        text_hdr.addStretch()
        copy_text_btn = QPushButton("Copy Text")
        copy_text_btn.setObjectName("actionButton")
        copy_text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_text_btn.clicked.connect(self._copy_text)
        text_hdr.addWidget(copy_text_btn)
        rl.addLayout(text_hdr)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Decrypted text will appear here...")
        self.output_text.setMinimumHeight(150)
        rl.addWidget(self.output_text, 1)
        
        res_grp.setLayout(rl)
        l.addWidget(res_grp, 1)
        return w
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;
            font-size:{int(12 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox {{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title {{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for grp in self.findChildren(QGroupBox):
            try:
                grp.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(16 * scale)}px;"
                        f"font-weight:700;font-size:{int(14 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(16 * scale)}px;"
                        f"font-weight:700;font-size:{int(14 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        # Scale the primary "Break Cipher" button so text never clips
        for btn in self.findChildren(QPushButton):
            try:
                if btn.text() == "Break Cipher":
                    btn.setMinimumHeight(max(42, int(52 * scale)))
            except RuntimeError:
                pass
        
        self.input_text.setStyleSheet(
            f"QTextEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        self.status_output.setStyleSheet(
            f"QTextEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(12 * scale)}px;}}"
        )
        self.key_output.setStyleSheet(
            f"QLineEdit{{background:{t['crust']};color:{t['accent']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(11, int(11 * scale))}px;}}"
        )
        self.output_text.setStyleSheet(
            f"QTextEdit{{background:{t['crust']};color:{t['success']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
        )
        
        self.progress_bar.setStyleSheet(
            f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
            f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
            f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
        )
        
        # Spinbox with visible CSS-triangle arrows
        sp_font = max(12, int(12 * scale))
        arrow_w = max(16, int(18 * scale))
        for spin in [self.rounds_input, self.consolidate_input]:
            try:
                spin.setFixedHeight(max(30, int(34 * scale)))
                spin.setStyleSheet(
                    f"QSpinBox{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:4px;"
                    f"padding:0px 8px;"
                    f"font-size:{sp_font}px;}} "
                    f"QSpinBox::up-button {{"
                    f"  subcontrol-origin: border;"
                    f"  subcontrol-position: top right;"
                    f"  width:{arrow_w}px;"
                    f"  background:{t['surface0']};"
                    f"  border-left:1px solid {t['border']};"
                    f"  border-top-right-radius:4px;"
                    f"  border-bottom:1px solid {t['border']};"
                    f"}} "
                    f"QSpinBox::down-button {{"
                    f"  subcontrol-origin: border;"
                    f"  subcontrol-position: bottom right;"
                    f"  width:{arrow_w}px;"
                    f"  background:{t['surface0']};"
                    f"  border-left:1px solid {t['border']};"
                    f"  border-bottom-right-radius:4px;"
                    f"}} "
                    f"QSpinBox::up-arrow {{"
                    f"  width:0; height:0;"
                    f"  border-left:4px solid transparent;"
                    f"  border-right:4px solid transparent;"
                    f"  border-bottom:5px solid {t['text']};"
                    f"}} "
                    f"QSpinBox::down-arrow {{"
                    f"  width:0; height:0;"
                    f"  border-left:4px solid transparent;"
                    f"  border-right:4px solid transparent;"
                    f"  border-top:5px solid {t['text']};"
                    f"}}"
                )
            except RuntimeError:
                pass
        
        self.json_combo.setStyleSheet(f"""
            QComboBox{{background:{t['crust']};color:{t['text']};
            border:1px solid {t['border']};border-radius:4px;
            padding:5px 10px;font-size:{max(12, int(12 * scale))}px;font-weight:600;}}
            QComboBox:hover{{border-color:{t['accent']};}}
            QComboBox QAbstractItemView{{background:{t['crust']};color:{t['text']};
            border:1px solid {t['border']};
            selection-background-color:{t['surface0']};}}
        """)
        
        self._update_json_badge()
    
    def _paste_to(self, widget):
        """Paste clipboard contents into the given text widget."""
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setPlainText(clipboard)
    
    def _clear_all(self):
        """Clear ciphertext input and any previous results."""
        self.input_text.clear()
        self.key_output.clear()
        self.output_text.clear()
        self.status_output.clear()
        self.progress_bar.setValue(0)
    
    def _copy_key(self):
        """Copy the recovered key to the clipboard."""
        text = self.key_output.text().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Key copied to clipboard!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No key has been recovered yet.")
    
    def _copy_text(self):
        """Copy the decrypted text to the clipboard."""
        text = self.output_text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Decrypted text copied to clipboard!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No decrypted text available yet.")
    
    def _solve(self):
        ciphertext = self.input_text.toPlainText().strip()
        if not ciphertext:
            QMessageBox.warning(self, "No Input", "Please enter ciphertext to break.")
            return
        
        if self.json_combo.currentIndex() == 1 and not self.custom_json:
            QMessageBox.warning(
                self, "No JSON Configured",
                "You selected 'Custom JSON' but no file is configured.\n\n"
                "Please go to Config > Quadgram Settings to configure a custom "
                "quadgram JSON file, or switch to 'Default (EN.json)'."
            )
            return
        
        if not os.path.exists(self.quadgram_file):
            QMessageBox.warning(
                self, "JSON File Missing",
                f"Quadgram file not found:\n{self.quadgram_file}"
            )
            return
        
        max_rounds = self.rounds_input.value()
        consolidate = self.consolidate_input.value()
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.progress_bar.setValue(0)
        
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        self.worker = SubstitutionSolverWorker(
            ciphertext, self.quadgram_file, max_rounds, consolidate
        )
        self.worker.progress.connect(self.status_output.append)
        self.worker.progress_value.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_finished(self, success, plaintext, key, init_fit, final_fit):
        self.tabs.setCurrentIndex(2)
        if success:
            self.key_output.setText(key)
            self.output_text.setPlainText(plaintext)
        else:
            self.output_text.setPlainText(f"Error:\n{key}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()