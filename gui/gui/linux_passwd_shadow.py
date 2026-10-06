# gui/linux_passwd_shadow.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QTextBrowser, QFrame,
    QApplication, QScrollArea, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import os, subprocess, shutil, threading, time, tempfile, platform, sys
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
            while p and not isinstance(p, LinuxPasswdShadowPage):
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
        while p and not isinstance(p, LinuxPasswdShadowPage):
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


class LinuxToolsInstaller(QThread):
    output = Signal(str)
    finished = Signal(bool, str)
    
    def run(self):
        try:
            self.output.emit("Installing john...")
            subprocess.run(["sudo", "apt", "update", "-qq"], capture_output=True, text=True, timeout=30)
            subprocess.run(["sudo", "apt", "install", "-y", "john"], capture_output=True, text=True, timeout=120)
            self.finished.emit(True, "Ready")
        except Exception as e:
            self.finished.emit(False, str(e))


class LinuxShadowWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    users_found = Signal(list)
    
    def __init__(self, passwd_path, shadow_path, wordlist_path, split_parts, rules, target_user=None):
        super().__init__()
        self.passwd_path = passwd_path
        self.shadow_path = shadow_path
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.rules = rules
        self.target_user = target_user
        self.stop_flag = threading.Event()
        self.temp_dir = None
        self.hash_file = None
    
    def _find_john(self):
        if sys.platform == "win32":
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
                jtr_path = os.path.join(bundle_dir, "JtR", "run", "john.exe")
                if os.path.exists(jtr_path):
                    return jtr_path
            else:
                local_jtr = os.path.join(os.path.dirname(__file__), '..', 'JtR', 'run', 'john.exe')
                if os.path.exists(local_jtr):
                    return local_jtr
        
        for p in ["john", "/usr/sbin/john", "/usr/bin/john"]:
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                if subprocess.run([p], capture_output=True, timeout=3, creationflags=creationflags).returncode in [0, 1]:
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
    
    def _create_hash_file(self):
        """Runs unshadow to merge passwd + shadow, optionally filters to target user."""
        unshadow_bin = self._find_unshadow()
        if not unshadow_bin:
            self.progress.emit("unshadow not found - install the 'john' package (it bundles unshadow)")
            return 0

        try:
            result = subprocess.run(
                [unshadow_bin, self.passwd_path, self.shadow_path],
                capture_output=True, text=True, timeout=30
            )
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
        split_dir = os.path.join(home, ".sokonalysis", "shadow_parts")
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
                self.finished.emit(False, "passwd/shadow cracking requires Linux (needs unshadow + the system's crypt library)")
                return

            jp = self._find_john()
            home = os.path.expanduser("~")
            
            users = self._parse_users()
            for u in users:
                u['hash_type'] = self._detect_hash_type(u['hash'])
            self.users_found.emit(users)
            
            if not users:
                self.finished.emit(False, "No users with crackable password hashes found")
                return
            
            self.temp_dir = tempfile.mkdtemp(prefix="sokonalysis_shadow_")
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
            
            work_dir = os.path.join(home, ".sokonalysis", "shadow_work")
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
            running_procs = []
            procs_lock = threading.Lock()
            finished_emitted = threading.Event()
            timestamp = int(time.time() * 1000)
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

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

            def read_password_from_pot(pot_files):
                """
                Read the cracked password from pot files. Source of truth.
                
                unshadow output format: user:hash:last_change:min:max:warn:inactive:expire:reserved
                john pot format:        hash:password
                
                The hash itself may contain colons (e.g. $6$rounds=5000$salt$...),
                so the password is the LAST segment after the final colon.
                """
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
                                pwd = line.rsplit(':', 1)[-1]
                                if not pwd:
                                    continue
                                if pwd.startswith('$'):
                                    continue
                                return pwd
                    except:
                        continue
                return None

            def read_users_from_pot(pot_files):
                """Read user:password pairs from john pot file. Returns dict."""
                users = {}
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
                                pwd = line.rsplit(':', 1)[-1]
                                if not pwd or pwd.startswith('$'):
                                    continue
                                # The hash (before the last colon) maps to a user
                                hash_part = line.rsplit(':', 1)[0]
                                # We need to look up the user from the unshadow file
                                users[hash_part] = pwd
                    except:
                        continue
                return users

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
                
                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, creationflags=creationflags
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

                    if not finished_emitted.is_set() and saw_crack_hint:
                        pwd = read_password_from_pot([pot])
                        if pwd:
                            with pwd_lock:
                                if not password:
                                    password = pwd
                                    # Determine which user cracked by checking --show
                                    try:
                                        show_cmd = [jp, os.path.abspath(self.hash_file),
                                                    "--show", f"--pot={pot}"] + format_args
                                        show = subprocess.run(show_cmd, capture_output=True,
                                                              text=True, timeout=10,
                                                              creationflags=creationflags)
                                        if show.stdout.strip():
                                            for line in show.stdout.strip().split('\n'):
                                                if ':' in line and not line.startswith('0 password'):
                                                    parts_line = line.split(':')
                                                    if len(parts_line) >= 2:
                                                        candidate = parts_line[1]
                                                        if (candidate and not candidate.startswith('$')
                                                                and len(candidate) < 128):
                                                            cracked_user = parts_line[0]
                                                            break
                                    except:
                                        pass
                                    if not cracked_user:
                                        cracked_user = "Unknown"
                                    self.stop_flag.set()
                            kill_all_procs()
                            self.progress.emit("Password found!")
                            result = f"User: {cracked_user}\nPassword: {password}"
                            emit_finished_once(True, result)
                            return

                    if not finished_emitted.is_set():
                        self.progress.emit(f"Part {idx+1}/{len(parts)} done")
                        self.progress_value.emit(30 + int(((idx+1)/len(parts))*65))

            threads = []
            for idx, pf in enumerate(parts):
                t = threading.Thread(target=crack_part, args=(pf, idx), daemon=True)
                threads.append(t)
                t.start()
                time.sleep(0.3)

            while not finished_emitted.is_set() and any(t.is_alive() for t in threads):
                time.sleep(0.2)

            if password and not finished_emitted.is_set():
                kill_all_procs()
                result = f"User: {cracked_user or 'Unknown'}\nPassword: {password}"
                emit_finished_once(True, result)
            elif not finished_emitted.is_set():
                # Final fallback: --show across all pots
                all_pots = [os.path.join(work_dir, f"pot_{i+1}_{timestamp}") for i in range(len(parts))]
                parsed_results = []
                for pot in all_pots:
                    if not os.path.exists(pot):
                        continue
                    try:
                        show_cmd = [jp, os.path.abspath(self.hash_file),
                                    "--show", f"--pot={pot}"] + format_args
                        show = subprocess.run(show_cmd, capture_output=True,
                                              text=True, timeout=10,
                                              creationflags=creationflags)
                        if show.stdout.strip():
                            for line in show.stdout.strip().split('\n'):
                                if ':' in line and not line.startswith('0 password'):
                                    parts_line = line.split(':')
                                    if len(parts_line) >= 2:
                                        username = parts_line[0]
                                        candidate = parts_line[1]
                                        if (candidate and not candidate.startswith('$')
                                                and len(candidate) < 128):
                                            parsed_results.append(
                                                f"User: {username}\nPassword: {candidate}"
                                            )
                    except:
                        continue
                
                if parsed_results:
                    # Deduplicate
                    seen = set()
                    unique = []
                    for r in parsed_results:
                        if r not in seen:
                            seen.add(r)
                            unique.append(r)
                    emit_finished_once(True, '\n\n'.join(unique))
                else:
                    emit_finished_once(True, "No match found")

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


class LinuxPasswdShadowPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.passwd_path = ""
        self.shadow_path = ""
        self.worker = None
        self.installer = None
        self.rule_cards = []
        self.john_ok = self._chk("john")
        self._ui()
        self.setAcceptDrops(True)
    
    def _chk(self, cmd):
        if sys.platform == "win32":
            if getattr(sys, 'frozen', False):
                bundle_dir = sys._MEIPASS
                jtr_path = os.path.join(bundle_dir, "JtR", "run", "john.exe")
                if os.path.exists(jtr_path):
                    try:
                        return subprocess.run(
                            [jtr_path], capture_output=True, timeout=3,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        ).returncode in [0, 1]
                    except:
                        pass
            else:
                local_jtr = os.path.join(os.path.dirname(__file__), '..', 'JtR', 'run', 'john.exe')
                if os.path.exists(local_jtr):
                    try:
                        return subprocess.run(
                            [local_jtr], capture_output=True, timeout=3,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        ).returncode in [0, 1]
                    except:
                        pass
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
            if fp:
                fn = os.path.basename(fp).lower()
                if 'passwd' in fn or 'password' in fn:
                    self.passwd_path = fp
                    self.passwd_input.setText(fp)
                    self._update_passwd_preview(fp)
                elif 'shadow' in fn:
                    self.shadow_path = fp
                    self.shadow_input.setText(fp)
                    self._update_shadow_preview(fp)
                if self.passwd_path and self.shadow_path:
                    self._load_users()
                self.start_btn.setEnabled(
                    bool(self.wordlist_path) and bool(self.passwd_path)
                    and bool(self.shadow_path) and self.john_ok
                )
                break
    
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
        t = QLabel("passwd & shadow Cracking")
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
        for attr in ['rule_grp', 'files_grp', 'res_grp', 'req_group']:
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
        if hasattr(self, 'passwd_input') and self.passwd_input is not None:
            self.passwd_input.setStyleSheet(input_style)
        if hasattr(self, 'shadow_input') and self.shadow_input is not None:
            self.shadow_input.setStyleSheet(input_style)
        
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
        if hasattr(self, 'user_combo') and self.user_combo is not None:
            self.user_combo.setStyleSheet(
                f"QComboBox{{background:{t['crust']};color:{t['text_secondary']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:8px 12px;"
                f"font-size:{max(12, int(13 * scale))}px;min-width:200px;}} "
                f"QComboBox QAbstractItemView{{background:{t['base']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:4px;"
                f"selection-background-color:{t['hover']};"
                f"selection-color:{t['text']};outline:none;}} "
                f"QComboBox QAbstractItemView::item{{padding:6px 12px;border-radius:4px;}} "
                f"QComboBox QAbstractItemView::item:hover{{background:{t['hover']};}} "
                f"QComboBox QAbstractItemView::item:selected{{background:{t['hover']};color:{t['text']};}}"
            )
        if hasattr(self, 'pb') and self.pb is not None:
            self.pb.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        if hasattr(self, 'passwd_preview') and self.passwd_preview is not None:
            self.passwd_preview.setStyleSheet(
                f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
                f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
            )
        if hasattr(self, 'shadow_preview') and self.shadow_preview is not None:
            self.shadow_preview.setStyleSheet(
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
        self.files_grp.setVisible(True)
        self.user_combo.setVisible(True)
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(True)
    
    def _on_rule_cleared(self):
        self.files_grp.setVisible(False)
        self.user_combo.setVisible(False)
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(False)
    
    def _update_passwd_preview(self, filepath):
        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1048576:.1f} MB"
            self.passwd_preview.setText(f"passwd: {os.path.basename(filepath)}\n{size_str}")
        else:
            self.passwd_preview.setText("Drag & drop passwd file here\nor click Browse to select")
    
    def _update_shadow_preview(self, filepath):
        if filepath and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1048576:.1f} MB"
            self.shadow_preview.setText(f"shadow: {os.path.basename(filepath)}\n{size_str}")
        else:
            self.shadow_preview.setText("Drag & drop shadow file here\nor click Browse to select")
    
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
        
        self.files_grp = QGroupBox("2. Files")
        self.files_grp.setVisible(False)
        fl = QVBoxLayout()
        fl.setSpacing(10)
        
        self.passwd_preview = QLabel("Drag & drop passwd file here\nor click Browse to select")
        self.passwd_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.passwd_preview.setFixedHeight(60)
        fl.addWidget(self.passwd_preview)
        pr = QHBoxLayout()
        self.passwd_input = QLineEdit()
        self.passwd_input.setReadOnly(True)
        self.passwd_input.setPlaceholderText("No passwd file selected...")
        pb = QPushButton("Browse")
        pb.setObjectName("actionButton")
        pb.setCursor(Qt.CursorShape.PointingHandCursor)
        pb.clicked.connect(lambda: self._br("passwd"))
        pr.addWidget(self.passwd_input)
        pr.addWidget(pb)
        fl.addLayout(pr)
        
        self.shadow_preview = QLabel("Drag & drop shadow file here\nor click Browse to select")
        self.shadow_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shadow_preview.setFixedHeight(60)
        fl.addWidget(self.shadow_preview)
        sr = QHBoxLayout()
        self.shadow_input = QLineEdit()
        self.shadow_input.setReadOnly(True)
        self.shadow_input.setPlaceholderText("No shadow file selected...")
        sb = QPushButton("Browse")
        sb.setObjectName("actionButton")
        sb.setCursor(Qt.CursorShape.PointingHandCursor)
        sb.clicked.connect(lambda: self._br("shadow"))
        sr.addWidget(self.shadow_input)
        sr.addWidget(sb)
        fl.addLayout(sr)
        
        self.files_grp.setLayout(fl)
        l.addWidget(self.files_grp)
        
        self.user_combo = QComboBox()
        self.user_combo.addItem("ALL USERS")
        self.user_combo.setVisible(False)
        l.addWidget(self.user_combo)
        
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
    
    def _load_users(self):
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
            
            users = []
            for line in passwd_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        if username in shadow_dict:
                            h = shadow_dict[username]
                            if h and h not in ['*', '!', '!!', '!*', 'x', '']:
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
                                users.append({
                                    'username': username,
                                    'uid': parts[2],
                                    'hash': h,
                                    'hash_type': ht
                                })
            
            self.user_combo.clear()
            self.user_combo.addItem("ALL USERS")
            for u in users:
                self.user_combo.addItem(f"{u['username']} (UID: {u['uid']})")
            return True
        except Exception:
            return False
    
    def _br(self, ft):
        if ft == "passwd":
            fp, _ = QFileDialog.getOpenFileName(self, "Select passwd File", "", "All Files (*)")
            if fp:
                self.passwd_path = fp
                self.passwd_input.setText(fp)
                self._update_passwd_preview(fp)
        else:
            fp, _ = QFileDialog.getOpenFileName(self, "Select shadow File", "", "All Files (*)")
            if fp:
                self.shadow_path = fp
                self.shadow_input.setText(fp)
                self._update_shadow_preview(fp)
        if self.passwd_path and self.shadow_path:
            self._load_users()
        self.start_btn.setEnabled(
            bool(self.wordlist_path) and bool(self.passwd_path)
            and bool(self.shadow_path) and self.john_ok
        )
    
    def _in(self):
        if QMessageBox.question(
            self, "Install", "Install john?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        self.ib.setEnabled(False)
        self.ib.setText("Installing...")
        self.installer = LinuxToolsInstaller()
        self.installer.output.connect(lambda m: self.rs.setText(m))
        self.installer.finished.connect(self._id)
        self.installer.start()
    
    def _id(self, ok, msg):
        if ok:
            self.john_ok = self._chk("john")
            self._ut()
            self._uq()
        self.start_btn.setEnabled(
            bool(self.wordlist_path) and bool(self.passwd_path)
            and bool(self.shadow_path) and self.john_ok
        )
        if not ok:
            self.ib.setEnabled(True)
            self.ib.setText("Retry")
    
    def set_wordlist_config(self, wp, sp):
        self.wordlist_path = wp
        self.split_parts = sp
        self._ub()
        self.start_btn.setEnabled(
            bool(self.passwd_path) and bool(self.shadow_path) and self.john_ok
        )
    
    def _go(self):
        if sys.platform != "linux":
            QMessageBox.warning(
                self, "Linux Only",
                "passwd/shadow cracking requires Linux (needs unshadow + the system's crypt library). "
                "It will not work on Windows or macOS."
            )
            return
        if not self.rule_slot.is_filled():
            QMessageBox.warning(self, "No Rules", "Please drag a rule first.")
            return
        if not self.passwd_path or not self.shadow_path:
            QMessageBox.warning(self, "No Files", "Please select both passwd and shadow files.")
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
        
        target_user = None
        if self.user_combo.currentIndex() > 0:
            target_text = self.user_combo.currentText()
            target_user = target_text.split(" (UID:")[0]
        
        rules = self.rule_slot.rule_name if self.rule_slot.is_filled() else "Standard rules (recommended)"
        self.worker = LinuxShadowWorker(
            self.passwd_path, self.shadow_path,
            self.wordlist_path, self.split_parts, rules, target_user
        )
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