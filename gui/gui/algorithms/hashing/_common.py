# gui/algorithms/hashing/_common.py
"""
Shared helpers for the hashing modules.

Includes the FULL john format table (100+ formats) so the AI can reverse
any hash the desktop Hash Reverse page handles, not just MD5/SHA-*.

The format table is the same one HashingPage.HashReverseWorker already
uses. When that page is eventually refactored to call into this module,
its behavior will be byte-for-byte identical because it's the same table.

The john --show parser is line-by-line (see parse_john_show) so a
multi-line --show output can't be flattened into a garbage password.
"""
import hashlib
import os
import re
import subprocess
import tempfile


# --------------------------------------------------------------------- #
# Raw hash length detection (MD5, SHA-1/224/256/384/512)
# --------------------------------------------------------------------- #
HASH_LENGTHS = {
    32:  'MD5',
    40:  'SHA-1',
    56:  'SHA-224',
    64:  'SHA-256',
    96:  'SHA-384',
    128: 'SHA-512',
}

HASH_REGEX = re.compile(r'\b([a-fA-F0-9]{8,128})\b')

JOHN_FORMAT = {
    'MD5':     'raw-md5',
    'SHA-1':   'raw-sha1',
    'SHA-224': 'raw-sha224',
    'SHA-256': 'raw-sha256',
    'SHA-384': 'raw-sha384',
    'SHA-512': 'raw-sha512',
}

PY_HASHERS = {
    'MD5':     hashlib.md5,
    'SHA-1':   hashlib.sha1,
    'SHA-224': hashlib.sha224,
    'SHA-256': hashlib.sha256,
    'SHA-384': hashlib.sha384,
    'SHA-512': hashlib.sha512,
}


def find_hash_in_text(text: str):
    """
    Return (hash_value, hash_type_or_None) if a hex hash is present.
    hash_type is only filled for the raw-hex family we can pre-identify
    by length. Everything else (bcrypt, NTLM, WPA, ...) returns None for
    the type and lets the format table decide at crack time.
    """
    if not text:
        return None, None
    m = HASH_REGEX.search(text)
    if not m:
        return None, None
    v = m.group(1)
    return v, HASH_LENGTHS.get(len(v))


def detect_hash_type(value: str):
    """Length-based guess, or None."""
    if not value:
        return None
    return HASH_LENGTHS.get(len(value.strip()))


# --------------------------------------------------------------------- #
# FULL john format table (100+ formats)
# --------------------------------------------------------------------- #
def detect_format_info(hash_value: str):
    """
    Return (--format=..., display_name) for a hash string.

    Mirrors HashingPage.HashReverseWorker._detect_format_info exactly,
    so the AI and the desktop page identify formats identically.

    Returns ("", "auto-detect") when nothing matches - john will try to
    figure it out on its own.
    """
    if ':' in hash_value:
        parts = hash_value.split(':')
        clean_hash = parts[-1] if len(parts) > 1 else hash_value
    else:
        clean_hash = hash_value
    clean_hash = clean_hash.strip()
    hlen = len(clean_hash)
    is_hex = bool(re.match(r'^[0-9a-fA-F]+$', clean_hash))

    # --- Unix crypt ---
    if clean_hash.startswith('$2a$') or clean_hash.startswith('$2b$') or clean_hash.startswith('$2y$'):
        return "--format=bcrypt", "bcrypt (Blowfish)"
    if clean_hash.startswith('$6$'):  return "--format=sha512crypt", "SHA-512 crypt"
    if clean_hash.startswith('$5$'):  return "--format=sha256crypt", "SHA-256 crypt"
    if clean_hash.startswith('$1$'):  return "--format=md5crypt", "MD5 crypt"
    if clean_hash.startswith('$y$'):  return "--format=yescrypt", "yescrypt"
    if clean_hash.startswith('$7$'):  return "--format=scrypt", "scrypt"
    if clean_hash.startswith('$argon2'): return "--format=argon2", "Argon2"
    if clean_hash.startswith('$md5$') or clean_hash.startswith('$md5,'):
        return "--format=md5crypt", "MD5 crypt (Sun)"
    if clean_hash.startswith('$sha1$'): return "--format=sha1crypt", "SHA1 crypt"

    # --- Windows / AD ---
    if clean_hash.startswith('$DCC2$'):     return "--format=mscash2", "MS Cache v2"
    if clean_hash.startswith('$netntlmv2$'):return "--format=netntlmv2", "NetNTLMv2"
    if clean_hash.startswith('$netntlm$'):  return "--format=netntlm", "NetNTLM"
    if clean_hash.startswith('$mschapv2$'): return "--format=MSCHAPv2", "MS-CHAPv2"
    if clean_hash.startswith('$DPAPImk$'):  return "--format=DPAPImk", "DPAPI Master Key"

    # --- Databases ---
    if clean_hash.startswith('$mysql$'):    return "--format=mysql", "MySQL"
    if clean_hash.startswith('$mysqlna$'):  return "--format=mysqlna", "MySQL NA"
    if clean_hash.startswith('$mssql12$'):  return "--format=mssql12", "MSSQL 2012"
    if clean_hash.startswith('$mssql05$'):  return "--format=mssql05", "MSSQL 2005"
    if clean_hash.startswith('$mssql$'):    return "--format=mssql", "MSSQL"
    if clean_hash.startswith('$oracle12c$'):return "--format=Oracle12C", "Oracle 12C"
    if clean_hash.startswith('$oracle11$'): return "--format=oracle11", "Oracle 11"
    if clean_hash.startswith('$oracle$'):   return "--format=oracle", "Oracle"
    if clean_hash.startswith('$postgres$'): return "--format=postgres", "PostgreSQL"
    if clean_hash.startswith('$mongodb$'):  return "--format=MongoDB", "MongoDB"
    if clean_hash.startswith('$sybase$'):   return "--format=SybaseASE", "Sybase ASE"
    if clean_hash.startswith('$scram$'):    return "--format=scram", "SCRAM"

    # --- Web apps ---
    if clean_hash.startswith('$P$') or clean_hash.startswith('$H$'):
        return "--format=phpass", "PHPass"
    if clean_hash.startswith('$PHPS$'):     return "--format=PHPS", "PHPS"
    if clean_hash.startswith('$Drupal7$'):  return "--format=Drupal7", "Drupal 7"
    if clean_hash.startswith('$S$') or clean_hash.startswith('$C$') or clean_hash.startswith('$D$'):
        return "--format=Drupal7", "Drupal"
    if clean_hash.startswith('$J$'):        return "--format=phpass", "Joomla"
    if clean_hash.startswith('$W$'):        return "--format=phpass", "WordPress"
    if clean_hash.startswith('$pbkdf2-sha512$'):
        return "--format=PBKDF2-HMAC-SHA512", "PBKDF2-SHA512"
    if clean_hash.startswith('$pbkdf2-sha256$'):
        return "--format=PBKDF2-HMAC-SHA256", "PBKDF2-SHA256"
    if clean_hash.startswith('$django-scrypt$'): return "--format=django-scrypt", "Django Scrypt"
    if clean_hash.startswith('$django$'):   return "--format=django", "Django"
    if clean_hash.startswith('$MediaWiki$'):return "--format=MediaWiki", "MediaWiki"
    if clean_hash.startswith('$bitwarden$'):return "--format=Bitwarden", "Bitwarden"

    # --- Kerberos / network protocols ---
    if clean_hash.startswith('$krb5asrep$'):return "--format=krb5asrep", "Kerberos AS-REP"
    if clean_hash.startswith('$krb5tgs$'):  return "--format=krb5tgs", "Kerberos TGS"
    if clean_hash.startswith('$krb5pa$'):   return "--format=krb5pa-sha1", "Kerberos PA"
    if clean_hash.startswith('$krb5$'):     return "--format=krb5", "Kerberos 5"
    if clean_hash.startswith('$chap$'):     return "--format=chap", "CHAP"
    if clean_hash.startswith('$tacacs$'):   return "--format=tacacs-plus", "TACACS+"
    if clean_hash.startswith('$radius$'):   return "--format=radius", "RADIUS"
    if clean_hash.startswith('$ssh$'):      return "--format=SSH", "SSH Private Key"
    if clean_hash.startswith('$ike$'):      return "--format=IKE", "IKE"
    if clean_hash.startswith('$sip$'):      return "--format=SIP", "SIP"
    if clean_hash.startswith('$SNMP$'):     return "--format=SNMP", "SNMP"
    if clean_hash.startswith('$xmpp$'):     return "--format=xmpp-scram", "XMPP SCRAM"

    # --- Archives ---
    if clean_hash.startswith('$zip2$'):     return "--format=ZIP", "ZIP (AES)"
    if clean_hash.startswith('$zip$'):      return "--format=ZIP", "ZIP"
    if clean_hash.startswith('$rar5$'):     return "--format=rar", "RAR5"
    if clean_hash.startswith('$rar$'):      return "--format=rar", "RAR"
    if clean_hash.startswith('$7z$'):       return "--format=7z", "7-Zip"
    if clean_hash.startswith('$pkzip$'):    return "--format=PKZIP", "PKZIP"

    # --- Disk encryption ---
    if clean_hash.startswith('$bitlocker$'):return "--format=BitLocker", "BitLocker"
    if clean_hash.startswith('$luks$'):     return "--format=LUKS", "LUKS"
    if clean_hash.startswith('$truecrypt$') or clean_hash.startswith('$veracrypt$'):
        return "--format=tc_sha512", "TrueCrypt/VeraCrypt"
    if clean_hash.startswith('$fvde$'):     return "--format=FVDE", "FileVault"

    # --- Documents ---
    if clean_hash.startswith('$office$'):   return "--format=Office", "MS Office"
    if clean_hash.startswith('$oldoffice$'):return "--format=oldoffice", "Old Office"
    if clean_hash.startswith('$pdf$'):      return "--format=PDF", "PDF"
    if clean_hash.startswith('$odf$'):      return "--format=ODF", "OpenDocument"
    if clean_hash.startswith('$keepass$'):  return "--format=KeePass", "KeePass"
    if clean_hash.startswith('$itunes$'):   return "--format=itunes-backup", "iTunes Backup"
    if clean_hash.startswith('$pst$'):      return "--format=PST", "Outlook PST"

    # --- VPN / network devices ---
    if clean_hash.startswith('$asa$'):      return "--format=asa-md5", "Cisco ASA"
    if clean_hash.startswith('$pix$'):      return "--format=pix-md5", "Cisco PIX"
    if clean_hash.startswith('$ios$') or clean_hash.startswith('$cisco$'):
        return "--format=md5crypt", "Cisco IOS"
    if clean_hash.startswith('$fortinet$'): return "--format=Fortigate256", "FortiGate 256"
    if clean_hash.startswith('$fortigate$'):return "--format=Fortigate", "FortiGate"
    if clean_hash.startswith('$juniper$'):  return "--format=md5crypt", "Juniper"
    if clean_hash.startswith('$solarwinds$'):return "--format=solarwinds", "SolarWinds"
    if clean_hash.startswith('$citrix$'):   return "--format=Citrix_NS10", "Citrix"

    # --- Blockchain ---
    if clean_hash.startswith('$bitcoin$'):  return "--format=Bitcoin", "Bitcoin"
    if clean_hash.startswith('$ethereum$'): return "--format=ethereum", "Ethereum"
    if clean_hash.startswith('$monero$'):   return "--format=monero", "Monero"
    if clean_hash.startswith('$electrum$'): return "--format=electrum", "Electrum"

    # --- Other apps ---
    if clean_hash.startswith('$gpg$') or clean_hash.startswith('$pgp$'):
        return "--format=gpg", "GPG/PGP"
    if clean_hash.startswith('$keychain$'): return "--format=keychain", "Keychain"
    if clean_hash.startswith('$keyring$'):  return "--format=keyring", "Keyring"
    if clean_hash.startswith('$keystore$'): return "--format=keystore", "Keystore"
    if clean_hash.startswith('$kwallet$'):  return "--format=kwallet", "KWallet"
    if clean_hash.startswith('$lastpass$'): return "--format=LastPass", "LastPass"
    if clean_hash.startswith('$lp$'):       return "--format=lpcli", "LastPass CLI"
    if clean_hash.startswith('$putty$'):    return "--format=PuTTY", "PuTTY"
    if clean_hash.startswith('$pwsafe$'):   return "--format=pwsafe", "Password Safe"
    if clean_hash.startswith('$android$'):  return "--format=AndroidBackup", "Android Backup"
    if clean_hash.startswith('$azure$'):    return "--format=AzureAD", "Azure AD"
    if clean_hash.startswith('$encfs$'):    return "--format=EncFS", "EncFS"
    if clean_hash.startswith('$dmg$'):      return "--format=dmg", "DMG"
    if clean_hash.startswith('$vmx$'):      return "--format=vmx", "VMware VMX"
    if clean_hash.startswith('$vnc$'):      return "--format=VNC", "VNC"
    if clean_hash.startswith('$openssl$'):  return "--format=openssl-enc", "OpenSSL"

    # --- Raw hex by length ---
    if hlen == 16 and is_hex and clean_hash == clean_hash.upper():
        return "--format=LM", "LM hash"
    if hlen == 32 and is_hex:  return "--format=Raw-MD5", "MD5"
    if hlen == 40 and is_hex:  return "--format=Raw-SHA1", "SHA1"
    if hlen == 56 and is_hex:  return "--format=Raw-SHA224", "SHA224"
    if hlen == 64 and is_hex:  return "--format=Raw-SHA256", "SHA256"
    if hlen == 96 and is_hex:  return "--format=Raw-SHA384", "SHA384"
    if hlen == 128 and is_hex: return "--format=Raw-SHA512", "SHA512"

    # --- WPA PSK (colon-delimited) ---
    if ':' in hash_value and len(hash_value.split(':')) >= 4:
        return "--format=wpapsk", "WPA PSK"

    return "", "auto-detect"


# --------------------------------------------------------------------- #
# john --show parsing (line-by-line, correct)
# --------------------------------------------------------------------- #
def parse_john_show(stdout: str):
    """
    Extract the cracked password from `john --show` output.

    john --show output for a cracked hash looks like:
        ?:rosaria:1000:1000:User:/home/rosaria:/bin/bash

        1 password hash cracked, 0 left

    We iterate line by line so the summary line can never glue itself
    onto the password. This is the fix for the 'rosaria 1 password
    hash cracked, 0 left' bug.
    """
    if not stdout:
        return None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('0 password'):
            continue
        if 'password hash' in line and 'left' in line:
            continue
        if ':' not in line:
            continue
        parts = line.split(':')
        if len(parts) < 2:
            continue
        pwd = parts[1].strip()
        if pwd and not pwd.startswith('$'):
            return pwd
    return None


# --------------------------------------------------------------------- #
# john invocation
# --------------------------------------------------------------------- #
def _john_run(hash_value: str, wordlist_path: str, fmt_arg: str = None,
              timeout: int = 120, progress_cb=None):
    """
    Write the hash to a temp file, run john --wordlist, then --show.

    fmt_arg may be:
      - None                 -> john auto-detects
      - "--format=raw-md5"   -> uses that format (leading '--format=' is
                                stripped before building the command)
    """
    def log(m):
        if progress_cb:
            progress_cb(m)

    fd, hash_file = tempfile.mkstemp(prefix='sokonalysis_hash_', suffix='.hash')
    os.close(fd)
    try:
        with open(hash_file, 'w') as f:
            f.write(f"{hash_value}\n")

        cmd = ['john']
        if fmt_arg:
            # Strip the --format= prefix if present
            if fmt_arg.startswith('--format='):
                cmd.append(fmt_arg)
            else:
                cmd.append(f'--format={fmt_arg}')
        cmd.extend(['--wordlist=' + wordlist_path, hash_file])

        try:
            log("Running john...")
            subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            log("john not found")
            return None
        except subprocess.TimeoutExpired:
            log("john timed out")
            # still try --show; a hit may have landed before the timeout

        show = subprocess.run(
            ['john', '--show', hash_file],
            capture_output=True, text=True
        )
        return parse_john_show(show.stdout)
    finally:
        try:
            os.remove(hash_file)
        except OSError:
            pass


def crack_with_python(hash_value: str, hash_type: str, wordlist_path: str,
                      cancelled_check=None):
    """
    Deterministic fallback for the raw-hex family
    (MD5, SHA-1, SHA-224/256/384/512).
    Returns the plaintext (str) or None.
    """
    algo = PY_HASHERS.get(hash_type)
    if algo is None:
        return None

    target = hash_value.lower()
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if cancelled_check and cancelled_check():
                    return None
                pw = line.rstrip('\r\n')
                if not pw:
                    continue
                if algo(pw.encode('utf-8', errors='ignore')).hexdigest() == target:
                    return pw
    except Exception:
        return None
    return None


# --------------------------------------------------------------------- #
# Public entry point used by the AI (and later, by the pages)
# --------------------------------------------------------------------- #
def reverse_auto(hash_value: str, wordlist_path: str,
                 progress_cb=None, cancelled_check=None):
    """
    Reverse ANY hash against a wordlist, auto-detecting format.

    Covers the same 100+ formats as the desktop Hash Reverse page:
    raw MD5/SHA-*, crypt, NTLM, Kerberos, WPA, ZIP/RAR/7z hashes, PDF,
    Office, LUKS, Bitcoin, Electrum, GPG, KeePass, PuTTY, ... everything
    john can handle with an explicit --format.

    Returns the plaintext (str) or None.
    """
    def log(m):
        if progress_cb:
            progress_cb(m)

    if not wordlist_path or not os.path.exists(wordlist_path):
        return None

    fmt_arg, display = detect_format_info(hash_value)
    log(f"Hash identified: {display}")
    log(f"Using wordlist: {os.path.basename(wordlist_path)}")

    pwd = _john_run(hash_value, wordlist_path, fmt_arg=fmt_arg,
                    timeout=120, progress_cb=progress_cb)
    if pwd:
        return pwd

    # If we identified it as a raw hex family, cross-check with Python -
    # john's --show can miss real hits due to pot-file / format mismatch.
    raw_type = HASH_LENGTHS.get(len(hash_value.strip()))
    if raw_type:
        log("Double-checking with direct comparison...")
        return crack_with_python(hash_value, raw_type, wordlist_path,
                                 cancelled_check=cancelled_check)

    return None