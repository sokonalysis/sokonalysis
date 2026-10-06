# gui/wifi_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QTextBrowser, QFrame,
    QApplication, QScrollArea, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import os, subprocess, shutil, threading, time, re, sys
from gui.layout_manager import layout_manager


class DraggableRuleCard(QFrame):
    def __init__(self, rule_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.rule_id = rule_id
        self.rule_name = name
        self.colors = theme_colors
        self.name_label = None
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(200, int(260 * scale))
        h = max(56, int(70 * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(60 * scale), h + int(20 * scale))
    
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
            self.name_label = QLabel(self.rule_name)
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
            mime.setText(f"{self.rule_id}:{self.rule_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class RuleDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.rule_id = None
        self.rule_name = None
        self._placeholder = "Drag rule here to start"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(240, text_w)
        max_w = min_w + int(100 * scale)
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
        return self.rule_id is not None
    
    def clear_slot(self):
        self.rule_id = None
        self.rule_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    
    def dropEvent(self, e):
        data = e.mimeData().text()
        try:
            rid, rn = data.split(':', 1)
            self.rule_id = int(rid)
            self.rule_name = rn
            self._style_filled()
            self.update()
            self.repaint()
            e.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, WiFiPage):
                p = p.parent()
            if p:
                p._on_rule_dropped()
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
            text = self.rule_name
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
        while p and not isinstance(p, WiFiPage):
            p = p.parent()
        if p:
            p._on_rule_cleared()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class ToolsInstaller(QThread):
    output = Signal(str)
    install_done = Signal(bool, str)
    
    def run(self):
        try:
            self.output.emit("Installing...")
            subprocess.run(["sudo", "apt", "update", "-qq"], capture_output=True, text=True, timeout=30)
            subprocess.run(
                ["sudo", "apt", "install", "-y", "john", "aircrack-ng"],
                capture_output=True, text=True, timeout=120
            )
            self.install_done.emit(True, "Ready")
        except Exception as e:
            self.install_done.emit(False, str(e))


class WiFiCrackWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    crack_done = Signal(bool, str)
    wifi_details = Signal(str, str, str, str)

    def __init__(self, handshake_path, wordlist_path, split_parts, rules):
        super().__init__()
        self.handshake_path = handshake_path
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.rules = rules
        self.stop_flag = threading.Event()
        self.work_dir = None

    def _jp(self):
        for p in ["john", "/usr/sbin/john", "/usr/bin/john"]:
            try:
                if subprocess.run([p], capture_output=True, timeout=3).returncode in [0, 1]:
                    return p
            except:
                continue
        return "john"

    def _h2j(self):
        for p in [
            "/usr/sbin/hccap2john", "/usr/bin/hccap2john",
            "/usr/share/john/hccap2john", "hccap2john"
        ]:
            if os.path.exists(p):
                return p
        return None

    def run(self):
        try:
            jp = self._jp()
            home = os.path.expanduser("~")
            self.work_dir = os.path.join(home, ".sokonalysis", "wifi_crack")
            os.makedirs(self.work_dir, exist_ok=True)
            for f in os.listdir(self.work_dir):
                if f.startswith("pot_") or f.startswith("sess_"):
                    os.remove(os.path.join(self.work_dir, f))
            
            self.progress.emit("Reading handshake...")
            r = subprocess.run(["aircrack-ng", self.handshake_path], capture_output=True, text=True, timeout=10)
            o = r.stdout + r.stderr
            pk, b, e, en = "Unknown", "Unknown", "Unknown", "Unknown"
            m = re.search(r'Read\s+(\d+)\s+packets', o)
            if m:
                pk = m.group(1)
            m = re.search(
                r'\d+\s+([0-9A-Fa-f:]{17})\s+(.+?)\s+(WPA\d*|WEP|OPN)\s*\(\d+\s+handshake',
                o
            )
            if m:
                b, e, en = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            self.wifi_details.emit(e, b, pk, en)
            self.progress.emit(f"ESSID: {e}, Encryption: {en}, Packets: {pk}")
            self.progress_value.emit(10)
            
            base = os.path.join(self.work_dir, "wifi_handshake")
            hccap = base + ".hccap"
            subprocess.run(
                ["aircrack-ng", self.handshake_path, "-J", base],
                capture_output=True, text=True, timeout=30
            )
            if not os.path.exists(hccap):
                hx = base + ".hccapx"
                if os.path.exists(hx):
                    hccap = hx
                elif self.handshake_path.endswith('.hccap'):
                    shutil.copy2(self.handshake_path, hccap)
                else:
                    self.crack_done.emit(False, "Conversion failed")
                    return
            self.progress.emit("Converted")
            self.progress_value.emit(20)
            
            h2j = self._h2j()
            if not h2j:
                self.crack_done.emit(False, "hccap2john not found")
                return
            
            hf = os.path.join(self.work_dir, "wifi_hash.txt")
            with open(hf, 'w') as out:
                cmd = ["python3", h2j, hccap] if h2j.endswith('.py') else [h2j, hccap]
                subprocess.run(cmd, stdout=out, text=True, timeout=10)
            self.progress.emit("Hash extracted")
            self.progress_value.emit(25)
            
            split_dir = os.path.join(home, ".sokonalysis", "wordlist_parts")
            os.makedirs(split_dir, exist_ok=True)
            marker = os.path.join(split_dir, ".info")
            need = True
            if os.path.exists(marker):
                try:
                    with open(marker) as f:
                        op, _, oparts = f.read().strip().split('|')
                        if op == self.wordlist_path and int(oparts) == self.split_parts:
                            need = False
                except:
                    pass
            if need:
                for f in os.listdir(split_dir):
                    if f.startswith('part_'):
                        os.remove(os.path.join(split_dir, f))
                wc = sum(1 for _ in open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') if _.strip())
                lpp = wc // self.split_parts
                rem = wc % self.split_parts
                self.progress.emit(f"Splitting {wc:,} words into {self.split_parts} parts...")
                with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as inf:
                    for i in range(self.split_parts):
                        pf = os.path.join(split_dir, f"part_{i+1}.txt")
                        n = lpp + (1 if i < rem else 0)
                        with open(pf, 'w', encoding='utf-8') as out:
                            for _ in range(n):
                                l = inf.readline()
                                if not l:
                                    break
                                out.write(l)
                with open(marker, 'w') as f:
                    f.write(f"{self.wordlist_path}|{wc}|{self.split_parts}")
            self.progress.emit(f"Wordlist ready ({self.split_parts} parts)")
            self.progress_value.emit(30)
            
            parts = [
                os.path.join(split_dir, f"part_{i+1}.txt")
                for i in range(self.split_parts)
                if os.path.exists(os.path.join(split_dir, f"part_{i+1}.txt"))
            ]
            rm = {
                "No rules (fastest)": [],
                "Standard rules (recommended)": ["--rules"],
                "All rules (thorough)": ["--rules=All"]
            }
            
            password = None
            pwd_lock = threading.Lock()
            running_procs = []
            procs_lock = threading.Lock()
            finished_emitted = threading.Event()
            timestamp = int(time.time() * 1000)
            
            def emit_finished_once(ok, msg):
                if finished_emitted.is_set():
                    return
                finished_emitted.set()
                try:
                    self.crack_done.emit(ok, msg)
                except:
                    pass
            
            def kill_all_procs():
                with procs_lock:
                    for proc in running_procs:
                        try:
                            if proc.poll() is None:
                                proc.terminate()
                        except:
                            pass
            
            def read_password_from_pot(pot_files):
                """Read the cracked password from pot files. Source of truth."""
                for pot_file in pot_files:
                    if not pot_file or not os.path.exists(pot_file):
                        continue
                    try:
                        with open(pot_file, 'r', errors='ignore') as f:
                            for line in f:
                                line = line.rstrip('\r\n')
                                if not line or line.startswith('#'):
                                    continue
                                if ':' not in line:
                                    continue
                                # WPA pot lines look like: hash:password
                                # hash may contain colons; password is last segment
                                pwd = line.rsplit(':', 1)[-1]
                                if not pwd:
                                    continue
                                if pwd.startswith('$'):
                                    continue
                                return pwd
                    except:
                        continue
                return None
            
            def crack_part(pf, idx):
                nonlocal password
                if self.stop_flag.is_set() or finished_emitted.is_set():
                    return
                
                pot = os.path.join(self.work_dir, f"pot_{idx+1}_{timestamp}")
                sess = os.path.join(self.work_dir, f"sess_{idx+1}_{timestamp}")
                
                cmd = [
                    jp, os.path.abspath(hf), "--format=wpapsk",
                    f"--wordlist={os.path.abspath(pf)}",
                    f"--pot={pot}", f"--session={sess}"
                ] + rm.get(self.rules, ["--rules"])
                
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                
                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, cwd=self.work_dir, creationflags=creationflags
                    )
                except Exception as e:
                    self.progress.emit(f"Failed to start john: {e}")
                    return
                
                with procs_lock:
                    running_procs.append(proc)
                
                saw_crack_hint = False
                
                try:
                    for line in iter(proc.stdout.readline, ''):
                        if self.stop_flag.is_set() or finished_emitted.is_set():
                            break
                        line = line.strip()
                        if not line:
                            continue
                        
                        if any(kw in line for kw in ['g/s', 'c/s', 'Progress', 'Cracked', 'password', 'DONE']):
                            self.progress.emit(f"Part {idx+1}: {line}")
                        
                        low = line.lower()
                        if ('cracked' in low
                                or ('done' in low and 'g ' in low)
                                or ('  (' in line and 'password' not in low
                                    and 'loaded' not in low
                                    and 'press' not in low
                                    and 'cost' not in low
                                    and 'using default' not in low
                                    and 'remaining' not in low)):
                            saw_crack_hint = True
                finally:
                    try:
                        if proc.poll() is None:
                            proc.terminate()
                    except:
                        pass
                    with procs_lock:
                        if proc in running_procs:
                            running_procs.remove(proc)
                    
                    # Pot file is the source of truth
                    if not finished_emitted.is_set() and saw_crack_hint:
                        pwd = read_password_from_pot([pot])
                        if pwd:
                            with pwd_lock:
                                if not password:
                                    password = pwd
                                    self.stop_flag.set()
                            kill_all_procs()
                            self.progress.emit(f"Password found: {pwd}")
                            emit_finished_once(True, password)
                            return
                    
                    if not finished_emitted.is_set():
                        self.progress.emit(f"Part {idx+1}/{len(parts)} done")
                        self.progress_value.emit(30 + int(((idx+1)/len(parts))*65))
            
            threads = []
            for idx, pf in enumerate(parts):
                if self.stop_flag.is_set():
                    break
                t = threading.Thread(target=crack_part, args=(pf, idx), daemon=True)
                threads.append(t)
                t.start()
                time.sleep(0.1)
            
            while not finished_emitted.is_set() and any(t.is_alive() for t in threads):
                time.sleep(0.1)
            
            if password and not finished_emitted.is_set():
                kill_all_procs()
                emit_finished_once(True, password)
            elif not finished_emitted.is_set():
                # Check all pot files as final fallback
                all_pots = [
                    os.path.join(self.work_dir, f"pot_{i+1}_{timestamp}")
                    for i in range(len(parts))
                ]
                pwd = read_password_from_pot(all_pots)
                if pwd:
                    emit_finished_once(True, pwd)
                else:
                    emit_finished_once(True, "No match found")
            
            self.progress_value.emit(100)
        except Exception as e:
            try:
                self.crack_done.emit(False, str(e))
            except:
                pass
    
    def stop(self):
        self.stop_flag.set()


class WiFiPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.handshake_path = ""
        self.worker = None
        self.installer = None
        self.rule_cards = []
        self.john_ok = self._chk("john")
        self.air_ok = self._chk("aircrack-ng")
        self._ui()
        self.setAcceptDrops(True)

    def _chk(self, cmd):
        try:
            return subprocess.run([cmd], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return False
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp and any(fp.lower().endswith(ext) for ext in ['.cap', '.pcap', '.pcapng', '.hccap']):
                self.handshake_path = fp
                self.handshake_path_input.setText(fp)
                self._update_file_preview(fp)
                self.start_btn.setEnabled(bool(self.wordlist_path) and self.john_ok)
                try:
                    r = subprocess.run(["aircrack-ng", fp], capture_output=True, text=True, timeout=5)
                    o = r.stdout + r.stderr
                    m = re.search(r'Read\s+(\d+)\s+packets', o)
                    if m:
                        self.pd.setText(m.group(1))
                    m = re.search(
                        r'\d+\s+([0-9A-Fa-f:]{17})\s+(.+?)\s+(WPA\d*|WEP|OPN)\s*\(\d+\s+handshake',
                        o
                    )
                    if m:
                        self.bd.setText(m.group(1).strip())
                        self.ed.setText(m.group(2).strip())
                        self.end.setText(m.group(3).strip())
                except:
                    pass
                break

    def _ui(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(40, 24, 40, 24)
        l.setSpacing(12)
        h = QHBoxLayout()
        b = QPushButton("  Back")
        b.setObjectName("backButton")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            b.setIcon(QIcon(back_icon_path))
            b.setIconSize(QSize(16, 16))
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(self.back_callback)
        b.setMaximumWidth(100)
        t = QLabel("Wi-Fi Handshake Cracking")
        t.setObjectName("pageTitle")
        h.addWidget(b)
        h.addWidget(t)
        h.addStretch()
        
        wl_container = QHBoxLayout()
        wl_container.setSpacing(4)
        self.wl_icon = QLabel()
        self.wl_icon.setFixedSize(18, 18)
        self.wl_icon.setStyleSheet("background:transparent;")
        self.wl_badge = QLabel()
        self._ub()
        wl_container.addWidget(self.wl_icon)
        wl_container.addWidget(self.wl_badge)
        h.addLayout(wl_container)
        
        tools_container = QHBoxLayout()
        tools_container.setSpacing(4)
        self.tools_icon = QLabel()
        self.tools_icon.setFixedSize(18, 18)
        self.tools_icon.setStyleSheet("background:transparent;")
        self.tb = QLabel()
        self._ut()
        tools_container.addWidget(self.tools_icon)
        tools_container.addWidget(self.tb)
        h.addLayout(tools_container)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._th(), "Setup")
        self.tabs.addTab(self._td(), "Details")
        self.tabs.addTab(self._ts(), "Status")
        self.tabs.addTab(self._tr(), "Results")
        self.tabs.addTab(self._tq(), "Requirements")
        l.addLayout(h)
        l.addWidget(self.tabs, 1)
        self._theme()

    def _ut(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        ok = self.john_ok and self.air_ok
        self.tb.setText("Tools Ready" if ok else "Tools Missing")
        c = t['success'] if ok else t['error']
        icon_path = os.path.join(icons_dir, "tools.png") if ok else os.path.join(icons_dir, "no.png")
        self.tb.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'tools_icon'):
            self.tools_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))

    def _theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(
            f"QTabWidget::pane{{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}} "
            f"QTabBar::tab{{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};"
            f"padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;"
            f"font-size:{int(13 * scale)}px;font-weight:600;}} "
            f"QTabBar::tab:selected{{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}"
        )
        
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
        for attr in ['rule_grp', 'handshake_grp', 'detail_grp', 'res_grp', 'req_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        input_style = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        if hasattr(self, 'handshake_path_input') and self.handshake_path_input is not None:
            self.handshake_path_input.setStyleSheet(input_style)
        for attr in ['ed', 'bd', 'end', 'pd']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'so') and self.so is not None:
            self.so.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'ro') and self.ro is not None:
            self.ro.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono;font-size:{int(18 * scale)}px;font-weight:700;}}"
            )
        if hasattr(self, 'rq') and self.rq is not None:
            self.rq.setStyleSheet(
                f"QTextBrowser{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-family:JetBrains Mono;font-size:{int(12 * scale)}px;}}"
            )
        if hasattr(self, 'pb') and self.pb is not None:
            self.pb.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        if hasattr(self, 'handshake_preview') and self.handshake_preview is not None:
            self.handshake_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        
        if hasattr(self, 'rule_slot') and self.rule_slot is not None:
            self.rule_slot.update_colors(t)
        for card in self.rule_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        self._ub()
        self._ut()
        self._uq()

    def _ub(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        self.wl_badge.setText("Wordlist Ready" if self.wordlist_path else "No Wordlist")
        c = t['success'] if self.wordlist_path else t['warning']
        icon_path = os.path.join(icons_dir, "wordlist.png") if self.wordlist_path else os.path.join(icons_dir, "no.png")
        self.wl_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'wl_icon'):
            self.wl_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))

    def _on_rule_dropped(self):
        self.handshake_grp.setVisible(True)
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(True)
    
    def _on_rule_cleared(self):
        self.handshake_grp.setVisible(False)
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(False)

    def _update_file_preview(self, filepath):
        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1048576:.1f} MB"
            self.handshake_preview.setText(f"{os.path.basename(filepath)}\n{size_str}")
        else:
            self.handshake_preview.setText("Drag & drop a handshake file here\nor click Browse to select")

    def _th(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.rule_grp = QGroupBox("1. Cracking Rules (Drag & Drop)")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        t = self.theme.current
        for rid, rn in [
            (0, "No rules (fastest)"),
            (1, "Standard rules (recommended)"),
            (2, "All rules (thorough)")
        ]:
            card = DraggableRuleCard(rid, rn, t)
            self.rule_cards.append(card)
            cr.addWidget(card)
        cr.addStretch()
        rl.addLayout(cr)
        dr = QHBoxLayout()
        self.rule_slot = RuleDropSlot(t)
        dr.addWidget(self.rule_slot)
        dr.addStretch()
        rl.addLayout(dr)
        self.rule_grp.setLayout(rl)
        l.addWidget(self.rule_grp)
        
        self.handshake_grp = QGroupBox("2. Handshake File")
        self.handshake_grp.setVisible(False)
        hl = QVBoxLayout()
        self.handshake_preview = QLabel("Drag & drop a handshake file here\nor click Browse to select")
        self.handshake_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.handshake_preview.setFixedHeight(100)
        hl.addWidget(self.handshake_preview)
        fr = QHBoxLayout()
        self.handshake_path_input = QLineEdit()
        self.handshake_path_input.setReadOnly(True)
        self.handshake_path_input.setPlaceholderText("No file selected...")
        btn = QPushButton("Browse")
        btn.setObjectName("actionButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._br)
        fr.addWidget(self.handshake_path_input)
        fr.addWidget(btn)
        hl.addLayout(fr)
        self.handshake_grp.setLayout(hl)
        l.addWidget(self.handshake_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.start_btn = QPushButton("Start Cracking")
        self.start_btn.setObjectName("actionButton")
        self.start_btn.setMinimumHeight(42)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._go)
        self.start_btn.setVisible(False)
        br.addWidget(self.stop_btn)
        br.addWidget(self.start_btn)
        l.addLayout(br)
        l.addStretch()
        
        scroll.setWidget(content)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return w

    def _td(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.detail_grp = QGroupBox("Network Details")
        dl = QFormLayout()
        dl.setSpacing(12)
        self.ed = QLineEdit()
        self.ed.setReadOnly(True)
        dl.addRow("ESSID:", self.ed)
        self.bd = QLineEdit()
        self.bd.setReadOnly(True)
        dl.addRow("BSSID:", self.bd)
        self.end = QLineEdit()
        self.end.setReadOnly(True)
        dl.addRow("Encryption:", self.end)
        self.pd = QLineEdit()
        self.pd.setReadOnly(True)
        dl.addRow("Packets:", self.pd)
        self.detail_grp.setLayout(dl)
        l.addWidget(self.detail_grp)
        l.addStretch()
        return w

    def _ts(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        self.pb.setValue(0)
        self.pb.setTextVisible(True)
        self.pb.setFormat("%p%")
        self.pb.setMinimumHeight(28)
        self.so = QTextEdit()
        self.so.setReadOnly(True)
        self.so.setPlaceholderText("Log...")
        l.addWidget(self.pb)
        l.addWidget(self.so)
        return w

    def _tr(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        self.res_grp = QGroupBox("Result")
        rl = QVBoxLayout()
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Wi-Fi Password:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        self.ro = QTextEdit()
        self.ro.setReadOnly(True)
        self.ro.setPlaceholderText("Password...")
        rl.addWidget(self.ro, 1)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w

    def _copy_result(self):
        text = self.ro.toPlainText().strip()
        if text and text != "No match found":
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Password copied to clipboard!")

    def _tq(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(30, 24, 30, 24)
        l.setSpacing(14)
        self.req_group = QGroupBox("Required Tools")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        self.rq = QTextBrowser()
        self.rq.setOpenExternalLinks(False)
        rl.addWidget(self.rq)
        self.ib = QPushButton("Install Requirements")
        self.ib.setObjectName("actionButton")
        self.ib.setMinimumHeight(40)
        self.ib.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ib.clicked.connect(self._in)
        self.rs = QLabel("")
        rl.addWidget(self.ib)
        rl.addWidget(self.rs)
        self.req_group.setLayout(rl)
        l.addWidget(self.req_group)
        l.addStretch()
        self._uq()
        return w

    def _uq(self):
        t = self.theme.current
        h = ""
        for n, o in [("john", self.john_ok), ("aircrack-ng", self.air_ok)]:
            c = t['success'] if o else t['error']
            h += f"<h3 style='color:{c};'>{n}</h3>"
        h += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install john aircrack-ng</p>"
        self.rq.setHtml(h)
        all_ok = self.john_ok and self.air_ok
        self.ib.setEnabled(not all_ok)
        self.ib.setText("All Tools Installed" if all_ok else "Install Requirements")

    def _br(self):
        fp, _ = QFileDialog.getOpenFileName(
            self, "Select Handshake", "",
            "Handshake (*.cap *.pcap *.pcapng);;All (*)"
        )
        if fp:
            self.handshake_path = fp
            self.handshake_path_input.setText(fp)
            self._update_file_preview(fp)
            self.start_btn.setEnabled(bool(self.wordlist_path) and self.john_ok)
            try:
                r = subprocess.run(["aircrack-ng", fp], capture_output=True, text=True, timeout=5)
                o = r.stdout + r.stderr
                m = re.search(r'Read\s+(\d+)\s+packets', o)
                if m:
                    self.pd.setText(m.group(1))
                m = re.search(
                    r'\d+\s+([0-9A-Fa-f:]{17})\s+(.+?)\s+(WPA\d*|WEP|OPN)\s*\(\d+\s+handshake',
                    o
                )
                if m:
                    self.bd.setText(m.group(1).strip())
                    self.ed.setText(m.group(2).strip())
                    self.end.setText(m.group(3).strip())
            except:
                pass

    def _in(self):
        if QMessageBox.question(
            self, "Install", "Install john & aircrack-ng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self.ib.setEnabled(False)
        self.ib.setText("Installing...")
        self.installer = ToolsInstaller()
        self.installer.output.connect(lambda m: self.rs.setText(m))
        self.installer.install_done.connect(self._id)
        self.installer.start()

    def _id(self, ok, msg):
        if ok:
            self.john_ok = self._chk("john")
            self.air_ok = self._chk("aircrack-ng")
            self._ut()
            self._uq()
        else:
            self.ib.setEnabled(True)
            self.ib.setText("Retry")

    def set_wordlist_config(self, wp, sp):
        self.wordlist_path = wp
        self.split_parts = sp
        self._ub()
        self.start_btn.setEnabled(bool(self.handshake_path) and self.john_ok)

    def _go(self):
        if not self.rule_slot.is_filled():
            QMessageBox.warning(self, "No Rules", "Please drag a rule first.")
            return
        if not self.handshake_path:
            QMessageBox.warning(self, "No File", "Please select a handshake file.")
            return
        if not self.wordlist_path:
            QMessageBox.warning(self, "No Wordlist", "Please configure a wordlist from Configurations menu.")
            return
        if not os.path.exists(self.wordlist_path):
            QMessageBox.warning(self, "Wordlist Not Found", f"Wordlist file not found:\n{self.wordlist_path}")
            return
        self.tabs.setCurrentIndex(2)
        self.so.clear()
        self.ro.clear()
        self.pb.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        rules = self.rule_slot.rule_name if self.rule_slot.is_filled() else "Standard rules (recommended)"
        self.worker = WiFiCrackWorker(self.handshake_path, self.wordlist_path, self.split_parts, rules)
        self.worker.progress.connect(lambda m: self.so.append(m))
        self.worker.progress_value.connect(self.pb.setValue)
        self.worker.crack_done.connect(self._dn)
        self.worker.wifi_details.connect(
            lambda e, b, p, en: (
                self.ed.setText(e),
                self.bd.setText(b),
                self.pd.setText(p),
                self.end.setText(en)
            )
        )
        self.worker.start()

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self.so.append("Stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _dn(self, ok, msg):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pb.setValue(100)
        if ok:
            if msg == "No match found":
                self.ro.setText("No match found")
            else:
                self.ro.setText(msg)
                self.tabs.setCurrentIndex(3)
        else:
            self.ro.setText(f"Error: {msg}")

    def refresh_theme(self):
        self.setStyleSheet("")
        self._theme()