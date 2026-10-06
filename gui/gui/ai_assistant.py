# gui/ai_assistant.py
"""
AI Assistant - step 6: file / stego / hash / substitution cracking
+ contextual help + navigation + tool links.

Routes to:
  - gui.algorithms.file_crack     (ZIP, RAR, 7z, PDF, Office, Wi-Fi)
  - gui.algorithms.steganography  (image/audio hidden content)
  - gui.algorithms.hashing        (MD5/SHA-* + 100+ formats via john)
  - gui.algorithms.substitution   (encrypt / decrypt / crack)
  - gui.ai.help                   (contextual help topics)
  - gui.ai.navigation             (theme/layout/about/config intents)
  - gui.ai.links                  (tool description + clickable link)

This file contains NO cracking logic itself. Every crack is a call
into gui.algorithms.
"""
from PySide6.QtCore import QThread, Signal
from gui.user_preferences import user_prefs
from gui.algorithms import file_crack
from gui.algorithms import steganography
from gui.algorithms import hashing
from gui.algorithms import substitution
from gui.ai import help as help_module
from gui.ai import navigation
from gui.ai import links
import os
import re


class AIAssistantWorker(QThread):
    """
    AI Assistant worker.

    Dispatches user input to the modules we've extracted so far.
    """
    response_ready = Signal(str)
    action_requested = Signal(str, str)
    progress_update = Signal(str)
    cancelled = False

    _last_response = ""

    def __init__(self, question, dropped_file=None, main_window=None):
        super().__init__()
        self.question = (question or "").lower().strip()
        self.dropped_file = dropped_file
        self.main_window = main_window

    def cancel(self):
        AIAssistantWorker.cancelled = True

    # ------------------------------------------------------------------ #
    # Theming helpers
    # ------------------------------------------------------------------ #
    def _format_result(self, value, label=None):
        """
        Format a cracked value for display using the app's REAL theme colors.
        """
        if value is None:
            return value

        value = str(value).strip()
        if not value:
            return value

        if label is None:
            label = "Passphrase" if (' ' in value or len(value) > 20) else "Password"

        text_color = '#000000'
        muted_color = '#495057'

        try:
            if self.main_window is not None and hasattr(self.main_window, 'theme'):
                theme = self.main_window.theme.current
                text_color = theme.get('text', text_color)
                muted_color = theme.get('text_secondary', muted_color)
        except Exception:
            pass

        return (
            f'<div style="color:{text_color};font-weight:600;font-size:14px;">'
            f'Results: {value}</div>'
            f'<div style="color:{muted_color};font-size:11px;margin-top:2px;">'
            f'Type: {label}</div>'
        )

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #
    def run(self):
        AIAssistantWorker.cancelled = False
        response = self._generate_response()
        if response:
            response = f'<div style="margin:8px 0 8px 0;line-height:1.5;">{response}</div>'
        AIAssistantWorker._last_response = response
        self.response_ready.emit(response)

    def _generate_response(self):
        if self.dropped_file:
            return self._handle_dropped_file()

        hash_reply = self._handle_hash_in_question(self.question)
        if hash_reply is not None:
            return hash_reply

        sub_reply = self._handle_substitution_in_question(self.question)
        if sub_reply is not None:
            return sub_reply

        # Contextual help (before navigation so 'help' wins over any
        # navigation intent that might also match)
        help_reply = help_module.lookup(self.question)
        if help_reply is not None:
            return help_reply

        nav = navigation.route(self.question)
        if nav is not None:
            action, payload, reply = nav
            if action:
                self.action_requested.emit(action, payload or '')
            return reply

        tool_match = links.lookup(self.question, _build_options_index())
        if tool_match:
            return tool_match

        return "I don't know that one yet."

    # ------------------------------------------------------------------ #
    # Dropped-file dispatch
    # ------------------------------------------------------------------ #
    def _handle_dropped_file(self):
        if not self.dropped_file:
            return "Could not analyze the file."

        filename = os.path.basename(self.dropped_file)
        _, file_ext = os.path.splitext(filename)
        file_ext = file_ext.lower()

        if file_ext in ('.txt', '.lst', '.dict', '.wordlist'):
            self.progress_update.emit(f"Loading wordlist: {filename}...")
            return f"Wordlist ready: {filename}"

        if file_ext == '.zip':
            return self._crack_zip(self.dropped_file, filename)

        if file_ext == '.rar':
            return self._crack_rar(self.dropped_file, filename)

        if file_ext == '.7z':
            return self._crack_7z(self.dropped_file, filename)

        if file_ext == '.pdf':
            return self._crack_pdf(self.dropped_file, filename)

        if file_ext in ('.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt'):
            return self._crack_office(self.dropped_file, filename)

        if file_ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif',
                        '.tiff', '.webp', '.wav', '.mp3', '.ogg', '.flac'):
            return self._analyze_stego(self.dropped_file, filename)

        if file_ext in ('.cap', '.hccapx', '.pcap', '.pcapng'):
            return self._crack_wifi(self.dropped_file, filename)

        return f"Dropped {filename}. I don't recognise that file type yet."

    # ------------------------------------------------------------------ #
    # File crackers - delegate to gui.algorithms.file_crack
    # ------------------------------------------------------------------ #
    def _get_wordlist(self):
        wl = getattr(user_prefs, 'wordlist_path', '')
        return wl if wl and os.path.exists(wl) else None

    def _crack_zip(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_zip(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd) if pwd else "Password not found in wordlist."

    def _crack_rar(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_rar(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd) if pwd else "Password not found in wordlist."

    def _crack_7z(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_7z(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd) if pwd else "Password not found in wordlist."

    def _crack_pdf(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_pdf(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd) if pwd else "Password not found in wordlist."

    def _crack_office(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_office(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd) if pwd else "Password not found in wordlist."

    def _crack_wifi(self, filepath, filename):
        wl = self._get_wordlist()
        if not wl:
            self.progress_update.emit("No wordlist configured")
            return "No wordlist configured. Drop a wordlist file first."
        pwd = file_crack.crack_wifi(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        return self._format_result(pwd, label="Passphrase") if pwd \
               else "Password not found in wordlist."

    # ------------------------------------------------------------------ #
    # Steganography
    # ------------------------------------------------------------------ #
    def _analyze_stego(self, filepath, filename):
        wl = self._get_wordlist()
        content = steganography.extract(
            filepath, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        if content:
            return self._format_result(content, label="Extracted data")
        return "No hidden data found."

    # ------------------------------------------------------------------ #
    # Hash cracking
    # ------------------------------------------------------------------ #
    def _handle_hash_in_question(self, question):
        hash_value, _ = hashing.find_hash_in_text(question)

        if hash_value is None:
            stripped = question.strip()
            if stripped.startswith('$') and len(stripped) > 20:
                hash_value = stripped

        if hash_value is None:
            return None

        wl = self._get_wordlist()
        if not wl:
            return (
                f"That looks like a possible hash "
                f"(<b>{len(hash_value)} characters</b>), but no wordlist "
                f"is configured so I can't attempt it.<br><br>"
                f"Drop a wordlist file, or open <b>Hash Reverse</b> and "
                f"select the format manually."
            )

        pwd = hashing.reverse_auto(
            hash_value, wl,
            progress_cb=self.progress_update.emit,
            cancelled_check=lambda: AIAssistantWorker.cancelled,
        )
        if pwd:
            return self._format_result(pwd)
        return "Password not found in wordlist."

    # ------------------------------------------------------------------ #
    # Substitution cipher - delegates to gui.algorithms.substitution
    # ------------------------------------------------------------------ #
    def _handle_substitution_in_question(self, question):
        """
        Handle:
          encrypt substitution <text> key=<26 letters>
          decrypt substitution <text> key=<26 letters>
          decrypt substitution <text>            -> frequency analysis
          crack substitution <text>              -> frequency analysis
        """
        q = question.strip()
        q_lower = q.lower()

        if q_lower.startswith('encrypt substitution'):
            op, rest = 'encrypt', q[len('encrypt substitution'):].strip()
        elif q_lower.startswith('decrypt substitution'):
            op, rest = 'decrypt', q[len('decrypt substitution'):].strip()
        elif q_lower.startswith('crack substitution'):
            op, rest = 'crack', q[len('crack substitution'):].strip()
        else:
            return None

        if not rest:
            if op == 'encrypt':
                return (
                    "Please include the text and the key.<br><br>"
                    "Example: <code>encrypt substitution hello world "
                    "key=QWERTYUIOPASDFGHJKLZXCVBNM</code>"
                )
            return (
                "Please include the ciphertext.<br><br>"
                "Example: <code>decrypt substitution "
                "vt qkt ztlzofu ziol qhhsoeqzogf ygk ozl tyytezoctftll</code>"
            )

        key = None
        m = re.search(r'key\s*=\s*([A-Za-z]{26})', rest, re.IGNORECASE)
        if m:
            key = m.group(1)
            rest = (rest[:m.start()] + rest[m.end():]).strip()

        if op == 'encrypt':
            if not key:
                return (
                    f"Please include the 26-letter key.<br><br>"
                    f"Example: <code>encrypt substitution "
                    f"{rest or 'hello world'} key=QWERTYUIOPASDFGHJKLZXCVBNM</code>"
                )
            try:
                result = substitution.encrypt(rest, key)
            except ValueError as e:
                return f"<b>Invalid key:</b> {e}"
            return self._format_result(result, label="Ciphertext")

        if op == 'decrypt' and key:
            try:
                result = substitution.decrypt(rest, key)
            except ValueError as e:
                return f"<b>Invalid key:</b> {e}"
            return self._format_result(result, label="Plaintext")

        # No key: crack via frequency analysis
        qg = self._get_quadgram_path()
        if not qg:
            return (
                "Quadgram file (EN.json) not found. Place EN.json at the "
                "project root, or configure it via "
                "<b>Config → Quadgram Settings</b>."
            )

        self.progress_update.emit("Running frequency analysis...")
        try:
            plaintext, key_str = substitution.crack(
                rest, qg,
                progress_cb=self.progress_update.emit,
                cancelled_check=lambda: AIAssistantWorker.cancelled,
            )
        except (FileNotFoundError, ValueError) as e:
            return f"<b>Error:</b> {e}"

        return (
            f"{self._format_result(plaintext, label='Plaintext')}"
            f"<div style='margin-top:6px;font-family:JetBrains Mono;font-size:12px;'>"
            f"<b>Recovered key:</b> {key_str}</div>"
        )

    def _get_quadgram_path(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, 'EN.json'),
            os.path.join(base_dir, 'gui', 'EN.json'),
            os.path.join(base_dir, 'assets', 'EN.json'),
        ]
        try:
            configured = getattr(user_prefs, 'json_path', '')
            if configured:
                candidates.insert(0, configured)
        except Exception:
            pass
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None


# --------------------------------------------------------------------- #
# Options index builder (used by links.lookup)
# --------------------------------------------------------------------- #
def _build_options_index():
    """
    Build {name.lower(): {'name', 'description', 'category', 'children'}}
    from the live search registry.
    """
    from gui.search_registry import get_all_options

    all_options = get_all_options()
    index = {}

    for category, options in all_options.items():
        for opt in options:
            name = opt[0] if isinstance(opt, tuple) else opt
            desc = opt[1] if isinstance(opt, tuple) and len(opt) > 1 else ""
            key = name.lower()
            index[key] = {
                'name': name,
                'description': desc,
                'category': category,
                'children': [],
            }

    for category in all_options.keys():
        cat_lower = category.lower()
        if cat_lower in index:
            children = []
            for sub in all_options[category]:
                sub_name = sub[0] if isinstance(sub, tuple) else sub
                sub_desc = sub[1] if isinstance(sub, tuple) and len(sub) > 1 else ""
                children.append({'name': sub_name, 'description': sub_desc})
            index[cat_lower]['children'] = children

    return index