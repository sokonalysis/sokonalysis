# gui/linux_live_system.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QMessageBox, QProgressBar,
    QTextBrowser, QFrame, QApplication, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QRadioButton, QButtonGroup, QTableWidgetSelectionRange, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import os, subprocess, shutil, threading, time, tempfile, sys
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
            while p and not isinstance(p, LiveSystemPage):
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
        while p and not isinstance(p, LiveSystemPage):
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


class LiveSystemToolsInstaller(QThread):
    output = Signal(str)
    finished = Signal(bool, str)
    
    def run(self):
        try:
            self.output.emit("Installing john...")
            subprocess.run(["sudo", "apt", "update", "-qq"], capture_output=True, text=True, timeout=30)
            subprocess.run(["sudo", "apt", "install", "-y", "john", "policykit-1"], capture_output=True, text=True, timeout=120)
            self.finished.emit(True, "Ready")
        except Exception as e:
            self.finished.emit(False, str(e))


class LiveSystemWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    users_found = Signal(list)
    
    def __init__(self, wordlist_path, split_parts, rules, target_user=None):
        super().__init__()
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.rules = rules
        self.target_user = target_user
        self.stop_flag = threading.Event()
        self.temp_dir = None
        self.hash_file = None
        self.passwd_path = None
        self.shadow_path = None
    
    def _find_john(self):
        for p in ["john", "/usr/sbin/john", "/usr/bin/john"]:
            try:
                if subprocess.run([p], capture_output=True, timeout=3).returncode in [0, 1]:
                    return p
            except:
                continue
        return "john"
    
    def _find_unshadow(self):
        for p in ["unshadow", "/usr/sbin/unshadow", "/usr/bin/unshadow", "/usr/local/sbin/unshadow", "/usr/local/bin/unshadow"]:
            try:
                if subprocess.run([p], capture_output=True, timeout=3).returncode in [0, 1, 2]:
                    return p
            except:
                continue
        try:
            r = subprocess.run(["which", "unshadow"], capture_output=True, text=True, timeout=3)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except:
            pass
        return None
    
    def _detect_hash_type(self, h):
        if h.startswith('$1$'):
            return "MD5"
        if h.startswith('$2a$') or h.startswith('$2b$') or h.startswith('$2y$'):
            return "Blowfish"
        if h.startswith('$5$'):
            return "SHA-256"
        if h.startswith('$6$'):
            return "SHA-512"
        if h.startswith('$y$'):
            return "Yescrypt"
        if h.startswith('$argon2'):
            return "Argon2"
        return "Unknown"
    
    def _parse_users(self):
        users = []
        try:
            with open(self.passwd_path, 'r', errors='ignore') as f:
                passwd_lines = f.readlines()
            with open(self.shadow_path, 'r', errors='ignore') as f:
                shadow_lines = f.readlines()
            shadow_dict = {}
            for line in shadow_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        shadow_dict[parts[0]] = parts[1]
            for line in passwd_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        if username in shadow_dict:
                            h = shadow_dict[username]
                            if h and h not in ['*', '!', '!!', '!*', 'x', '']:
                                users.append({'username': username, 'uid': parts[2], 'hash': h})
            return users
        except:
            return []
    
    def _create_hash_file(self):
        unshadow_bin = self._find_unshadow()
        if not unshadow_bin:
            self.progress.emit("unshadow not found - install the 'john' package (it bundles unshadow)")
            return 0

        try:
            result = subprocess.run([unshadow_bin, self.passwd_path, self.shadow_path],
                                     capture_output=True, text=True, timeout=30)
        except Exception as e:
            self.progress.emit(f"unshadow failed to run: {e}")
            return 0

        output = result.stdout.strip()
        if not output:
            err = result.stderr.strip()
            self.progress.emit(f"unshadow produced no output{': ' + err if err else ''}")
            return 0

        lines = [l for l in output.split('\n') if l.strip()]
        usable = []
        for line in lines:
            parts = line.split(':')
            if len(parts) < 2:
                continue
            h = parts[1]
            if not h or h in ['*', '!', '!!', '!*', 'x', '']:
                continue
            if self.target_user and parts[0] != self.target_user:
                continue
            usable.append(line)

        if not usable:
            self.progress.emit("No crackable accounts left after filtering")
            return 0

        with open(self.hash_file, 'w') as out:
            out.write('\n'.join(usable) + '\n')

        self.progress.emit(f"Created {len(usable)} hash(es) for cracking (via unshadow)")
        return len(usable)
    
    def _prepare_wordlist(self):
        home = os.path.expanduser("~")
        split_dir = os.path.join(home, ".sokonalysis", "live_parts")
        os.makedirs(split_dir, exist_ok=True)
        
        marker = os.path.join(split_dir, ".info")
        need_split = True
        
        if os.path.exists(marker):
            try:
                with open(marker) as f:
                    ver, op, _, oparts = f.read().strip().split('|')
                    if ver == "v2" and op == self.wordlist_path and int(oparts) == self.split_parts:
                        need_split = False
            except:
                pass
        
        if need_split:
            for f in os.listdir(split_dir):
                if f.startswith('part_'):
                    os.remove(os.path.join(split_dir, f))
            
            wc = sum(1 for _ in open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') if _.strip())
            lpp, rem = wc // self.split_parts, wc % self.split_parts
            self.progress.emit(f"Splitting {wc:,} words into {self.split_parts} parts...")
            
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as inf:
                non_blank_lines = (line for line in inf if line.strip())
                for i in range(self.split_parts):
                    pf = os.path.join(split_dir, f"part_{i+1}.txt")
                    n = lpp + (1 if i < rem else 0)
                    with open(pf, 'w', encoding='utf-8') as out:
                        for _ in range(n):
                            try:
                                line = next(non_blank_lines)
                            except StopIteration:
                                break
                            out.write(line)
            
            with open(marker, 'w') as f:
                f.write(f"v2|{self.wordlist_path}|{wc}|{self.split_parts}")
        
        return [
            os.path.join(split_dir, f"part_{i+1}.txt")
            for i in range(self.split_parts)
            if os.path.exists(os.path.join(split_dir, f"part_{i+1}.txt"))
        ]
    
    def run(self):
        try:
            if sys.platform != "linux":
                self.finished.emit(False, "Live system cracking requires Linux (needs unshadow + the system's crypt library)")
                return

            jp = self._find_john()
            home = os.path.expanduser("~")

            self.progress.emit("Reading local system accounts...")
            self.progress_value.emit(5)

            try:
                with open('/etc/passwd', 'r', errors='ignore') as f:
                    passwd_content = f.read()
                with open('/etc/shadow', 'r', errors='ignore') as f:
                    shadow_content = f.read()
            except Exception as e:
                self.finished.emit(False, f"Could not read system files: {e}")
                return

            self.temp_dir = tempfile.mkdtemp(prefix="sokonalysis_live_")
            self.passwd_path = os.path.join(self.temp_dir, "passwd.copy")
            self.shadow_path = os.path.join(self.temp_dir, "shadow.copy")
            with open(self.passwd_path, 'w') as f:
                f.write(passwd_content)
            with open(self.shadow_path, 'w') as f:
                f.write(shadow_content)
            try:
                os.chmod(self.shadow_path, 0o600)
            except:
                pass

            users = self._parse_users()
            for u in users:
                u['hash_type'] = self._detect_hash_type(u['hash'])
            self.users_found.emit(users)

            if not users:
                self.finished.emit(False, "No users with crackable password hashes found")
                return

            self.hash_file = os.path.join(self.temp_dir, "hashes.txt")

            self.progress.emit("Creating hash file...")
            self.progress_value.emit(10)
            hashes_written = self._create_hash_file()
            if hashes_written == 0:
                self.finished.emit(False, "No crackable password hashes found (check unshadow output above)")
                return
            self.progress_value.emit(20)

            format_args = ["--format=crypt"]

            self.progress.emit("Preparing wordlist...")
            parts = self._prepare_wordlist()
            self.progress_value.emit(30)

            work_dir = os.path.join(home, ".sokonalysis", "live_work")
            os.makedirs(work_dir, exist_ok=True)
            for f in os.listdir(work_dir):
                if f.endswith('.rec') or f.endswith('.log'):
                    try:
                        os.remove(os.path.join(work_dir, f))
                    except:
                        pass

            rules_map = {
                "No rules (fastest)": [],
                "Standard rules (recommended)": ["--rules"],
                "All rules (thorough)": ["--rules=All"]
            }
            password = None
            cracked_user = None
            pwd_lock = threading.Lock()
            timestamp = int(time.time() * 1000)
            running_procs = []
            procs_lock = threading.Lock()
            finished_emitted = threading.Event()

            def emit_finished_once(ok, msg):
                if finished_emitted.is_set():
                    return
                finished_emitted.set()
                try:
                    self.finished.emit(ok, msg)
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

            def crack_part(pf, idx):
                nonlocal password, cracked_user
                if self.stop_flag.is_set() or finished_emitted.is_set():
                    return

                pot = os.path.join(work_dir, f"pot_{idx+1}_{timestamp}")
                sess = os.path.join(work_dir, f"sess_{idx+1}_{timestamp}")

                cmd = [
                    jp, os.path.abspath(self.hash_file),
                    f"--wordlist={os.path.abspath(pf)}",
                    f"--pot={pot}", f"--session={sess}"
                ] + format_args + rules_map.get(self.rules, ["--rules"])

                env = os.environ.copy()
                env["OMP_NUM_THREADS"] = "1"

                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, env=env
                    )
                except Exception as e:
                    self.progress.emit(f"Failed to start john: {e}")
                    return

                with procs_lock:
                    running_procs.append(proc)

                try:
                    for line in iter(proc.stdout.readline, ''):
                        if self.stop_flag.is_set() or finished_emitted.is_set():
                            break
                        line = line.strip()
                        if line:
                            self.progress.emit(line)

                            # Immediate parse of john's crack line: "PASSWORD   (username)"
                            if '(' in line and ')' in line and not line.startswith('0 password'):
                                low = line.lower()
                                if ('loaded' not in low and 'press' not in low
                                        and 'cost' not in low and 'using default' not in low
                                        and 'remaining' not in low):
                                    try:
                                        pwd_part, user_part = line.rsplit('(', 1)
                                        candidate = pwd_part.strip()
                                        username_found = user_part.rstrip(')').strip()
                                        # Remove trailing extra columns like "1g 0:00:00:02 DONE"
                                        if candidate and ' ' in candidate:
                                            # Some lines are "password  (user)  1g 0:00:00:02 DONE"
                                            # rsplit on '(' handles the user already
                                            pass
                                        if candidate and not candidate.startswith('$') and len(candidate) < 128:
                                            with pwd_lock:
                                                if not password:
                                                    password = candidate
                                                    cracked_user = username_found
                                                    self.stop_flag.set()
                                            kill_all_procs()
                                            self.progress.emit("Password found!")
                                            result = f"User: {cracked_user}\nPassword: {password}"
                                            emit_finished_once(True, result)
                                            return
                                    except Exception:
                                        pass
                finally:
                    try:
                        if proc.poll() is None:
                            proc.terminate()
                    except:
                        pass
                    with procs_lock:
                        if proc in running_procs:
                            running_procs.remove(proc)

                    # Fallback: check pot file in case stdout parse missed
                    if not finished_emitted.is_set() and os.path.exists(pot):
                        try:
                            with open(pot, 'r', errors='ignore') as f:
                                for line in f:
                                    line = line.strip()
                                    if ':' in line and not line.startswith('#'):
                                        pot_parts = line.split(':')
                                        if len(pot_parts) >= 2:
                                            candidate = pot_parts[1]
                                            if (candidate and not candidate.startswith('$')
                                                    and len(candidate) < 128):
                                                with pwd_lock:
                                                    if not password:
                                                        password = candidate
                                                        cracked_user = pot_parts[0]
                                                        self.stop_flag.set()
                                                kill_all_procs()
                                                self.progress.emit("Password found!")
                                                result = f"User: {cracked_user}\nPassword: {password}"
                                                emit_finished_once(True, result)
                                                return
                        except:
                            pass

                    self.progress.emit(f"Part {idx+1}/{len(parts)} done")
                    self.progress_value.emit(30 + int(((idx+1)/len(parts))*65))

            threads = []
            for idx, pf in enumerate(parts):
                t = threading.Thread(target=crack_part, args=(pf, idx), daemon=True)
                threads.append(t)
                t.start()
                time.sleep(0.3)

            # Wait until finished is emitted or all threads exit
            while not finished_emitted.is_set() and any(t.is_alive() for t in threads):
                time.sleep(0.2)

            # Safety: if we have a password but finished wasn't emitted yet
            if password and not finished_emitted.is_set():
                kill_all_procs()
                emit_finished_once(True, f"User: {cracked_user}\nPassword: {password}")
            elif not finished_emitted.is_set():
                # No match - verify with --show
                show_cmd = [jp, os.path.abspath(self.hash_file), "--show"] + format_args
                try:
                    show = subprocess.run(show_cmd, capture_output=True, text=True, timeout=15)
                    if show.stdout.strip() and "password hash" not in show.stdout.lower():
                        parsed_results = []
                        for line in show.stdout.strip().split('\n'):
                            if ':' in line and not line.startswith('0 password'):
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    username = parts[0]
                                    password_found = parts[1]
                                    if (password_found and not password_found.startswith('$')
                                            and len(password_found) < 128):
                                        parsed_results.append(
                                            f"User: {username}\nPassword: {password_found}"
                                        )
                        if parsed_results:
                            emit_finished_once(True, '\n\n'.join(parsed_results))
                        else:
                            emit_finished_once(True, "No match found")
                    else:
                        emit_finished_once(True, "No match found")
                except Exception as e:
                    emit_finished_once(False, str(e))

            self.progress_value.emit(100)

        except Exception as e:
            try:
                self.finished.emit(False, str(e))
            except:
                pass
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
    
    def stop(self):
        self.stop_flag.set()


class LiveSystemPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.worker = None
        self.installer = None
        self.rule_cards = []
        self.john_ok = self._chk("john")
        self.users_list = []
        self.selected_user = None
        self.radio_group = None
        self._ui()
    
    def _chk(self, cmd):
        try:
            return subprocess.run([cmd], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return False
    
    def _ui(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(40, 24, 40, 24)
        l.setSpacing(12)
        
        h = QHBoxLayout()
        b = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            b.setIcon(QIcon(back_icon_path))
            b.setIconSize(QSize(16, 16))
        b.setObjectName("backButton")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(self.back_callback)
        b.setMaximumWidth(100)
        
        t = QLabel("Live System Password Cracking")
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
        
        john_container = QHBoxLayout()
        john_container.setSpacing(4)
        self.john_icon = QLabel()
        self.john_icon.setFixedSize(18, 18)
        self.john_icon.setStyleSheet("background:transparent;")
        self.tb = QLabel()
        self._ut()
        john_container.addWidget(self.john_icon)
        john_container.addWidget(self.tb)
        h.addLayout(john_container)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._th(), "Setup")
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
        ok = self.john_ok
        self.tb.setText("John Ready" if ok else "John Missing")
        c = t['success'] if ok else t['error']
        icon_path = os.path.join(icons_dir, "jonny.png") if ok else os.path.join(icons_dir, "no.png")
        self.tb.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'john_icon'):
            self.john_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {t['border']}; border-radius: 8px; background: {t['base']}; }}
            QTabBar::tab {{ background: {t['crust']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; padding: 10px 28px; margin-right: 2px; border-top-left-radius: 7px; border-top-right-radius: 7px; font-size: {int(13 * scale)}px; font-weight: 600; }}
            QTabBar::tab:selected {{ background: {t['base']}; color: {t['text']}; border-bottom-color: transparent; }}
        """)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{ background: {t['crust']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 10px; padding: {int(14 * scale)}px; font-weight: 700; font-size: {int(15 * scale)}px; }}
                        QPushButton:hover {{ background: {t['surface0']}; }}
                    """)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{ background: {t['crust']}; color: {t['error']}; border: 1px solid {t['border']}; border-radius: 10px; padding: {int(14 * scale)}px; font-weight: 700; font-size: {int(15 * scale)}px; }}
                        QPushButton:hover {{ background: {t['surface0']}; }}
                    """)
            except RuntimeError:
                pass
        
        gs = f"""
            QGroupBox {{ color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; margin-top: 14px; padding: 20px 16px 16px; font-weight: 600; font-size: {int(13 * scale)}px; }}
            QGroupBox::title {{ left: 14px; padding: 0 8px; color: {t['text']}; }}
        """
        for attr in ['rule_grp', 'users_grp', 'res_grp', 'req_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'so') and self.so is not None:
            self.so.setStyleSheet(
                f"QTextEdit {{ background: {t['crust']}; color: {t['text']}; "
                f"border: 1px solid {t['border']}; border-radius: 6px; padding: 10px; "
                f"font-family: JetBrains Mono; font-size: {int(13 * scale)}px; }}"
            )
        if hasattr(self, 'ro') and self.ro is not None:
            self.ro.setStyleSheet(
                f"QTextEdit {{ background: {t['crust']}; color: {t['success']}; "
                f"border: 1px solid {t['border']}; border-radius: 6px; padding: 16px; "
                f"font-family: JetBrains Mono; font-size: {int(18 * scale)}px; font-weight: 700; }}"
            )
        if hasattr(self, 'rq') and self.rq is not None:
            self.rq.setStyleSheet(
                f"QTextBrowser {{ background: {t['crust']}; color: {t['text']}; "
                f"border: 1px solid {t['border']}; border-radius: 6px; padding: 12px; "
                f"font-family: JetBrains Mono; font-size: {int(12 * scale)}px; }}"
            )
        if hasattr(self, 'pb') and self.pb is not None:
            self.pb.setStyleSheet(
                f"QProgressBar {{ background: {t['surface0']}; border: none; border-radius: 4px; "
                f"height: {int(14 * scale)}px; text-align: center; font-size: {int(10 * scale)}px; font-weight: 600; }} "
                f"QProgressBar::chunk {{ background: {t['success']}; border-radius: 4px; }}"
            )
        
        if hasattr(self, 'users_table') and self.users_table is not None:
            self.users_table.setStyleSheet(f"""
                QTableWidget {{
                    background: {t['crust']};
                    color: {t['text']};
                    border: 1px solid {t['border']};
                    border-radius: 6px;
                    gridline-color: {t['border']};
                    font-family: JetBrains Mono;
                    font-size: {int(12 * scale)}px;
                }}
                QTableWidget::item {{
                    padding: {int(8 * scale)}px;
                    border-bottom: 1px solid {t['border']};
                }}
                QTableWidget::item:selected {{
                    background: {t['hover']};
                    color: {t['text']};
                }}
                QTableWidget::item:alternate {{
                    background: {t['surface0']};
                }}
                QHeaderView::section {{
                    background: {t['surface0']};
                    color: {t['text']};
                    padding: {int(8 * scale)}px;
                    border: 1px solid {t['border']};
                    font-weight: 600;
                    font-family: JetBrains Mono;
                    font-size: {int(12 * scale)}px;
                }}
                QRadioButton {{
                    color: {t['text']};
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {t['border']};
                    background: {t['crust']};
                }}
                QRadioButton::indicator:checked {{
                    border: 2px solid {t['accent']};
                    background: {t['accent']};
                }}
            """)
        
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
        self.users_grp.setVisible(True)
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(True)
        self._load_users()
    
    def _on_rule_cleared(self):
        self.users_grp.setVisible(False)
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(False)
    
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
        
        self.users_grp = QGroupBox("2. System Users")
        self.users_grp.setVisible(False)
        ul = QVBoxLayout()
        
        self.user_count_label = QLabel("")
        self.user_count_label.setStyleSheet(
            f"color: {self.theme.current['text_secondary']}; font-size: 12px;"
        )
        ul.addWidget(self.user_count_label)
        
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels(["", "Full Name", "Username", "Role", "ID", "Hash Type"])
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.users_table.setColumnWidth(0, 40)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setMinimumHeight(250)
        self.users_table.setMaximumHeight(450)
        self.users_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setShowGrid(True)
        
        ul.addWidget(self.users_table)
        self.users_grp.setLayout(ul)
        l.addWidget(self.users_grp)
        
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
        self.so.setPlaceholderText("Cracking log...")
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
        rh.addWidget(QLabel("Cracked Passwords:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        self.ro = QTextEdit()
        self.ro.setReadOnly(True)
        self.ro.setPlaceholderText("Password will appear here...")
        rl.addWidget(self.ro, 1)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _copy_result(self):
        text = self.ro.toPlainText().strip()
        if text and text != "No match found in wordlist":
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied to clipboard!")
    
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
        for n, o in [("john", self.john_ok)]:
            c = t['success'] if o else t['error']
            h += f"<h3 style='color:{c};'>{n}</h3>"
        h += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install john (bundles unshadow)</p>"
        if sys.platform != "linux":
            h += f"<p style='font-size:12px;color:{t['error']};font-weight:600;'>This feature only works on Linux — it relies on the system's crypt(3) library via John's --format=crypt, which has no equivalent on Windows/macOS.</p>"
        self.rq.setHtml(h)
        self.ib.setEnabled(not self.john_ok and sys.platform == "linux")
        self.ib.setText("All Tools Installed" if self.john_ok else "Install Requirements")
    
    def _get_full_name(self, gecos):
        if gecos:
            parts = gecos.split(',')
            if parts[0].strip():
                return parts[0].strip()
        return ""
    
    def _get_role(self, uid, username):
        try:
            uid_int = int(uid)
            if uid_int == 0:
                return "Root"
            elif uid_int < 1000:
                return "System"
            elif uid_int >= 1000:
                try:
                    with open('/etc/group', 'r', errors='ignore') as f:
                        group_lines = f.readlines()
                    
                    sudo_groups = ['sudo', 'wheel', 'admin']
                    for line in group_lines:
                        parts = line.strip().split(':')
                        if len(parts) >= 4:
                            group_name = parts[0]
                            if group_name in sudo_groups:
                                members = parts[3].split(',')
                                if username in members:
                                    return "Administrator"
                except:
                    pass
                return "Standard"
        except:
            pass
        return "Standard"
    
    def _load_users(self):
        try:
            with open('/etc/passwd', 'r', errors='ignore') as f:
                passwd_lines = f.readlines()
            with open('/etc/shadow', 'r', errors='ignore') as f:
                shadow_lines = f.readlines()
            
            shadow_dict = {}
            for line in shadow_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        shadow_dict[parts[0]] = parts[1]
            
            self.users_list = []
            for line in passwd_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        if username in shadow_dict:
                            h = shadow_dict[username]
                            if h and h not in ['*', '!', '!!', '!*', 'x', ''] and not h.startswith('!'):
                                ht = "Unknown"
                                if h.startswith('$1$'):
                                    ht = "MD5"
                                elif h.startswith('$2a$') or h.startswith('$2b$') or h.startswith('$2y$'):
                                    ht = "Blowfish"
                                elif h.startswith('$5$'):
                                    ht = "SHA-256"
                                elif h.startswith('$6$'):
                                    ht = "SHA-512"
                                elif h.startswith('$y$'):
                                    ht = "Yescrypt"
                                
                                full_name = self._get_full_name(parts[4])
                                role = self._get_role(parts[2], username)
                                
                                self.users_list.append({
                                    'full_name': full_name,
                                    'username': username,
                                    'role': role,
                                    'uid': parts[2],
                                    'hash_type': ht,
                                    'hash': h
                                })
            
            self.user_count_label.setText(
                f"Found {len(self.users_list)} active account(s) with password hashes"
            )
            
            self.users_table.setRowCount(len(self.users_list))
            self.radio_group = QButtonGroup(self)
            
            for i, u in enumerate(self.users_list):
                radio = QRadioButton()
                radio.setCursor(Qt.CursorShape.PointingHandCursor)
                radio.clicked.connect(lambda checked, uname=u['username']: self._on_user_selected(uname))
                self.radio_group.addButton(radio)
                
                radio_container = QWidget()
                radio_layout = QHBoxLayout(radio_container)
                radio_layout.addWidget(radio)
                radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                radio_layout.setContentsMargins(0, 0, 0, 0)
                self.users_table.setCellWidget(i, 0, radio_container)
                
                full_name_item = QTableWidgetItem(u['full_name'] if u['full_name'] else "-")
                username_item = QTableWidgetItem(u['username'])
                role_item = QTableWidgetItem(u['role'])
                uid_item = QTableWidgetItem(u['uid'])
                hash_item = QTableWidgetItem(u['hash_type'])
                
                uid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                scale = layout_manager.font_scale()
                role_font = QFont("JetBrains Mono", max(10, int(11 * scale)), QFont.Weight.Bold)
                
                if u['role'] == "Root":
                    role_item.setForeground(QColor(self.theme.current['error']))
                    role_item.setFont(role_font)
                elif u['role'] == "Administrator":
                    role_item.setForeground(QColor(self.theme.current['warning']))
                    role_item.setFont(role_font)
                elif u['role'] == "System":
                    role_item.setForeground(QColor(self.theme.current['text_secondary']))
                
                self.users_table.setItem(i, 1, full_name_item)
                self.users_table.setItem(i, 2, username_item)
                self.users_table.setItem(i, 3, role_item)
                self.users_table.setItem(i, 4, uid_item)
                self.users_table.setItem(i, 5, hash_item)
            
            self.users_table.cellClicked.connect(self._on_row_clicked)
            
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load users: {e}")
            return False
    
    def _on_user_selected(self, username):
        self.selected_user = username
    
    def _on_row_clicked(self, row, col):
        if 0 <= row < len(self.users_list):
            if self.radio_group and row < len(self.radio_group.buttons()):
                self.radio_group.buttons()[row].setChecked(True)
                self.selected_user = self.users_list[row]['username']
            
            self.users_table.selectRow(row)
    
    def _in(self):
        if QMessageBox.question(
            self, "Install", "Install john?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self.ib.setEnabled(False)
        self.ib.setText("Installing...")
        self.installer = LiveSystemToolsInstaller()
        self.installer.output.connect(lambda m: self.rs.setText(m))
        self.installer.finished.connect(self._id)
        self.installer.start()
    
    def _id(self, ok, msg):
        if ok:
            self.john_ok = self._chk("john")
            self._ut()
            self._uq()
        if not ok:
            self.ib.setEnabled(True)
            self.ib.setText("Retry")
    
    def set_wordlist_config(self, wp, sp):
        self.wordlist_path = wp
        self.split_parts = sp
        self._ub()
    
    def _go(self):
        if sys.platform != "linux":
            QMessageBox.warning(
                self, "Linux Only",
                "Live system cracking requires Linux (needs unshadow + the system's crypt library). "
                "It will not work on Windows or macOS."
            )
            return
        if not self.rule_slot.is_filled():
            QMessageBox.warning(self, "No Rules", "Please drag a rule first.")
            return
        if not hasattr(self, 'selected_user') or self.selected_user is None:
            QMessageBox.warning(self, "No User Selected", "Please select a user from the table.")
            return
        if not self.wordlist_path:
            QMessageBox.warning(self, "No Wordlist", "Please configure a wordlist from Configurations menu.")
            return
        if not os.path.exists(self.wordlist_path):
            QMessageBox.warning(self, "Wordlist Not Found", f"Wordlist file not found:\n{self.wordlist_path}")
            return
        
        self.tabs.setCurrentIndex(1)
        self.so.clear()
        self.ro.clear()
        self.pb.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        rules = self.rule_slot.rule_name if self.rule_slot.is_filled() else "Standard rules (recommended)"
        self.worker = LiveSystemWorker(self.wordlist_path, self.split_parts, rules, self.selected_user)
        self.worker.progress.connect(lambda m: self.so.append(m))
        self.worker.progress_value.connect(self.pb.setValue)
        self.worker.finished.connect(self._dn)
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
            self.ro.setText("No match found in wordlist" if msg == "No match found" else msg)
            self.tabs.setCurrentIndex(2)
        else:
            self.ro.setText(f"Error: {msg}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._theme()