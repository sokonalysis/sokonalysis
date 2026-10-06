# gui/ai/help.py
"""
Contextual help for the AI chat.

Topic-based HTML replies, matched by keyword via gui.ai.matcher.

Public API:
    lookup(question) -> str | None
"""

from gui.ai import matcher


_LINK = 'color:#2563eb; text-decoration:none;'
_CODE = 'font-family:JetBrains Mono,monospace;'


# --------------------------------------------------------------------- #
# Topics
# --------------------------------------------------------------------- #
def _t_getting_started():
    return (
        "<b>Welcome to sokonalysis AI Assistant</b><br><br>"
        "Here's everything I can do, with copy-paste commands:<br><br>"

        "<b>1. Crack files</b><br>"
        "&nbsp;&nbsp;Drop a <b>.zip</b>, <b>.rar</b>, <b>.7z</b>, <b>.pdf</b>, "
        "<b>.docx</b>, or Wi-Fi capture (<b>.cap</b>, <b>.hccapx</b>) directly "
        "on the chat.<br>"
        f"&nbsp;&nbsp;You'll need a <b>wordlist</b> configured first — "
        f"<a href=\"http://sokonalysis/config/wordlist\" style=\"{_LINK}\">open Wordlist Settings</a>.<br><br>"

        "<b>2. Crack hashes</b><br>"
        "&nbsp;&nbsp;Just paste the hash. I'll auto-detect the format "
        "(MD5, SHA, bcrypt, NTLM, WPA, ... 100+).<br>"
        f"&nbsp;&nbsp;Example: <code style=\"{_CODE}\">5d41402abc4b2a76b9719d911017c592</code><br><br>"

        "<b>3. Crack ciphers (no key needed)</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">crack substitution &lt;ciphertext&gt;</code> — "
        "uses frequency analysis.<br>"
        f"&nbsp;&nbsp;Example: <code style=\"{_CODE}\">crack substitution vt qkt ztlzofu ziol...</code><br><br>"

        "<b>4. Encrypt / decrypt with a key</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">encrypt substitution hello world key=QWERTYUIOPASDFGHJKLZXCVBNM</code><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">decrypt substitution itssg vqkxb key=QWERTYUIOPASDFGHJKLZXCVBNM</code><br><br>"

        "<b>5. Open any tool by name</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">base64</code> &bull; "
        f"<code style=\"{_CODE}\">md5 reverse</code> &bull; "
        f"<code style=\"{_CODE}\">atbash</code> &bull; "
        f"<code style=\"{_CODE}\">caesar</code><br>"
        "&nbsp;&nbsp;Or browse a category: "
        f"<code style=\"{_CODE}\">ctf</code> &bull; "
        f"<code style=\"{_CODE}\">hashing</code><br><br>"

        "<b>6. Configure</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">open wordlist</code> &bull; "
        f"<code style=\"{_CODE}\">open john</code> &bull; "
        f"<code style=\"{_CODE}\">open quadgram</code><br><br>"

        "<b>7. Switch theme / layout</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">dark mode</code> &bull; "
        f"<code style=\"{_CODE}\">wide layout</code> &bull; "
        f"<code style=\"{_CODE}\">compact layout</code><br><br>"

        "<b>8. About / License / User Guide</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">about</code> &bull; "
        f"<code style=\"{_CODE}\">license</code> &bull; "
        f"<code style=\"{_CODE}\">user guide</code><br><br>"

        "Need details on a topic? Try: "
        f"<code style=\"{_CODE}\">help with hash</code> &bull; "
        f"<code style=\"{_CODE}\">help with substitution</code> &bull; "
        f"<code style=\"{_CODE}\">help with wordlist</code>"
    )


def _t_crack_file():
    return (
        "<b>How to crack a protected file</b><br><br>"

        "<b>Supported formats:</b><br>"
        "&nbsp;&nbsp;&bull; <b>.zip</b> — <a href=\"http://sokonalysis/option/Zip%20File/none\" "
        f"style=\"{_LINK}\">Zip File</a><br>"
        "&nbsp;&nbsp;&bull; <b>.rar</b> — <a href=\"http://sokonalysis/option/Rar%20File/none\" "
        f"style=\"{_LINK}\">Rar File</a><br>"
        "&nbsp;&nbsp;&bull; <b>.7z</b><br>"
        "&nbsp;&nbsp;&bull; <b>.pdf</b> — <a href=\"http://sokonalysis/option/PDF%20File/none\" "
        f"style=\"{_LINK}\">PDF File</a><br>"
        "&nbsp;&nbsp;&bull; <b>.docx / .xlsx / .pptx</b> — "
        "<a href=\"http://sokonalysis/option/Office%20Document/none\" "
        f"style=\"{_LINK}\">Office Document</a><br><br>"

        "<b>How to do it:</b><br>"
        "&nbsp;&nbsp;1. Make sure a <b>wordlist</b> is configured "
        f"(<a href=\"http://sokonalysis/config/wordlist\" style=\"{_LINK}\">Wordlist Settings</a>).<br>"
        "&nbsp;&nbsp;2. Drag the file onto the chat, or drop it on the "
        "AI input box.<br>"
        "&nbsp;&nbsp;3. I'll extract the hash with the right tool "
        "(zip2john, rar2john, pdf2john, office2john) and run John the "
        "Ripper against your wordlist.<br><br>"

        "<b>Tips:</b><br>"
        "&nbsp;&nbsp;&bull; The larger your wordlist, the better the "
        "chance of success.<br>"
        "&nbsp;&nbsp;&bull; For ZIP files without a configured wordlist, "
        "I'll also try a direct Python pass as a fallback.<br>"
        "&nbsp;&nbsp;&bull; If you need rules (<code>--rules</code>), "
        f"use the dedicated page: <a href=\"http://sokonalysis/option/Zip%20File/none\" "
        f"style=\"{_LINK}\">Zip File</a>."
    )


def _t_crack_hash():
    return (
        "<b>How to crack a hash</b><br><br>"

        "Just <b>paste the hash</b> into the chat. That's it.<br><br>"

        f"<code style=\"{_CODE}\">5d41402abc4b2a76b9719d911017c592</code>  (MD5)<br>"
        f"<code style=\"{_CODE}\">aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d</code>  (SHA-1)<br>"
        f"<code style=\"{_CODE}\">$2b$12$...</code>  (bcrypt)<br>"
        f"<code style=\"{_CODE}\">$DCC2$10240#user#...</code>  (MS Cache v2)<br><br>"

        "<b>Supported formats (100+):</b><br>"
        "&nbsp;&nbsp;Raw hex (MD5, SHA-1/224/256/384/512), Unix crypt "
        "(bcrypt, sha512crypt, md5crypt), Windows (NTLM, MS Cache, "
        "MS-CHAPv2), Kerberos, WPA, ZIP/RAR/7z/PDF/Office, LUKS, "
        "Bitcoin, Electrum, GPG, KeePass, PuTTY, and more.<br><br>"

        "<b>What happens:</b><br>"
        "&nbsp;&nbsp;1. I auto-detect the format by its signature.<br>"
        "&nbsp;&nbsp;2. Run John the Ripper with the right "
        "<code>--format=</code> and your wordlist.<br>"
        "&nbsp;&nbsp;3. For raw MD5/SHA-*, I also cross-check with a "
        "direct Python pass in case John's pot file missed a hit.<br><br>"

        "<b>Requirement:</b> a configured "
        f"<a href=\"http://sokonalysis/config/wordlist\" style=\"{_LINK}\">wordlist</a>.<br><br>"

        "For deeper options (rules, split-wordlist parallel cracking), "
        f"open <a href=\"http://sokonalysis/option/Hash%20Reverse/none\" "
        f"style=\"{_LINK}\">Hash Reverse</a>."
    )


def _t_substitution():
    return (
        "<b>Substitution cipher</b><br><br>"

        "A substitution cipher replaces each letter of the alphabet with "
        "another. The <b>key</b> is a 26-letter permutation, e.g. "
        f"<code style=\"{_CODE}\">QWERTYUIOPASDFGHJKLZXCVBNM</code>.<br><br>"

        "<b>Encrypt with a key:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">encrypt substitution hello world key=QWERTYUIOPASDFGHJKLZXCVBNM</code><br><br>"

        "<b>Decrypt with a key:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">decrypt substitution itssg vqkxb key=QWERTYUIOPASDFGHJKLZXCVBNM</code><br><br>"

        "<b>Crack without a key (frequency analysis):</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">crack substitution vt qkt ztlzofu ziol...</code><br>"
        "&nbsp;&nbsp;Uses a hill-climbing solver against quadgram "
        "frequencies. Works best with 50+ characters.<br><br>"

        "<b>Related pages:</b><br>"
        "&nbsp;&nbsp;&bull; <a href=\"http://sokonalysis/option/Decrypt%20with%20Known%20Key/none\" "
        f"style=\"{_LINK}\">Decrypt with Known Key</a><br>"
        "&nbsp;&nbsp;&bull; <a href=\"http://sokonalysis/option/Encrypt%20with%20Known%20Key/none\" "
        f"style=\"{_LINK}\">Encrypt with Known Key</a><br>"
        "&nbsp;&nbsp;&bull; <a href=\"http://sokonalysis/option/Frequency%20Analysis/none\" "
        f"style=\"{_LINK}\">Frequency Analysis</a>"
    )


def _t_wordlist():
    return (
        "<b>Wordlists</b><br><br>"

        "A wordlist is a plain text file with one candidate password per "
        "line. It's used by every cracking tool: file cracking, hash "
        "reversal, Wi-Fi, and steganography.<br><br>"

        "<b>Configure one:</b><br>"
        f"&nbsp;&nbsp;Type <code style=\"{_CODE}\">open wordlist</code> in the chat, "
        "or click <a href=\"http://sokonalysis/config/wordlist\" "
        f"style=\"{_LINK}\">Wordlist Settings</a>.<br><br>"

        "<b>Recommended wordlists:</b><br>"
        "&nbsp;&nbsp;&bull; <b>rockyou.txt</b> — 14M common passwords, "
        "the classic starting point.<br>"
        "&nbsp;&nbsp;&bull; <b>SecLists</b> — curated collections for "
        "different targets.<br>"
        "&nbsp;&nbsp;&bull; <b>crackstation-human-only.txt</b> — 64M "
        "human-chosen passwords.<br><br>"

        "<b>Where to get them:</b><br>"
        "&nbsp;&nbsp;&bull; Kali / Parrot: "
        f"<code style=\"{_CODE}\">/usr/share/wordlists/</code><br>"
        "&nbsp;&nbsp;&bull; Online: <a href=\"https://weakpass.com/\" "
        "style=\"color:#2563eb;\">weakpass.com</a>, "
        "<a href=\"https://github.com/danielmiessler/SecLists\" "
        "style=\"color:#2563eb;\">SecLists on GitHub</a><br><br>"

        "<b>Tip:</b> start with a small wordlist to test your setup, "
        "then switch to a larger one for real targets."
    )


def _t_quadgram():
    return (
        "<b>Quadgrams</b><br><br>"

        "A quadgram is a sequence of four letters (e.g. <b>tion</b>, "
        "<b>ther</b>). English text has very predictable quadgram "
        "frequencies — words like 'that', 'ther', 'atio' appear far more "
        "often than random letter sequences.<br><br>"

        "<b>Why it matters:</b><br>"
        "&nbsp;&nbsp;When cracking a substitution cipher, we try "
        "thousands of candidate keys. To decide which one is best, we "
        "score the decrypted text against a quadgram table — the higher "
        "the score, the more English the output looks.<br><br>"

        "<b>Default file:</b> <code>EN.json</code> at the project root.<br><br>"

        "<b>Custom file:</b><br>"
        f"&nbsp;&nbsp;Type <code style=\"{_CODE}\">open quadgram</code> in the chat, "
        "or click <a href=\"http://sokonalysis/config/json\" "
        f"style=\"{_LINK}\">Quadgram Settings</a>.<br><br>"

        "You only need a custom file if you're cracking text in a "
        "language other than English."
    )


def _t_john():
    return (
        "<b>John the Ripper</b><br><br>"

        "John the Ripper (JtR) is the engine behind most cracking in "
        "this app — file password recovery, hash reversal, Wi-Fi "
        "handshakes, Linux shadow files, and more.<br><br>"

        "<b>Do I need to install it?</b><br>"
        "&nbsp;&nbsp;On Linux, most of the app works out of the box if "
        "<code>john</code> is installed via your package manager.<br>"
        f"&nbsp;&nbsp;Check with: <code style=\"{_CODE}\">open john</code> "
        "in the chat.<br><br>"

        "<b>Install on Debian/Ubuntu/Parrot/Kali:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">sudo apt install john</code><br><br>"

        "<b>Install on macOS:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">brew install john-jumbo</code><br><br>"

        "<b>Install on Windows:</b><br>"
        "&nbsp;&nbsp;Download the <i>jumbo</i> build from "
        "<a href=\"https://www.openwall.com/john/\" style=\"color:#2563eb;\">openwall.com/john</a>.<br><br>"

        f"<a href=\"http://sokonalysis/config/john\" style=\"{_LINK}\">Open John Configuration</a>"
    )


def _t_navigation():
    return (
        "<b>Finding your way around</b><br><br>"

        "<b>Open a tool by name:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">base64</code> &bull; "
        f"<code style=\"{_CODE}\">md5 reverse</code> &bull; "
        f"<code style=\"{_CODE}\">atbash</code><br>"
        "&nbsp;&nbsp;I'll show its description and a clickable link.<br><br>"

        "<b>Browse a category:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">ctf</code> &bull; "
        f"<code style=\"{_CODE}\">hashing</code> &bull; "
        f"<code style=\"{_CODE}\">symmetric</code><br><br>"

        "<b>List all categories:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">categories</code><br><br>"

        "<b>Keyword search:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">sha</code> &bull; "
        f"<code style=\"{_CODE}\">caesar</code> &bull; "
        f"<code style=\"{_CODE}\">steganography</code><br>"
        "&nbsp;&nbsp;I'll match against tool names and category names."
    )


def _t_configure():
    return (
        "<b>Configuration</b><br><br>"

        "<b>Wordlist</b> — needed for every cracking tool:<br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">open wordlist</code><br><br>"

        "<b>Quadgram (EN.json)</b> — needed for substitution-crack:<br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">open quadgram</code><br><br>"

        "<b>John the Ripper</b> — the cracking engine:<br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">open john</code><br><br>"

        "Each opens its settings page directly. Type the phrase, or use "
        "the clickable links above."
    )


def _t_theme():
    return (
        "<b>Theme and layout</b><br><br>"

        "<b>Theme:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">dark mode</code> &bull; "
        f"<code style=\"{_CODE}\">light mode</code> &bull; "
        f"<code style=\"{_CODE}\">switch theme</code><br><br>"

        "<b>Layout:</b><br>"
        f"&nbsp;&nbsp;<code style=\"{_CODE}\">compact layout</code> &bull; "
        f"<code style=\"{_CODE}\">wide layout</code> &bull; "
        f"<code style=\"{_CODE}\">default layout</code>"
    )


# --------------------------------------------------------------------- #
# Topic registry
# --------------------------------------------------------------------- #
_TOPICS = [
    {
        "key": "getting_started",
        "phrases": ["help", "what can you do", "what do you do",
                    "capabilities", "commands", "help me",
                    "what can i do", "show help"],
        "fn": _t_getting_started,
    },
    {
        "key": "crack_file",
        "phrases": ["help with file", "how do i crack a file",
                    "how to crack zip", "help with zip",
                    "help with rar", "help with pdf",
                    "help with office", "crack file help"],
        "fn": _t_crack_file,
    },
    {
        "key": "crack_hash",
        "phrases": ["help with hash", "how do i crack a hash",
                    "how to reverse hash", "help with hashing",
                    "how do i reverse a hash", "hash help"],
        "fn": _t_crack_hash,
    },
    {
        "key": "substitution",
        "phrases": ["help with substitution", "how do i use substitution",
                    "substitution help", "how to crack substitution",
                    "how to decrypt substitution"],
        "fn": _t_substitution,
    },
    {
        "key": "wordlist",
        "phrases": ["help with wordlist", "what is a wordlist",
                    "how do i configure wordlist", "wordlist help",
                    "where do i get a wordlist"],
        "fn": _t_wordlist,
    },
    {
        "key": "quadgram",
        "phrases": ["help with quadgram", "what is a quadgram",
                    "quadgram help", "help with json",
                    "help with ngram"],
        "fn": _t_quadgram,
    },
    {
        "key": "john",
        "phrases": ["help with john", "what is john",
                    "how do i install john", "john the ripper help",
                    "john help"],
        "fn": _t_john,
    },
    {
        "key": "navigation",
        "phrases": ["help with navigation", "how do i find a tool",
                    "how do i navigate", "navigation help"],
        "fn": _t_navigation,
    },
    {
        "key": "configure",
        "phrases": ["help with configure", "how do i configure",
                    "configuration help"],
        "fn": _t_configure,
    },
    {
        "key": "theme",
        "phrases": ["help with theme", "help with layout",
                    "how do i change theme", "theme help"],
        "fn": _t_theme,
    },
]


_THRESHOLD = 0.75


def lookup(question):
    """
    Return an HTML help reply matching the question, or None.

    Exact 'help' matches the getting-started overview.
    'help with X' matches a specific topic.
    """
    if not question:
        return None
    q = question.strip().lower()
    if not q:
        return None

    # Exact / near-exact match on getting_started first
    gs = _TOPICS[0]
    for phrase in gs["phrases"]:
        if q == phrase:
            return gs["fn"]()

    # Topic-specific matches
    best_score = 0.0
    best_topic = None
    for topic in _TOPICS[1:]:
        s, _ = matcher.score(q, topic["phrases"])
        if s > best_score:
            best_score = s
            best_topic = topic

    if best_topic and best_score >= _THRESHOLD:
        return best_topic["fn"]()

    # Fallback: query starts with 'help' and mentions a topic word
    if q.startswith('help'):
        for topic in _TOPICS[1:]:
            if topic["key"] in q:
                return topic["fn"]()

    return None