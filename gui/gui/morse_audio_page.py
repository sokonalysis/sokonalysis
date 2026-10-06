# gui/morse_audio_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSpinBox, QGridLayout, QToolButton, QMenu,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize, QTimer
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
import os, sys, struct, math, tempfile, subprocess, shutil, wave, time
import numpy as np
from gui.layout_manager import layout_manager


MORSE_ENCODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    'DOT': '.-.-.-', 'COMMA': '--..--', 'QMARK': '..--..', 'EXCL': '-.-.--',
    'SLASH': '-..-.', 'AT': '.--.-.', 'AMP': '.-...', 'COLON': '---...',
    'SEMI': '-.-.-.', 'EQ': '-...-', 'PLUS': '.-.-.', 'MINUS': '-....-',
    'UNDER': '..--.-', 'DQUOTE': '.-..-.', 'DOLLAR': '...-..-',
    'LPAREN': '-.--.', 'RPAREN': '-.--.-', 'APOS': '.----.',
    'AR': '.-.-.', 'AS': '.-...', 'BK': '-...-.-', 'BT': '-...-',
    'CL': '-.-..-..', 'CT': '-.-.-', 'DO': '-..---', 'KN': '-.--.',
    'SK': '...-.-', 'SN': '...-.', 'SOS': '...---...', 'VE': '...-.',
    'HH': '........', 'INT': '..-.-', 'KA': '-.-.-', 'CQ': '-.-.--.-',
    'DE': '-...', 'K': '-.-', 'R': '.-.', 'AA': '.-.-', 'NIL': '-. .. .-..',
    'QRA': '--.- .-. .-', 'QRB': '--.- .-. -...', 'QRG': '--.- .-. --.',
    'QRH': '--.- .-. ....', 'QRK': '--.- .-. -.-', 'QRL': '--.- .-. .-..',
    'QRM': '--.- .-. --', 'QRN': '--.- .-. -.', 'QRO': '--.- .-. ---',
    'QRP': '--.- .-. .--.', 'QRQ': '--.- .-. --.-', 'QRS': '--.- .-. ...',
    'QRT': '--.- .-. -', 'QRU': '--.- .-. ..-', 'QRV': '--.- .-. ...-',
    'QRX': '--.- .-. -..-', 'QRZ': '--.- .-. --..', 'QSA': '--.- ... .-',
    'QSB': '--.- ... -...', 'QSK': '--.- ... -.-', 'QSL': '--.- ... .-..',
    'QSO': '--.- ... ---', 'QSY': '--.- ... -.--', 'QTC': '--.- - -.-.',
    'QTH': '--.- - ....', 'QTR': '--.- - .-.',
    '73': '--... ...--', '88': '---.. ---..', '99': '----. ----.',
}

# Build decode dictionary prioritizing single characters
MORSE_DECODE = {}
for k, v in MORSE_ENCODE.items():
    if len(k) == 1 and k.isalpha():
        MORSE_DECODE[v] = k
for k, v in MORSE_ENCODE.items():
    if len(k) == 1 and k.isdigit():
        MORSE_DECODE[v] = k
for k, v in MORSE_ENCODE.items():
    if v not in MORSE_DECODE:
        MORSE_DECODE[v] = k


class MorseAudioDecodeWorker(QThread):
    progress = Signal(str); progress_value = Signal(int); finished = Signal(bool, str)
    def __init__(self, audio_path): super().__init__(); self.audio_path = audio_path
    def run(self):
        try:
            self.progress.emit(f"Reading: {os.path.basename(self.audio_path)}"); self.progress_value.emit(10)
            with wave.open(self.audio_path, 'rb') as w:
                sr, nc, sw, nf = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
                raw = w.readframes(nf)
            self.progress.emit(f"Rate: {sr}Hz | Duration: {nf/sr:.1f}s"); self.progress_value.emit(20)
            dtype = np.int16 if sw == 2 else np.int32; audio = np.frombuffer(raw, dtype=dtype)
            if nc == 2: audio = audio.reshape(-1, 2).mean(axis=1).astype(dtype)
            if np.max(np.abs(audio)) > 0: audio = audio / np.max(np.abs(audio))
            self.progress.emit("Analyzing frequency..."); self.progress_value.emit(30)
            ws = min(4096, len(audio)); seg = audio[:ws] * np.hanning(ws)
            fft = np.abs(np.fft.rfft(seg)); freqs = np.fft.rfftfreq(ws, 1/sr)
            mask = (freqs >= 300) & (freqs <= 2000)
            df = freqs[mask][np.argmax(fft[mask])] if np.any(mask) else 800
            self.progress.emit(f"Frequency: {df:.0f} Hz"); self.progress_value.emit(40)
            env = np.abs(audio); w = max(1, int(sr * 0.01))
            env = np.convolve(env, np.ones(w)/w, mode='same'); self.progress_value.emit(50)
            th = np.mean(env) + 0.5 * np.std(env); sig = (env > th).astype(int)
            self.progress.emit("Decoding Morse..."); self.progress_value.emit(60)
            trans = []; cur, cnt = sig[0] if len(sig) > 0 else 0, 0
            for s in sig:
                if s == cur: cnt += 1
                else: trans.append((cur, cnt)); cur = s; cnt = 1
            if cnt > 0: trans.append((cur, cnt))
            on_t = [d for st, d in trans if st == 1 and d > 10]
            if not on_t: self.finished.emit(False, "No Morse signals detected"); return
            on_t.sort(); dl = on_t[min(len(on_t)//3, len(on_t)-1)]
            self.progress.emit(f"Dit: {dl} samples ({dl/sr*1000:.0f}ms)"); self.progress_value.emit(70)
            morse = ""
            for st, d in trans:
                if st == 1: morse += "-" if d > dl * 2.5 else "."
                else:
                    if d > dl * 7: morse += " / "
                    elif d > dl * 3: morse += " "
            self.progress_value.emit(80)
            result = ""
            for word in morse.split('/'):
                w = ""
                for l in word.split():
                    l = l.strip(); w += MORSE_DECODE.get(l, '?' if l else '')
                if w: result += w + " "
            result = result.strip(); self.progress.emit(f"Done: {result}"); self.progress_value.emit(100)
            self.finished.emit(True, result)
        except Exception as e: self.progress.emit(f"Error: {str(e)}"); self.progress_value.emit(100); self.finished.emit(False, "")


class MorseAudioGenerator(QThread):
    progress = Signal(str); progress_value = Signal(int); finished = Signal(bool, str, list, int)
    def __init__(self, text, wpm=20, frequency=800, output_path=""):
        super().__init__(); self.text = text; self.wpm = wpm; self.frequency = frequency; self.output_path = output_path
    def run(self):
        try:
            self.progress.emit("Generating Morse audio..."); self.progress_value.emit(10)
            morse = []
            for c in self.text.upper():
                if c in MORSE_ENCODE: morse.append(MORSE_ENCODE[c])
                elif c == ' ': morse.append('/')
            sr = 22050; dl = int(sr * 1.2 / self.wpm); samples = []
            for sym in ' '.join(morse):
                if sym == '.': samples.extend(self._tone(dl, sr)); samples.extend(self._silence(dl, sr))
                elif sym == '-': samples.extend(self._tone(dl*3, sr)); samples.extend(self._silence(dl, sr))
                elif sym == ' ': samples.extend(self._silence(dl*2, sr))
                elif sym == '/': samples.extend(self._silence(dl*6, sr))
            self.progress_value.emit(70)
            out = self.output_path or os.path.join(tempfile.gettempdir(), "morse_output.wav")
            self._write_wav(out, samples, sr); self.progress_value.emit(100)
            self.finished.emit(True, out, samples, sr)
        except Exception as e: self.progress.emit(f"Error: {str(e)}"); self.progress_value.emit(100); self.finished.emit(False, "", [], 0)
    def _tone(self, l, sr): return [int(32767*0.8*math.sin(2*math.pi*self.frequency*i/sr)) for i in range(l)]
    def _silence(self, l, sr): return [0]*l
    def _write_wav(self, fn, samples, sr):
        with wave.open(fn, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            for s in samples: w.writeframes(struct.pack('<h', max(-32768, min(32767, int(s)))))


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
        self._build(name)
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(140, int(180 * scale))
        h = max(56, int(70 * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(40 * scale), h + int(20 * scale))
    
    def _build(self, name):
        t = self.colors
        scale = layout_manager.font_scale()
        if self.layout() is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(
                int(14 * scale), int(12 * scale),
                int(14 * scale), int(12 * scale)
            )
            layout.setSpacing(int(4 * scale))
            self.name_label = QLabel(name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            layout.addWidget(self.name_label)
        else:
            if self.name_label is not None:
                self.name_label.setText(name)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(13 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._apply_scaled_size()
        self._build(self.mode_name)
        self.update()
        self.repaint()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self._placeholder = "Drag operation here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(200, text_w)
        max_w = min_w + int(80 * scale)
        h = max(72, int(90 * scale))
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
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        try:
            mode_id, mode_name = data.split(':', 1)
            self.mode_id = int(mode_id)
            self.mode_name = mode_name
            self._style_filled()
            self.update()
            self.repaint()
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, MorseAudioPage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(11, int(13 * scale))
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size, QFont.Weight.Bold))
            text = self.mode_name
        else:
            font_size = max(9, int(10 * scale))
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size))
            text = self._placeholder
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = painter.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, MorseAudioPage):
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


class WaveformWidget(QWidget):
    def __init__(self, theme_colors=None, parent=None):
        super().__init__(parent)
        self.samples = []
        self.sample_rate = 22050
        self.colors = theme_colors or {}
        self._apply_scaled_size()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        self.setMinimumHeight(max(150, int(150 * scale)))
    
    def set_audio(self, s, sr):
        self.samples = s
        self.sample_rate = sr
        self.update()
    
    def update_colors(self, c):
        self.colors = c
        self.update()
    
    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mid = h // 2
        scale = layout_manager.font_scale()
        painter.fillRect(self.rect(), QColor(self.colors.get('crust', '#1e1e1e')))
        if not self.samples:
            painter.setPen(QColor(self.colors.get('text_tertiary', '#888')))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", max(9, int(10 * scale))))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No audio")
            painter.end()
            return
        dur = len(self.samples) / self.sample_rate if self.sample_rate > 0 else 0
        painter.setPen(QColor(self.colors.get('text_tertiary', '#888')))
        painter.setFont(QFont("JetBrains Mono, Consolas, monospace", max(8, int(9 * scale))))
        painter.drawText(10, h - 8, f"Duration: {dur:.1f}s")
        painter.setPen(QColor(self.colors.get('success', '#4ade80')))
        step = max(1, len(self.samples) // w)
        for x in range(w):
            idx = x * step
            if idx >= len(self.samples):
                continue
            ch = self.samples[idx:idx + step]
            if ch:
                pk = max(abs(min(ch)), abs(max(ch)))
                y = int(pk / 32768 * mid * 0.9)
                painter.drawLine(x, mid - y, x, mid + y)
        painter.end()


class MorseAudioPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.generator = None
        self.decoder = None
        self._player_process = None
        self.mode_cards = []
        self.last_audio_path = ""
        self.audio_samples = []
        self.audio_sample_rate = 22050
        self.current_mode = None
        self._current_ref_category = 'LETTERS'
        self._current_ref_category_name = 'Letters A-Z'
        self._playback_timer = QTimer()
        self._playback_timer.timeout.connect(self._check_playback)
        self._playback_duration = 0
        self._playback_start_time = 0
        self.symbols_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'symbols', 'morse'
        )
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp and fp.lower().endswith('.wav'):
                if hasattr(self, 'audio_path_input') and self.audio_path_input is not None:
                    self.audio_path_input.setText(fp)
                    self._update_audio_preview(fp)
                break
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        bp = os.path.join(icons_dir, "back.png")
        if os.path.exists(bp):
            back_btn.setIcon(QIcon(bp))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Morse Code Audio Tools")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_reference_tab(), "Reference")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        self._apply_theme()
    
    def _create_setup_tab(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.mode_group = QGroupBox("1. Operation Mode")
        ml = QVBoxLayout()
        ml.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        t = self.theme.current
        for mid, mn in [(1, "Decode Audio"), (2, "Generate Audio")]:
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
        self.mode_group.setLayout(ml)
        l.addWidget(self.mode_group)
        
        self.options_group = QGroupBox("2. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        l.addWidget(self.options_group)
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        self.execute_btn.setEnabled(False)
        l.addWidget(self.execute_btn)
        
        l.addStretch()
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
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
        
        self.waveform_group = QGroupBox("Audio Waveform")
        wl = QVBoxLayout()
        self.waveform = WaveformWidget(self.theme.current)
        wl.addWidget(self.waveform)
        self.waveform_group.setLayout(wl)
        l.addWidget(self.waveform_group)
        
        ctr = QHBoxLayout()
        for nm, ic, sl in [
            ("play", "play.png", self._play_audio),
            ("pause", "pause.png", self._pause_audio),
            ("stop", "stop.png", self._stop_audio),
        ]:
            btn = QPushButton()
            btn.setIcon(self._icon(ic))
            btn.setIconSize(QSize(24, 24))
            btn.setObjectName("actionButton")
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(sl)
            ctr.addWidget(btn)
            setattr(self, f"{nm}_btn", btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_audio)
        ctr.addStretch()
        ctr.addWidget(self.export_btn)
        l.addLayout(ctr)
        
        self.dec_result_group = QGroupBox("Decoded Text")
        dl = QVBoxLayout()
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Output:"))
        rh.addStretch()
        cb = QPushButton("Copy")
        cb.setObjectName("actionButton")
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.clicked.connect(lambda: self._copy_from(self.dec_result))
        rh.addWidget(cb)
        dl.addLayout(rh)
        self.dec_result = QTextEdit()
        self.dec_result.setReadOnly(True)
        self.dec_result.setPlaceholderText("Decoded text will appear here...")
        dl.addWidget(self.dec_result)
        self.dec_result_group.setLayout(dl)
        l.addWidget(self.dec_result_group)
        return w
    
    def _create_reference_tab(self):
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)
        
        fltr_row = QHBoxLayout()
        self.ref_filter_btn = QToolButton()
        self.ref_filter_btn.setIcon(self._icon("filter.png"))
        self.ref_filter_btn.setIconSize(QSize(32, 32))
        self.ref_filter_btn.setText("Filter")
        self.ref_filter_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.ref_filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.ref_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ref_menu = QMenu(self.ref_filter_btn)
        cats = [
            ("Letters A-Z", 'LETTERS'), ("Numbers 0-9", 'NUMBERS'),
            ("Punctuation", 'PUNCT'), ("Prosigns", 'PROSIGNS'),
            ("Q-Codes", 'QCODES'), ("Cyrillic", 'CYRILLIC'),
            ("Hebrew", 'HEBREW'), ("Arabic", 'ARABIC'),
            ("Greek", 'GREEK'), ("Japanese Katakana", 'KATAKANA'),
        ]
        for cn, ci in cats:
            a = self.ref_menu.addAction(cn)
            a.triggered.connect(lambda checked, c=ci, n=cn: self._filter_reference(c, n))
        self.ref_filter_btn.setMenu(self.ref_menu)
        fltr_row.addWidget(self.ref_filter_btn)
        fltr_row.addStretch()
        outer.addLayout(fltr_row)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none;background:transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ref_grid_widget = QWidget()
        self.ref_grid_layout = QGridLayout(self.ref_grid_widget)
        self.ref_grid_layout.setSpacing(4)
        self.ref_grid_layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self.ref_grid_widget)
        outer.addWidget(scroll, 1)
        
        self.ref_symbols = {
            'LETTERS': list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            'NUMBERS': list('0123456789'),
            'PUNCT': ['DOT', 'COMMA', 'QMARK', 'EXCL', 'SLASH', 'AT', 'AMP', 'COLON', 'SEMI', 'EQ', 'PLUS', 'MINUS', 'UNDER', 'DQUOTE', 'DOLLAR', 'LPAREN', 'RPAREN', 'APOS'],
            'PROSIGNS': ['AR', 'AS', 'BK', 'BT', 'CL', 'CT', 'DO', 'KN', 'SK', 'SN', 'SOS', 'VE', 'HH', 'INT', 'KA', 'CQ', 'DE', 'K', 'R', 'AA', 'NIL', '73', '88', '99'],
            'QCODES': ['QRA', 'QRB', 'QRG', 'QRH', 'QRK', 'QRL', 'QRM', 'QRN', 'QRO', 'QRP', 'QRQ', 'QRS', 'QRT', 'QRU', 'QRV', 'QRX', 'QRZ', 'QSA', 'QSB', 'QSK', 'QSL', 'QSO', 'QSY', 'QTC', 'QTH', 'QTR'],
            'CYRILLIC': list('АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'),
            'HEBREW': list('אבגדהוזחטיכלמנסעפצקרשת'),
            'ARABIC': list('ابتثجحخدذرزسشصضطظعغفقكلمنهوي'),
            'GREEK': list('ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'),
            'KATAKANA': list('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヰヱヲン'),
        }
        self._filter_reference('LETTERS', 'Letters A-Z')
        return widget
    
    def _filter_reference(self, cat, cat_name):
        self._current_ref_category = cat
        self._current_ref_category_name = cat_name
        self.ref_filter_btn.setText("Filter")
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        while self.ref_grid_layout.count():
            item = self.ref_grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        symbols = self.ref_symbols.get(cat, [])
        if not symbols:
            return
        
        COLS = 10
        cell_w = max(80, int(100 * scale))
        cell_h = max(44, int(55 * scale))
        pix_w = max(72, int(90 * scale))
        pix_h = max(40, int(50 * scale))
        label_size = max(10, int(12 * scale))
        mono_size = max(9, int(10 * scale))
        
        for i, symbol in enumerate(symbols):
            row = (i // COLS) * 2
            col = i % COLS
            img_path = os.path.join(self.symbols_dir, f"{symbol}.png")
            
            letter_lbl = QLabel(symbol)
            letter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            symbol_lbl = QLabel()
            symbol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if os.path.exists(img_path):
                symbol_lbl.setPixmap(
                    QPixmap(img_path).scaled(
                        pix_w, pix_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
            else:
                symbol_lbl.setText(MORSE_ENCODE.get(symbol, '?'))
                symbol_lbl.setStyleSheet(
                    f"font-family:JetBrains Mono,monospace; font-size:{mono_size}px; color:{t['text']};"
                )
            symbol_lbl.setFixedSize(cell_w, cell_h)
            
            self.ref_grid_layout.addWidget(letter_lbl, row, col)
            self.ref_grid_layout.addWidget(symbol_lbl, row + 1, col)
        
        final_row = ((len(symbols) - 1) // COLS + 1) * 2
        self.ref_grid_layout.setRowStretch(final_row, 1)
        self._apply_ref_labels_theme(t)
        
        if hasattr(self, 'ref_filter_btn') and self.ref_filter_btn is not None:
            self.ref_filter_btn.setStyleSheet(
                f"QToolButton{{color:{t['text_secondary']};padding:4px 12px;border-radius:4px;"
                f"font-size:{max(11, int(12 * scale))}px;font-weight:500;background:transparent;border:none;}} "
                f"QToolButton:hover{{color:{t['text']};}}"
            )
        if hasattr(self, 'ref_menu') and self.ref_menu is not None:
            self.ref_menu.setStyleSheet(
                f"QMenu{{background-color:{t['base']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:8px;padding:{int(8 * scale)}px;}} "
                f"QMenu::item{{padding:{int(8 * scale)}px {int(36 * scale)}px {int(8 * scale)}px {int(16 * scale)}px;"
                f"border-radius:4px;font-size:{max(11, int(12 * scale))}px;}} "
                f"QMenu::item:selected{{background-color:{t['hover']};color:{t['text']};}}"
            )
    
    def _apply_ref_labels_theme(self, t):
        scale = layout_manager.font_scale()
        for i in range(self.ref_grid_layout.count()):
            item = self.ref_grid_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                lbl = item.widget()
                if lbl.pixmap() is None and not lbl.text().startswith("font-family"):
                    lbl.setStyleSheet(
                        f"font-weight:700; font-size:{max(10, int(12 * scale))}px; "
                        f"color:{t['text']}; background:transparent;"
                    )
    
    def _icon(self, name):
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        path = os.path.join(icons_dir, name)
        return QIcon(path) if os.path.exists(path) else QIcon()
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    self._clear_layout(sl)
    
    def _on_mode_dropped(self):
        self.current_mode = self.mode_slot.mode_id
        self._clear_layout(self.options_layout)
        for attr in ['audio_path_input', 'audio_preview', 'audio_info',
                     'text_input', 'wpm_spin', 'freq_spin']:
            if hasattr(self, attr):
                delattr(self, attr)
        scale = layout_manager.font_scale()
        
        if self.current_mode == 1:
            self.options_group.setVisible(True)
            self.options_group.setTitle("2. Audio File")
            self.audio_preview = QLabel()
            self.audio_preview.setFixedHeight(max(80, int(100 * scale)))
            self.audio_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.audio_preview.setText("Drag & drop a WAV file here\nor click Browse to select")
            self.options_layout.addWidget(self.audio_preview)
            
            fr = QHBoxLayout()
            self.audio_path_input = QLineEdit()
            self.audio_path_input.setReadOnly(True)
            self.audio_path_input.setPlaceholderText("Select WAV file...")
            browse = QPushButton("Browse")
            browse.setObjectName("actionButton")
            browse.setCursor(Qt.CursorShape.PointingHandCursor)
            browse.clicked.connect(self._browse_audio)
            fr.addWidget(self.audio_path_input, 1)
            fr.addWidget(browse)
            self.options_layout.addLayout(fr)
            
            self.audio_info = QLabel("")
            self.options_layout.addWidget(self.audio_info)
            self.execute_btn.setText("Decode Audio")
        
        elif self.current_mode == 2:
            self.options_group.setVisible(True)
            self.options_group.setTitle("2. Text & Options")
            self.text_input = QTextEdit()
            self.text_input.setPlaceholderText("Enter text to convert...\nExample: SOS")
            self.text_input.setMinimumHeight(max(50, int(60 * scale)))
            self.text_input.setMaximumHeight(max(70, int(80 * scale)))
            self.options_layout.addWidget(self.text_input)
            
            tbr = QHBoxLayout()
            paste_btn = QPushButton("Paste")
            paste_btn.setObjectName("actionButton")
            paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            paste_btn.clicked.connect(lambda: self._paste_to(self.text_input))
            clear_btn = QPushButton("Clear")
            clear_btn.setObjectName("dangerButton")
            clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            clear_btn.clicked.connect(self.text_input.clear)
            tbr.addWidget(paste_btn)
            tbr.addWidget(clear_btn)
            tbr.addStretch()
            self.options_layout.addLayout(tbr)
            
            orow = QHBoxLayout()
            orow.addWidget(QLabel("WPM:"))
            self.wpm_spin = QSpinBox()
            self.wpm_spin.setRange(5, 60)
            self.wpm_spin.setValue(20)
            orow.addWidget(self.wpm_spin)
            orow.addWidget(QLabel("Freq:"))
            self.freq_spin = QSpinBox()
            self.freq_spin.setRange(300, 2000)
            self.freq_spin.setValue(800)
            self.freq_spin.setSingleStep(50)
            orow.addWidget(self.freq_spin)
            orow.addStretch()
            self.options_layout.addLayout(orow)
            self.execute_btn.setText("Generate Audio")
        
        self.execute_btn.setEnabled(True)
        self._apply_theme()
    
    def _on_mode_cleared(self):
        self._clear_layout(self.options_layout)
        for attr in ['audio_path_input', 'audio_preview', 'audio_info',
                     'text_input', 'wpm_spin', 'freq_spin']:
            if hasattr(self, attr):
                delattr(self, attr)
        self.current_mode = None
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _paste_to(self, w):
        c = QApplication.clipboard().text()
        if c:
            if isinstance(w, QTextEdit):
                w.setPlainText(c)
            else:
                w.setText(c)
    
    def _copy_from(self, w):
        t = w.toPlainText() if isinstance(w, QTextEdit) else w.text()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Text copied!")
    
    def _browse_audio(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "Select WAV File", "", "WAV Files (*.wav);;All Files (*)"
        )
        if fp and hasattr(self, 'audio_path_input') and self.audio_path_input is not None:
            self.audio_path_input.setText(fp)
            self._update_audio_preview(fp)
    
    def _update_audio_preview(self, path):
        if not path or not os.path.exists(path):
            return
        fn = os.path.basename(path)
        sz = os.path.getsize(path)
        ss = f"{sz}B" if sz < 1024 else f"{sz/1024:.1f}KB" if sz < 1048576 else f"{sz/1048576:.1f}MB"
        if hasattr(self, 'audio_preview') and self.audio_preview is not None:
            self.audio_preview.setText(f"Audio File\n{fn}")
        if hasattr(self, 'audio_info') and self.audio_info is not None:
            self.audio_info.setText(f"Size: {ss}")
    
    def _execute(self):
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.dec_result.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        self.dec_result_group.setVisible(self.current_mode == 1)
        
        if self.current_mode == 1:
            path = self.audio_path_input.text().strip() if hasattr(self, 'audio_path_input') and self.audio_path_input is not None else ""
            if not path or not os.path.exists(path):
                QMessageBox.warning(self, "No File", "Please select a WAV file.")
                self.execute_btn.setEnabled(True)
                return
            self.last_audio_path = path
            try:
                with wave.open(path, 'rb') as w:
                    self.audio_sample_rate = w.getframerate()
                    raw = w.readframes(w.getnframes())
                self.audio_samples = list(struct.unpack('<' + 'h' * (len(raw) // 2), raw))
                self.waveform.set_audio(self.audio_samples, self.audio_sample_rate)
            except Exception:
                pass
            self.decoder = MorseAudioDecodeWorker(path)
            self.decoder.progress.connect(lambda m: self.status_output.append(m))
            self.decoder.progress_value.connect(self.status_progress.setValue)
            self.decoder.finished.connect(self._on_decode_finished)
            self.decoder.start()
        
        elif self.current_mode == 2:
            text = self.text_input.toPlainText().strip() if hasattr(self, 'text_input') and self.text_input is not None else ""
            if not text:
                QMessageBox.warning(self, "No Input", "Please enter text.")
                self.execute_btn.setEnabled(True)
                return
            wpm = self.wpm_spin.value() if hasattr(self, 'wpm_spin') and self.wpm_spin is not None else 20
            freq = self.freq_spin.value() if hasattr(self, 'freq_spin') and self.freq_spin is not None else 800
            self.generator = MorseAudioGenerator(text, wpm, freq)
            self.generator.progress.connect(lambda m: self.status_output.append(m))
            self.generator.progress_value.connect(self.status_progress.setValue)
            self.generator.finished.connect(self._on_generation_finished)
            self.generator.start()
    
    def _on_decode_finished(self, s, r):
        self.execute_btn.setEnabled(True)
        if s:
            self.status_output.append("✓ Decoding complete!")
            self.status_progress.setValue(100)
            self.dec_result.setText(r)
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"✗ Decoding failed: {r}")
    
    def _on_generation_finished(self, s, p, smp, sr):
        self.execute_btn.setEnabled(True)
        if s:
            self.last_audio_path = p
            self.audio_samples = smp
            self.audio_sample_rate = sr
            self.waveform.set_audio(smp, sr)
            self.status_output.append("✓ Audio generated!")
            self.status_progress.setValue(100)
            self.tabs.setCurrentIndex(2)
    
    def _play_audio(self):
        if not self.last_audio_path or not os.path.exists(self.last_audio_path):
            return
        self._stop_audio()
        try:
            self._playback_duration = (
                len(self.audio_samples) / self.audio_sample_rate if self.audio_sample_rate > 0 else 0
            )
            self._playback_start_time = time.time()
            if sys.platform == 'win32':
                os.startfile(self.last_audio_path)
            elif sys.platform == 'darwin':
                self._player_process = subprocess.Popen(['afplay', self.last_audio_path])
            else:
                if shutil.which('ffplay'):
                    self._player_process = subprocess.Popen(
                        ['ffplay', '-nodisp', '-autoexit', self.last_audio_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                elif shutil.which('aplay'):
                    self._player_process = subprocess.Popen(
                        ['aplay', self.last_audio_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                elif shutil.which('paplay'):
                    self._player_process = subprocess.Popen(
                        ['paplay', self.last_audio_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            if self._playback_duration > 0:
                self._playback_timer.start(500)
        except Exception as e:
            print(f"Play error: {e}")
    
    def _check_playback(self):
        if not self._player_process:
            self._playback_timer.stop()
            return
        if self._player_process.poll() is not None:
            self._player_process = None
            self._playback_timer.stop()
            return
        if time.time() - self._playback_start_time >= self._playback_duration + 0.5:
            self._stop_audio()
    
    def _pause_audio(self):
        if self._player_process and self._player_process.poll() is None:
            try:
                subprocess.run(['kill', '-STOP', str(self._player_process.pid)])
            except Exception:
                pass
        self._playback_timer.stop()
    
    def _stop_audio(self):
        self._playback_timer.stop()
        if self._player_process:
            try:
                if self._player_process.poll() is None:
                    self._player_process.terminate()
                self._player_process = None
            except Exception:
                pass
        if sys.platform == 'linux':
            subprocess.run(['pkill', '-9', 'aplay'], capture_output=True)
            subprocess.run(['pkill', '-9', 'paplay'], capture_output=True)
            subprocess.run(['pkill', '-9', 'ffplay'], capture_output=True)
    
    def _export_audio(self):
        if not self.last_audio_path or not os.path.exists(self.last_audio_path):
            QMessageBox.warning(self, "No Audio", "Generate or decode audio first.")
            return
        ep, _ = QFileDialog.getSaveFileName(
            self, "Export Audio", "morse_output.wav", "WAV Files (*.wav)"
        )
        if ep:
            shutil.copy2(self.last_audio_path, ep)
            QMessageBox.information(self, "Exported", f"Saved to:\n{ep}")
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}} "
            f"QTabBar::tab{{background-color:{t['crust']};color:{t['text_secondary']};"
            f"border:1px solid {t['border']};padding:{int(10 * scale)}px {int(28 * scale)}px;"
            f"margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;"
            f"font-size:{max(12, int(13 * scale))}px;font-weight:600;}} "
            f"QTabBar::tab:selected{{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}"
        )
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:{int(20 * scale)}px {int(16 * scale)}px {int(16 * scale)}px;"
            f"font-weight:600;font-size:{max(12, int(13 * scale))}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['mode_group', 'options_group', 'waveform_group', 'dec_result_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(12, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(12, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        if hasattr(self, 'execute_btn') and self.execute_btn is not None:
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['text_input', 'status_output']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(ts)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'dec_result') and self.dec_result is not None:
            try:
                self.dec_result.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;"
                    f"font-size:{max(14, int(18 * scale))}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;"
            f"padding:{int(8 * scale)}px {int(10 * scale)}px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        if hasattr(self, 'audio_path_input') and self.audio_path_input is not None:
            try:
                self.audio_path_input.setStyleSheet(input_style)
            except RuntimeError:
                pass
        
        spin_style = (
            f"QSpinBox{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;"
            f"padding:{int(6 * scale)}px {int(10 * scale)}px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['wpm_spin', 'freq_spin']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(spin_style)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setMinimumHeight(max(24, int(28 * scale)))
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;"
                f"height:{max(12, int(14 * scale))}px;text-align:center;"
                f"font-size:{max(9, int(10 * scale))}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'audio_preview') and self.audio_preview is not None:
            self.audio_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{max(12, int(13 * scale))}px;"
            )
        if hasattr(self, 'audio_info') and self.audio_info is not None:
            self.audio_info.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{max(10, int(11 * scale))}px;background:transparent;"
            )
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            self.mode_slot.update_colors(t)
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        if hasattr(self, 'waveform') and self.waveform is not None:
            self.waveform._apply_scaled_size()
            self.waveform.update_colors(t)
        
        if hasattr(self, 'ref_filter_btn') and self.ref_filter_btn is not None:
            self.ref_filter_btn.setStyleSheet(
                f"QToolButton{{color:{t['text_secondary']};padding:4px 12px;border-radius:4px;"
                f"font-size:{max(11, int(12 * scale))}px;font-weight:500;background:transparent;border:none;}} "
                f"QToolButton:hover{{color:{t['text']};}}"
            )
        if hasattr(self, 'ref_menu') and self.ref_menu is not None:
            self.ref_menu.setStyleSheet(
                f"QMenu{{background-color:{t['base']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:8px;padding:{int(8 * scale)}px;}} "
                f"QMenu::item{{padding:{int(8 * scale)}px {int(36 * scale)}px {int(8 * scale)}px {int(16 * scale)}px;"
                f"border-radius:4px;font-size:{max(11, int(12 * scale))}px;}} "
                f"QMenu::item:selected{{background-color:{t['hover']};color:{t['text']};}}"
            )
        
        if hasattr(self, 'ref_grid_layout'):
            self._apply_ref_labels_theme(t)
    
    def refresh_theme(self):
        self._apply_theme()
        if hasattr(self, 'ref_grid_layout'):
            self._filter_reference(self._current_ref_category, self._current_ref_category_name)