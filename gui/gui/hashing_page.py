# gui/hashing_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QFormLayout, QCheckBox, QSpinBox, QProgressBar,
    QScrollArea, QTextBrowser, QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QMimeData
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDrag, QPainter
import os, subprocess, tempfile, shutil, threading, time, re, platform, sys
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
        # Wide enough for "Standard rules (recommended)" at any readable scale
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
        # Wide enough for the placeholder and for "Standard rules (recommended)"
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
            while p and not isinstance(p, HashingPage):
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
        while p and not isinstance(p, HashingPage):
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


class JohnManager:
    """Cross-platform John the Ripper detection"""
    
    def __init__(self):
        self.system = platform.system()
        self.john_path = None
        self.john_dir = None
    
    def find_john(self):
        if self.system == "Windows":
            return self._find_john_windows()
        else:
            return self._find_john_unix()
    
    def _verify_john(self, john_path):
        try:
            kwargs = {'capture_output': True, 'text': True, 'timeout': 5}
            if self.system == "Windows":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([john_path], **kwargs)
            if result.returncode in [0, 1]:
                output = (result.stderr + result.stdout).lower()
                return 'john' in output or 'password' in output
        except:
            pass
        return False
    
    def _find_john_windows(self):
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            jtr_path = os.path.join(bundle_dir, "JtR", "run", "john.exe")
            if os.path.exists(jtr_path) and self._verify_john(jtr_path):
                self.john_path = jtr_path
                self.john_dir = os.path.dirname(jtr_path)
                return True
        else:
            local_jtr = os.path.join(os.path.dirname(__file__), '..', 'JtR', 'run', 'john.exe')
            if os.path.exists(local_jtr) and self._verify_john(local_jtr):
                self.john_path = local_jtr
                self.john_dir = os.path.dirname(local_jtr)
                return True
        john_in_path = shutil.which('john.exe')
        if john_in_path and self._verify_john(john_in_path):
            self.john_path = john_in_path
            self.john_dir = os.path.dirname(john_in_path)
            return True
        search_dirs = [
            "C:\\john\\run", "C:\\john-1.9.0-jumbo-1\\run",
            "C:\\JtR\\run", "C:\\Program Files\\john\\run"
        ]
        for directory in search_dirs:
            john_exe = os.path.join(directory, "john.exe")
            if os.path.exists(john_exe) and self._verify_john(john_exe):
                self.john_path = john_exe
                self.john_dir = directory
                return True
        return False
    
    def _find_john_unix(self):
        common_paths = [
            "/usr/bin/john", "/usr/sbin/john", "/usr/local/bin/john",
            "/snap/bin/john", "/opt/john/run/john"
        ]
        for path in common_paths:
            if os.path.exists(path) and self._verify_john(path):
                self.john_path = path
                self.john_dir = os.path.dirname(path)
                return True
        which_john = shutil.which('john')
        if which_john and self._verify_john(which_john):
            self.john_path = which_john
            self.john_dir = os.path.dirname(which_john)
            return True
        return False
    
    def get_version(self):
        if not self.john_path:
            if not self.find_john():
                return "Not installed"
        try:
            kwargs = {'capture_output': True, 'text': True, 'timeout': 5}
            if self.system == "Windows":
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            result = subprocess.run([self.john_path], **kwargs)
            output = result.stderr if result.stderr else result.stdout
            for line in output.split('\n'):
                if 'John the Ripper' in line:
                    return line.strip()
            return "installed"
        except:
            return "unknown"


class HashReverseWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, hash_value, wordlist_path, rules, split_parts, john_path):
        super().__init__()
        self.hash_value = hash_value.strip()
        self.wordlist_path = wordlist_path
        self.rules = rules
        self.split_parts = split_parts
        self.john_path = john_path
        self.stop_flag = threading.Event()
        self.cracked_password = None
        self.lock = threading.Lock()
    
    def _count_words(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def _detect_format_info(self, hash_value):
        if ':' in hash_value:
            parts = hash_value.split(':')
            clean_hash = parts[-1] if len(parts) > 1 else hash_value
        else:
            clean_hash = hash_value
        clean_hash = clean_hash.strip()
        hlen = len(clean_hash)
        is_hex = bool(re.match(r'^[0-9a-fA-F]+$', clean_hash))
        
        if clean_hash.startswith('$2a$') or clean_hash.startswith('$2b$') or clean_hash.startswith('$2y$'):
            return "--format=bcrypt", "bcrypt (Blowfish)"
        if clean_hash.startswith('$6$'):
            return "--format=sha512crypt", "SHA-512 crypt"
        if clean_hash.startswith('$5$'):
            return "--format=sha256crypt", "SHA-256 crypt"
        if clean_hash.startswith('$1$'):
            return "--format=md5crypt", "MD5 crypt"
        if clean_hash.startswith('$y$'):
            return "--format=yescrypt", "yescrypt"
        if clean_hash.startswith('$7$'):
            return "--format=scrypt", "scrypt"
        if clean_hash.startswith('$argon2'):
            return "--format=argon2", "Argon2"
        if clean_hash.startswith('$md5$') or clean_hash.startswith('$md5,'):
            return "--format=md5crypt", "MD5 crypt (Sun)"
        if clean_hash.startswith('$sha1$'):
            return "--format=sha1crypt", "SHA1 crypt"
        if clean_hash.startswith('$DCC2$'):
            return "--format=mscash2", "MS Cache v2"
        if clean_hash.startswith('$netntlmv2$'):
            return "--format=netntlmv2", "NetNTLMv2"
        if clean_hash.startswith('$netntlm$'):
            return "--format=netntlm", "NetNTLM"
        if clean_hash.startswith('$mschapv2$'):
            return "--format=MSCHAPv2", "MS-CHAPv2"
        if clean_hash.startswith('$DPAPImk$'):
            return "--format=DPAPImk", "DPAPI Master Key"
        if clean_hash.startswith('$mysql$'):
            return "--format=mysql", "MySQL"
        if clean_hash.startswith('$mysqlna$'):
            return "--format=mysqlna", "MySQL NA"
        if clean_hash.startswith('$mssql12$'):
            return "--format=mssql12", "MSSQL 2012"
        if clean_hash.startswith('$mssql05$'):
            return "--format=mssql05", "MSSQL 2005"
        if clean_hash.startswith('$mssql$'):
            return "--format=mssql", "MSSQL"
        if clean_hash.startswith('$oracle12c$'):
            return "--format=Oracle12C", "Oracle 12C"
        if clean_hash.startswith('$oracle11$'):
            return "--format=oracle11", "Oracle 11"
        if clean_hash.startswith('$oracle$'):
            return "--format=oracle", "Oracle"
        if clean_hash.startswith('$postgres$'):
            return "--format=postgres", "PostgreSQL"
        if clean_hash.startswith('$mongodb$'):
            return "--format=MongoDB", "MongoDB"
        if clean_hash.startswith('$sybase$'):
            return "--format=SybaseASE", "Sybase ASE"
        if clean_hash.startswith('$scram$'):
            return "--format=scram", "SCRAM"
        if clean_hash.startswith('$P$') or clean_hash.startswith('$H$'):
            return "--format=phpass", "PHPass"
        if clean_hash.startswith('$PHPS$'):
            return "--format=PHPS", "PHPS"
        if clean_hash.startswith('$Drupal7$'):
            return "--format=Drupal7", "Drupal 7"
        if clean_hash.startswith('$S$') or clean_hash.startswith('$C$') or clean_hash.startswith('$D$'):
            return "--format=Drupal7", "Drupal"
        if clean_hash.startswith('$J$'):
            return "--format=phpass", "Joomla"
        if clean_hash.startswith('$W$'):
            return "--format=phpass", "WordPress"
        if clean_hash.startswith('$pbkdf2-sha512$'):
            return "--format=PBKDF2-HMAC-SHA512", "PBKDF2-SHA512"
        if clean_hash.startswith('$pbkdf2-sha256$'):
            return "--format=PBKDF2-HMAC-SHA256", "PBKDF2-SHA256"
        if clean_hash.startswith('$django-scrypt$'):
            return "--format=django-scrypt", "Django Scrypt"
        if clean_hash.startswith('$django$'):
            return "--format=django", "Django"
        if clean_hash.startswith('$MediaWiki$'):
            return "--format=MediaWiki", "MediaWiki"
        if clean_hash.startswith('$bitwarden$'):
            return "--format=Bitwarden", "Bitwarden"
        if clean_hash.startswith('$krb5asrep$'):
            return "--format=krb5asrep", "Kerberos AS-REP"
        if clean_hash.startswith('$krb5tgs$'):
            return "--format=krb5tgs", "Kerberos TGS"
        if clean_hash.startswith('$krb5pa$'):
            return "--format=krb5pa-sha1", "Kerberos PA"
        if clean_hash.startswith('$krb5$'):
            return "--format=krb5", "Kerberos 5"
        if clean_hash.startswith('$chap$'):
            return "--format=chap", "CHAP"
        if clean_hash.startswith('$tacacs$'):
            return "--format=tacacs-plus", "TACACS+"
        if clean_hash.startswith('$radius$'):
            return "--format=radius", "RADIUS"
        if clean_hash.startswith('$ssh$'):
            return "--format=SSH", "SSH Private Key"
        if clean_hash.startswith('$ike$'):
            return "--format=IKE", "IKE"
        if clean_hash.startswith('$sip$'):
            return "--format=SIP", "SIP"
        if clean_hash.startswith('$SNMP$'):
            return "--format=SNMP", "SNMP"
        if clean_hash.startswith('$xmpp$'):
            return "--format=xmpp-scram", "XMPP SCRAM"
        if clean_hash.startswith('$zip2$'):
            return "--format=ZIP", "ZIP (AES)"
        if clean_hash.startswith('$zip$'):
            return "--format=ZIP", "ZIP"
        if clean_hash.startswith('$rar5$'):
            return "--format=rar", "RAR5"
        if clean_hash.startswith('$rar$'):
            return "--format=rar", "RAR"
        if clean_hash.startswith('$7z$'):
            return "--format=7z", "7-Zip"
        if clean_hash.startswith('$pkzip$'):
            return "--format=PKZIP", "PKZIP"
        if clean_hash.startswith('$bitlocker$'):
            return "--format=BitLocker", "BitLocker"
        if clean_hash.startswith('$luks$'):
            return "--format=LUKS", "LUKS"
        if clean_hash.startswith('$truecrypt$') or clean_hash.startswith('$veracrypt$'):
            return "--format=tc_sha512", "TrueCrypt/VeraCrypt"
        if clean_hash.startswith('$fvde$'):
            return "--format=FVDE", "FileVault"
        if clean_hash.startswith('$office$'):
            return "--format=Office", "MS Office"
        if clean_hash.startswith('$oldoffice$'):
            return "--format=oldoffice", "Old Office"
        if clean_hash.startswith('$pdf$'):
            return "--format=PDF", "PDF"
        if clean_hash.startswith('$odf$'):
            return "--format=ODF", "OpenDocument"
        if clean_hash.startswith('$keepass$'):
            return "--format=KeePass", "KeePass"
        if clean_hash.startswith('$itunes$'):
            return "--format=itunes-backup", "iTunes Backup"
        if clean_hash.startswith('$pst$'):
            return "--format=PST", "Outlook PST"
        if clean_hash.startswith('$asa$'):
            return "--format=asa-md5", "Cisco ASA"
        if clean_hash.startswith('$pix$'):
            return "--format=pix-md5", "Cisco PIX"
        if clean_hash.startswith('$ios$') or clean_hash.startswith('$cisco$'):
            return "--format=md5crypt", "Cisco IOS"
        if clean_hash.startswith('$fortinet$'):
            return "--format=Fortigate256", "FortiGate 256"
        if clean_hash.startswith('$fortigate$'):
            return "--format=Fortigate", "FortiGate"
        if clean_hash.startswith('$juniper$'):
            return "--format=md5crypt", "Juniper"
        if clean_hash.startswith('$solarwinds$'):
            return "--format=solarwinds", "SolarWinds"
        if clean_hash.startswith('$citrix$'):
            return "--format=Citrix_NS10", "Citrix"
        if clean_hash.startswith('$bitcoin$'):
            return "--format=Bitcoin", "Bitcoin"
        if clean_hash.startswith('$ethereum$'):
            return "--format=ethereum", "Ethereum"
        if clean_hash.startswith('$monero$'):
            return "--format=monero", "Monero"
        if clean_hash.startswith('$electrum$'):
            return "--format=electrum", "Electrum"
        if clean_hash.startswith('$gpg$') or clean_hash.startswith('$pgp$'):
            return "--format=gpg", "GPG/PGP"
        if clean_hash.startswith('$keychain$'):
            return "--format=keychain", "Keychain"
        if clean_hash.startswith('$keyring$'):
            return "--format=keyring", "Keyring"
        if clean_hash.startswith('$keystore$'):
            return "--format=keystore", "Keystore"
        if clean_hash.startswith('$kwallet$'):
            return "--format=kwallet", "KWallet"
        if clean_hash.startswith('$lastpass$'):
            return "--format=LastPass", "LastPass"
        if clean_hash.startswith('$lp$'):
            return "--format=lpcli", "LastPass CLI"
        if clean_hash.startswith('$putty$'):
            return "--format=PuTTY", "PuTTY"
        if clean_hash.startswith('$pwsafe$'):
            return "--format=pwsafe", "Password Safe"
        if clean_hash.startswith('$android$'):
            return "--format=AndroidBackup", "Android Backup"
        if clean_hash.startswith('$azure$'):
            return "--format=AzureAD", "Azure AD"
        if clean_hash.startswith('$encfs$'):
            return "--format=EncFS", "EncFS"
        if clean_hash.startswith('$dmg$'):
            return "--format=dmg", "DMG"
        if clean_hash.startswith('$vmx$'):
            return "--format=vmx", "VMware VMX"
        if clean_hash.startswith('$vnc$'):
            return "--format=VNC", "VNC"
        if clean_hash.startswith('$openssl$'):
            return "--format=openssl-enc", "OpenSSL"
        if hlen == 16 and is_hex and clean_hash == clean_hash.upper():
            return "--format=LM", "LM hash"
        if hlen == 32 and is_hex:
            return "--format=Raw-MD5", "MD5"
        if hlen == 40 and is_hex:
            return "--format=Raw-SHA1", "SHA1"
        if hlen == 56 and is_hex:
            return "--format=Raw-SHA224", "SHA224"
        if hlen == 64 and is_hex:
            return "--format=Raw-SHA256", "SHA256"
        if hlen == 96 and is_hex:
            return "--format=Raw-SHA384", "SHA384"
        if hlen == 128 and is_hex:
            return "--format=Raw-SHA512", "SHA512"
        if ':' in hash_value and len(hash_value.split(':')) >= 4:
            return "--format=wpapsk", "WPA PSK"
        return "", "auto-detect"
    
    def _get_rules_flag(self):
        rules_map = {
            "No rules (fastest)": [],
            "Standard rules (recommended)": ["--rules"],
            "All rules (thorough)": ["--rules=All"]
        }
        return rules_map.get(self.rules, ["--rules"])
    
    def _run_john_part(self, part_file, part_num, hash_file, format_flag, rules_flag, temp_dir):
        pot_file = os.path.join(temp_dir, f"john_part{part_num}.pot")
        session_file = os.path.join(temp_dir, f"session_{part_num}")
        cmd = [
            self.john_path, hash_file,
            f"--wordlist={part_file}",
            f"--pot={pot_file}",
            f"--session={session_file}"
        ]
        if format_flag:
            cmd.append(format_flag)
        cmd.extend(rules_flag)
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=7200, cwd=temp_dir)
            if os.path.exists(pot_file):
                with open(pot_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            password = line.split(':')[-1]
                            if password and len(password) > 0:
                                with self.lock:
                                    if not self.stop_flag.is_set():
                                        self.cracked_password = password
                                        self.stop_flag.set()
                                return True
        except:
            pass
        return False
    
    def run(self):
        temp_dir = None
        try:
            self.progress.emit("Checking requirements...")
            self.progress_value.emit(3)
            try:
                subprocess.run([self.john_path], capture_output=True, timeout=3)
            except FileNotFoundError:
                self.finished.emit(False, "John the Ripper not found")
                return
            if not os.path.exists(self.wordlist_path):
                self.finished.emit(False, "Wordlist file not found")
                return
            word_count = self._count_words(self.wordlist_path)
            if word_count == 0:
                self.finished.emit(False, "Wordlist is empty")
                return
            self.progress.emit(f"Wordlist: {word_count:,} words")
            self.progress_value.emit(10)
            
            temp_dir = tempfile.mkdtemp(prefix="sokonalysis_")
            hash_file = os.path.join(temp_dir, "hash.txt")
            formatted = self.hash_value if ':' in self.hash_value else f"user:{self.hash_value}"
            with open(hash_file, 'w') as f:
                f.write(formatted + '\n')
            
            format_flag, display_name = self._detect_format_info(self.hash_value)
            rules_flag = self._get_rules_flag()
            self.progress.emit(f"Hash identified: {display_name}")
            self.progress_value.emit(15)
            
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
            
            self.progress.emit(f"Running {len(part_files)} parallel instances...")
            self.progress_value.emit(40)
            
            threads = []
            done = [0]
            
            def worker(pf, idx):
                if self.stop_flag.is_set():
                    return
                self._run_john_part(pf, idx + 1, hash_file, format_flag, rules_flag, temp_dir)
                with self.lock:
                    done[0] += 1
                    pct = 40 + int((done[0] / len(part_files)) * 55)
                    self.progress_value.emit(pct)
            
            for idx, pf in enumerate(part_files):
                t = threading.Thread(target=worker, args=(pf, idx))
                threads.append(t)
                t.start()
                time.sleep(0.1)
            
            for t in threads:
                while t.is_alive():
                    if self.stop_flag.is_set():
                        break
                    t.join(timeout=1)
            
            self.progress_value.emit(100)
            if self.cracked_password:
                self.finished.emit(True, self.cracked_password)
            else:
                self.finished.emit(True, "No match found")
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    
    def stop(self):
        self.stop_flag.set()


class HashingPage(QWidget):
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.worker = None
        self.rule_cards = []
        self.john_manager = JohnManager()
        self.john_available = self.john_manager.find_john()
        self.john_version = self.john_manager.get_version()
        self._init_ui()
    
    def _paste_to(self, widget):
        c = QApplication.clipboard().text()
        if c:
            widget.setText(c.strip())
    
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
        title = QLabel("Hash Reverse")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        john_container = QHBoxLayout()
        john_container.setSpacing(4)
        self.john_icon = QLabel()
        self.john_icon.setFixedSize(18, 18)
        self.john_icon.setStyleSheet("background:transparent;")
        self.john_badge = QLabel()
        self._update_john_badge()
        john_container.addWidget(self.john_icon)
        john_container.addWidget(self.john_badge)
        header.addLayout(john_container)
        
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
        self.tabs.addTab(self._tab_requirements(), "Requirements")
        self.tabs.addTab(self._tab_formats(), "Supported Formats")
        
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
    
    def _update_john_badge(self):
        t = self.theme.current
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.john_available:
            self.john_badge.setText("John Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "jonny.png")
        else:
            self.john_badge.setText("John Missing")
            c = t['error']
            icon_path = os.path.join(icons_dir, "no.png")
        self.john_badge.setStyleSheet(
            f"padding:4px 12px;border-radius:12px;font-size:11px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'john_icon'):
            self.john_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
    
    def _on_rule_dropped(self):
        self.in_grp.setVisible(True)
        self.reverse_btn.setVisible(True)
        self.stop_btn.setVisible(True)
    
    def _on_rule_cleared(self):
        self.in_grp.setVisible(False)
        self.reverse_btn.setVisible(False)
        self.stop_btn.setVisible(False)
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.rule_grp = QGroupBox("1. Cracking Rules (Drag & Drop)")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        t = self.theme.current
        for rid, rn in [(0, "No rules (fastest)"), (1, "Standard rules (recommended)"), (2, "All rules (thorough)")]:
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
        
        self.in_grp = QGroupBox("2. Hash Input")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        il.setSpacing(10)
        self.hash_input = QTextEdit()
        self.hash_input.setPlaceholderText("Paste your hash here...")
        self.hash_input.setMaximumHeight(100)
        self.hash_input.setMinimumHeight(80)
        il.addWidget(self.hash_input)
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.hash_input))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.hash_input.clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        il.addLayout(btn_row)
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setMinimumHeight(48)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_reversal)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setVisible(False)
        self.reverse_btn = QPushButton("Reverse")
        self.reverse_btn.setObjectName("actionButton")
        self.reverse_btn.setMinimumHeight(48)
        self.reverse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reverse_btn.clicked.connect(self._start_reversal)
        self.reverse_btn.setVisible(False)
        br.addWidget(self.stop_btn)
        br.addWidget(self.reverse_btn)
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _tab_status(self):
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(28)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        l.addWidget(self.progress_bar)
        l.addWidget(self.status_output)
        return widget
    
    def _tab_results(self):
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Cracked Password:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        l.addLayout(rh)
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Waiting for results...")
        l.addWidget(self.results_output, 1)
        return widget
    
    def _tab_requirements(self):
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.req_group = QGroupBox("System Requirements")
        rl = QVBoxLayout()
        self.req_output = QTextBrowser()
        self.req_output.setOpenExternalLinks(True)
        self.req_output.setMinimumHeight(120)
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Detection")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._refresh_john)
        self.install_btn = QPushButton("Install John the Ripper")
        self.install_btn.setObjectName("actionButton")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._install_john)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.install_btn)
        self.req_status = QLabel("")
        rl.addWidget(self.req_output)
        rl.addLayout(btn_layout)
        rl.addWidget(self.req_status)
        self.req_group.setLayout(rl)
        l.addWidget(self.req_group)
        l.addStretch()
        self._update_requirements_display()
        return widget
    
    def _tab_formats(self):
        widget = QWidget()
        l = QVBoxLayout(widget)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        self.formats_group = QGroupBox("All Supported Hash Formats")
        fl = QVBoxLayout()
        self.formats_output = QTextBrowser()
        self.formats_output.setOpenExternalLinks(False)
        self.formats_output.setHtml(self._get_formats_html())
        fl.addWidget(self.formats_output, 1)
        self.formats_group.setLayout(fl)
        l.addWidget(self.formats_group, 1)
        return widget
    
    def _get_formats_html(self):
        t = self.theme.current
        return f"""
        <h3 style="color: {t['accent']};">100+ Hash Formats Supported</h3>
        <table width="100%" cellpadding="4" cellspacing="0">
        <tr><td colspan="2"><b style="color: {t['text_secondary']};">Unix Crypt</b></td></tr>
        <tr><td>bcrypt (Blowfish)</td><td>sha512crypt</td></tr>
        <tr><td>sha256crypt</td><td>md5crypt</td></tr>
        <tr><td>yescrypt</td><td>scrypt</td></tr>
        <tr><td>Argon2</td><td>descrypt</td></tr>
        <tr><td>SHA1 crypt</td><td>SunMD5</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Windows / Active Directory</b></td></tr>
        <tr><td>NT hash</td><td>LM hash</td></tr>
        <tr><td>MS Cache v1/v2</td><td>NetNTLMv1/v2</td></tr>
        <tr><td>NetLM</td><td>MS-CHAPv2</td></tr>
        <tr><td>DPAPI Master Key</td><td>Kerberos (AS-REP/TGS/PA)</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Database</b></td></tr>
        <tr><td>MySQL</td><td>MySQL NA</td></tr>
        <tr><td>MSSQL (2005/2012)</td><td>Oracle (11/12C)</td></tr>
        <tr><td>PostgreSQL</td><td>MongoDB</td></tr>
        <tr><td>Sybase ASE</td><td>SCRAM</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Web Applications</b></td></tr>
        <tr><td>PHPass</td><td>Drupal 7</td></tr>
        <tr><td>Joomla</td><td>WordPress</td></tr>
        <tr><td>Django / Django Scrypt</td><td>PBKDF2-SHA256/SHA512</td></tr>
        <tr><td>MediaWiki</td><td>Bitwarden</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Network Protocols</b></td></tr>
        <tr><td>WPA PSK</td><td>SSH Private Key</td></tr>
        <tr><td>RADIUS</td><td>TACACS+</td></tr>
        <tr><td>CHAP</td><td>SIP</td></tr>
        <tr><td>IKE</td><td>SNMP</td></tr>
        <tr><td>XMPP SCRAM</td><td></td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Archives / Compression</b></td></tr>
        <tr><td>ZIP / ZIP (AES)</td><td>RAR / RAR5</td></tr>
        <tr><td>7-Zip</td><td>PKZIP</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Disk Encryption</b></td></tr>
        <tr><td>BitLocker</td><td>LUKS</td></tr>
        <tr><td>TrueCrypt / VeraCrypt</td><td>FileVault</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Documents</b></td></tr>
        <tr><td>MS Office</td><td>Old Office</td></tr>
        <tr><td>PDF</td><td>OpenDocument</td></tr>
        <tr><td>KeePass</td><td>iTunes Backup</td></tr>
        <tr><td>Outlook PST</td><td></td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">VPN / Network Devices</b></td></tr>
        <tr><td>Cisco ASA / PIX / IOS</td><td>FortiGate / FortiGate 256</td></tr>
        <tr><td>Juniper</td><td>SolarWinds</td></tr>
        <tr><td>Citrix</td><td></td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Blockchain / Crypto</b></td></tr>
        <tr><td>Bitcoin</td><td>Ethereum</td></tr>
        <tr><td>Monero</td><td>Electrum</td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Other Applications</b></td></tr>
        <tr><td>GPG/PGP</td><td>LastPass / LastPass CLI</td></tr>
        <tr><td>PuTTY</td><td>Password Safe</td></tr>
        <tr><td>Android Backup</td><td>Azure AD</td></tr>
        <tr><td>EncFS</td><td>DMG</td></tr>
        <tr><td>VMware VMX</td><td>VNC</td></tr>
        <tr><td>OpenSSL Encryption</td><td>Keychain / Keyring / Keystore</td></tr>
        <tr><td>KWallet</td><td></td></tr>
        <tr><td colspan="2"><br><b style="color: {t['text_secondary']};">Raw Hash Formats</b></td></tr>
        <tr><td>MD5 (32 hex)</td><td>SHA1 (40 hex)</td></tr>
        <tr><td>SHA224 (56 hex)</td><td>SHA256 (64 hex)</td></tr>
        <tr><td>SHA384 (96 hex)</td><td>SHA512 (128 hex)</td></tr>
        </table>
        <br><p style="color: {t['text_tertiary']};">Auto-detection identifies the format automatically based on hash structure and length.</p>
        """
    
    def _update_requirements_display(self):
        t = self.theme.current
        if self.john_available:
            self.req_output.setHtml(
                f"<h3 style='color:{t['success']};'>John the Ripper Found</h3>"
                f"<p>Status: <span style='color:{t['success']};'>Installed</span></p>"
                f"<p>Version: {self.john_version}</p>"
                f"<p>Location: {self.john_manager.john_path}</p>"
            )
            self.install_btn.setEnabled(False)
            self.install_btn.setText("Installed")
        else:
            self.req_output.setHtml(
                f"<h3 style='color:{t['error']};'>John the Ripper Not Found</h3>"
                f"<p>Status: <span style='color:{t['error']};'>Not Installed</span></p>"
                f"<p>Run: <code>sudo apt install john</code></p>"
            )
            self.install_btn.setEnabled(True)
            self.install_btn.setText("Install John the Ripper")
    
    def _refresh_john(self):
        if self.john_manager.find_john():
            self.john_available = True
            self.john_version = self.john_manager.get_version()
            self._update_john_badge()
            self._update_requirements_display()
        else:
            self.req_status.setText("John not found")
        self._apply_theme()
    
    def _install_john(self):
        reply = QMessageBox.question(
            self, "Install", "sudo apt install john -y?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.install_btn.setEnabled(False)
        self.req_status.setText("Installing...")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "john"], capture_output=True, timeout=120)
            if self.john_manager.find_john():
                self.john_available = True
                self.john_version = self.john_manager.get_version()
                self._update_john_badge()
                self._update_requirements_display()
                self.req_status.setText("")
        except Exception as e:
            self.req_status.setText(f"Error: {str(e)}")
        self._apply_theme()
    
    def _copy_result(self):
        text = self.results_output.toPlainText().strip()
        if text and text != "No match found in wordlist":
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Password copied!")
    
    def _start_reversal(self):
        hash_value = self.hash_input.toPlainText().strip()
        if not hash_value:
            QMessageBox.warning(self, "No Hash", "Please enter a hash value.")
            return
        if not self.wordlist_path:
            QMessageBox.warning(self, "No Wordlist", "Please configure a wordlist.")
            return
        if not self.john_available:
            QMessageBox.warning(self, "John Missing", "Please install John.")
            return
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.progress_bar.setValue(0)
        self.reverse_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        rules = self.rule_slot.rule_name if self.rule_slot.is_filled() else "Standard rules (recommended)"
        self.worker = HashReverseWorker(
            hash_value, self.wordlist_path, rules,
            self.split_parts, self.john_manager.john_path
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _stop_reversal(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
            self.status_output.append("Stopped")
            self.reverse_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def _on_progress(self, message):
        self.status_output.append(message)
    
    def _on_finished(self, success, message):
        self.reverse_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if success:
            if message == "No match found":
                self.results_output.setText("No match found in wordlist")
            else:
                self.results_output.setText(message)
                self.tabs.setCurrentIndex(2)
        else:
            self.results_output.setText(f"Error: {message}")
    
    def set_wordlist_config(self, wordlist_path, split_parts):
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self._update_badge()
    
    def _apply_theme(self):
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
        for attr in ['rule_grp', 'in_grp', 'req_group', 'formats_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'hash_input') and self.hash_input is not None:
            self.hash_input.setStyleSheet(
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
        if hasattr(self, 'req_output') and self.req_output is not None:
            self.req_output.setStyleSheet(
                f"QTextBrowser{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-size:{int(12 * scale)}px;}}"
            )
        if hasattr(self, 'formats_output') and self.formats_output is not None:
            self.formats_output.setStyleSheet(
                f"QTextBrowser{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-size:{int(12 * scale)}px;}}"
            )
        if hasattr(self, 'progress_bar') and self.progress_bar is not None:
            self.progress_bar.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'rule_slot') and self.rule_slot is not None:
            self.rule_slot.update_colors(t)
        for card in self.rule_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        
        self._update_badge()
        self._update_john_badge()
        if hasattr(self, 'req_output'):
            self._update_requirements_display()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()