#!/usr/bin/env python3
"""
HASH REVERSER BY SPLITTING WORDLIST
Split wordlist into parts for parallel password cracking
Multiple John instances for faster hash reversal
SOKONALYSIS - Created by Soko James
Following Sokonalysis C++ Style Guidelines for Sub-options
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import platform
import threading
from pathlib import Path
from datetime import datetime
from multiprocessing import cpu_count
import re

# ANSI color codes - matching C++ style from main.cpp
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
ORANGE = '\033[38;5;208m'
WHITE = '\033[37m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Tag functions with consistent spacing - matching C++ style
def tag_asterisk(): return YELLOW + "[*]" + RESET + " "
def tag_plus(): return GREEN + "[+]" + RESET + " "
def tag_minus(): return GREEN + "[-]" + RESET + " "
def tag_exclamation(): return RED + "[!]" + RESET + " "
def tag_gt(): return YELLOW + "[>]" + RESET + " "
def tag_x(): return RED + "[x]" + RESET + " "
def tag_question(): return ORANGE + "[?]" + RESET + " "
def tag_hash(): return CYAN + "[#]" + RESET + " "

class WordlistSplitter:
    def __init__(self):
        self.john_path = "john"
        self.current_dir = os.getcwd()
        self.temp_dir = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.wordlist_parts = []
        self.cracked_password = None
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        self.hash_format = ""
        
    def show_error(self, message):
        """Display error message in red with [x] tag"""
        print(tag_x() + message)
    
    def show_success(self, message):
        """Display success message in green with [+] tag"""
        print(tag_plus() + message)
    
    def show_info(self, message):
        """Display info message in cyan with [#] tag"""
        print(tag_hash() + message)
    
    def show_warning(self, message):
        """Display warning message in orange with [!] tag"""
        print(tag_exclamation() + message)
    
    def check_tools(self):
        """Check if required tools are available"""
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                self.show_error("John the Ripper not working properly")
                return False
        except FileNotFoundError:
            self.show_error("John the Ripper not found. Please install john.")
            return False
        
        # Check for default wordlist
        wordlist_paths = [
            self.default_wordlist,
            "wordlists/wordlist.txt",
            "../wordlists/wordlist.txt",
            "/usr/share/wordlists/rockyou.txt"
        ]
        
        for path in wordlist_paths:
            if os.path.exists(path):
                self.default_wordlist = path
                break
        
        return True
    
    def count_words(self, filepath):
        """Count words in a file"""
        if not os.path.exists(filepath):
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def format_size(self, size):
        """Format file size in human readable format"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024*1024:
            return f"{size/1024:.1f}KB"
        else:
            return f"{size/(1024*1024):.1f}MB"
    
    def detect_hash_format(self, hash_value):
        """Auto-detect hash format - supports ALL John formats"""
        # Clean the hash
        if ':' in hash_value:
            parts = hash_value.split(':')
            potential_hash = parts[1] if len(parts) >= 2 else hash_value
        else:
            potential_hash = hash_value
        
        clean_hash = potential_hash.strip()
        
        # ==================== UNIX CRYPT FORMATS ====================
        if clean_hash.startswith('$1$'):
            return ("md5crypt", "MD5 crypt")
        elif clean_hash.startswith('$2a$') or clean_hash.startswith('$2b$') or clean_hash.startswith('$2y$'):
            return ("bcrypt", "Blowfish crypt")
        elif clean_hash.startswith('$5$'):
            return ("sha256crypt", "SHA-256 crypt")
        elif clean_hash.startswith('$6$'):
            return ("sha512crypt", "SHA-512 crypt")
        elif clean_hash.startswith('$y$'):
            return ("crypt", "Yescrypt")
        elif clean_hash.startswith('$7$'):
            return ("scrypt", "Scrypt")
        elif clean_hash.startswith('$argon2'):
            return ("argon2", "Argon2")
        elif clean_hash.startswith('$md5$'):
            return ("md5crypt", "MD5 crypt")
        elif clean_hash.startswith('$sha1$'):
            return ("sha1crypt", "SHA1 crypt")
        elif clean_hash.startswith('$md5,'):
            return ("SunMD5", "SunMD5")
        elif len(clean_hash) == 13 and clean_hash.isalnum():
            return ("descrypt", "DES crypt")
        elif len(clean_hash) == 20 and clean_hash.startswith('_'):
            return ("bsdicrypt", "BSDI crypt")
        elif clean_hash.startswith('$dynamic_'):
            return ("dynamic_n", "Dynamic")
        
        # ==================== WINDOWS FORMATS ====================
        elif len(clean_hash) == 32 and all(c in '0123456789ABCDEF' for c in clean_hash.upper()):
            return ("NT", "NT hash")
        elif len(clean_hash) == 16 and all(c in '0123456789ABCDEF' for c in clean_hash.upper()):
            return ("LM", "LM hash")
        elif ':$' in hash_value and ':::' in hash_value:
            return ("mscash", "MS Cache v1")
        elif '$DCC2$' in clean_hash:
            return ("mscash2", "MS Cache v2")
        elif clean_hash.startswith('$netntlm$'):
            return ("netntlm", "NetNTLM")
        elif clean_hash.startswith('$netntlmv2$'):
            return ("netntlmv2", "NetNTLMv2")
        elif clean_hash.startswith('$netlm$'):
            return ("netlm", "NetLM")
        elif clean_hash.startswith('$netlmv2$'):
            return ("netlmv2", "NetLMv2")
        elif clean_hash.startswith('$nethalflm$'):
            return ("nethalflm", "NetHalfLM")
        elif clean_hash.startswith('$mschapv2$'):
            return ("MSCHAPv2", "MS-CHAPv2")
        
        # ==================== DATABASE FORMATS ====================
        elif clean_hash.startswith('$mysql$'):
            return ("mysql", "MySQL")
        elif clean_hash.startswith('$mysqlna$'):
            return ("mysqlna", "MySQL NA")
        elif '*' in clean_hash and len(clean_hash) == 40:
            return ("mysql-sha1", "MySQL SHA1")
        elif clean_hash.startswith('$mssql$'):
            return ("mssql", "MSSQL")
        elif clean_hash.startswith('$mssql05$'):
            return ("mssql05", "MSSQL 2005")
        elif clean_hash.startswith('$mssql12$'):
            return ("mssql12", "MSSQL 2012")
        elif clean_hash.startswith('$oracle$'):
            return ("oracle", "Oracle")
        elif clean_hash.startswith('$oracle11$'):
            return ("oracle11", "Oracle 11")
        elif clean_hash.startswith('$oracle12c$'):
            return ("Oracle12C", "Oracle 12C")
        elif clean_hash.startswith('S:') and len(clean_hash) == 60:
            return ("oracle", "Oracle S:")
        elif clean_hash.startswith('$postgres$'):
            return ("postgres", "PostgreSQL")
        elif clean_hash.startswith('$mongodb$'):
            return ("MongoDB", "MongoDB")
        elif clean_hash.startswith('$scram$'):
            return ("scram", "SCRAM")
        elif clean_hash.startswith('$sybase$'):
            return ("SybaseASE", "Sybase ASE")
        
        # ==================== WEB APPLICATION FORMATS ====================
        elif clean_hash.startswith('$P$') or clean_hash.startswith('$H$'):
            return ("phpass", "PHPass")
        elif clean_hash.startswith('$PHPS$'):
            return ("PHPS", "PHPS")
        elif clean_hash.startswith('$Drupal7$'):
            return ("Drupal7", "Drupal 7")
        elif clean_hash.startswith('$S$') or clean_hash.startswith('$C$') or clean_hash.startswith('$D$'):
            return ("Drupal7", "Drupal")
        elif clean_hash.startswith('$J$') or clean_hash.startswith('$joomla$'):
            return ("phpass", "Joomla")
        elif clean_hash.startswith('$W$') or clean_hash.startswith('$wordpress$'):
            return ("phpass", "WordPress")
        elif clean_hash.startswith('$pbkdf2-sha256$'):
            return ("PBKDF2-HMAC-SHA256", "PBKDF2-SHA256")
        elif clean_hash.startswith('$pbkdf2-sha512$'):
            return ("PBKDF2-HMAC-SHA512", "PBKDF2-SHA512")
        elif clean_hash.startswith('$django$'):
            return ("django", "Django")
        elif clean_hash.startswith('$django-scrypt$'):
            return ("django-scrypt", "Django Scrypt")
        elif clean_hash.startswith('$MediaWiki$'):
            return ("MediaWiki", "MediaWiki")
        elif clean_hash.startswith('$bitwarden$'):
            return ("Bitwarden", "Bitwarden")
        
        # ==================== NETWORK PROTOCOL FORMATS ====================
        elif clean_hash.startswith('$krb5$'):
            return ("krb5", "Kerberos 5")
        elif clean_hash.startswith('$krb5asrep$'):
            return ("krb5asrep", "Kerberos AS-REP")
        elif clean_hash.startswith('$krb5tgs$'):
            return ("krb5tgs", "Kerberos TGS")
        elif clean_hash.startswith('$krb5pa$'):
            return ("krb5pa-sha1", "Kerberos PA")
        elif clean_hash.startswith('$chap$'):
            return ("chap", "CHAP")
        elif clean_hash.startswith('$tacacs$'):
            return ("tacacs-plus", "TACACS+")
        elif clean_hash.startswith('$radius$'):
            return ("radius", "RADIUS")
        elif clean_hash.startswith('$ssh$'):
            return ("SSH", "SSH")
        elif clean_hash.startswith('$ike$'):
            return ("IKE", "IKE")
        elif clean_hash.startswith('$eigrp$'):
            return ("eigrp", "EIGRP")
        elif clean_hash.startswith('$ospf$'):
            return ("ospf", "OSPF")
        elif clean_hash.startswith('$sip$'):
            return ("SIP", "SIP")
        elif clean_hash.startswith('$SNMP$'):
            return ("SNMP", "SNMP")
        elif clean_hash.startswith('$xmpp$'):
            return ("xmpp-scram", "XMPP SCRAM")
        
        # ==================== ARCHIVE/COMPRESSION FORMATS ====================
        elif clean_hash.startswith('$zip$') or clean_hash.startswith('$zip2$'):
            return ("ZIP", "ZIP")
        elif clean_hash.startswith('$rar$') or clean_hash.startswith('$rar5$'):
            return ("rar", "RAR")
        elif clean_hash.startswith('$7z$'):
            return ("7z", "7-Zip")
        elif clean_hash.startswith('$pkzip$'):
            return ("PKZIP", "PKZIP")
        elif clean_hash.startswith('$securezip$'):
            return ("securezip", "SecureZIP")
        
        # ==================== DISK ENCRYPTION FORMATS ====================
        elif clean_hash.startswith('$bitlocker$'):
            return ("BitLocker", "BitLocker")
        elif clean_hash.startswith('$luks$'):
            return ("LUKS", "LUKS")
        elif clean_hash.startswith('$truecrypt$') or '$tc_' in clean_hash:
            return ("tc_sha512", "TrueCrypt")
        elif clean_hash.startswith('$veracrypt$'):
            return ("tc_sha512", "VeraCrypt")
        elif clean_hash.startswith('$fvde$'):
            return ("FVDE", "FileVault")
        elif clean_hash.startswith('$geli$'):
            return ("geli", "GELI")
        elif clean_hash.startswith('$ecryptfs$'):
            return ("eCryptfs", "eCryptfs")
        
        # ==================== DOCUMENT FORMATS ====================
        elif clean_hash.startswith('$office$'):
            return ("Office", "MS Office")
        elif clean_hash.startswith('$oldoffice$'):
            return ("oldoffice", "Old Office")
        elif clean_hash.startswith('$pdf$'):
            return ("PDF", "PDF")
        elif clean_hash.startswith('$odf$'):
            return ("ODF", "OpenDocument")
        elif clean_hash.startswith('$iwork$'):
            return ("iwork", "iWork")
        elif clean_hash.startswith('$keepass$'):
            return ("KeePass", "KeePass")
        elif clean_hash.startswith('$itunes$'):
            return ("itunes-backup", "iTunes Backup")
        elif clean_hash.startswith('$pst$'):
            return ("PST", "Outlook PST")
        
        # ==================== VPN/NETWORK DEVICE FORMATS ====================
        elif clean_hash.startswith('$asa$'):
            return ("asa-md5", "Cisco ASA")
        elif clean_hash.startswith('$pix$'):
            return ("pix-md5", "Cisco PIX")
        elif clean_hash.startswith('$ios$') or clean_hash.startswith('$cisco$'):
            return ("md5crypt", "Cisco IOS")
        elif clean_hash.startswith('$fortigate$'):
            return ("Fortigate", "FortiGate")
        elif clean_hash.startswith('$fortinet$'):
            return ("Fortigate256", "FortiGate 256")
        elif clean_hash.startswith('$juniper$'):
            return ("md5crypt", "Juniper")
        elif clean_hash.startswith('$solarwinds$'):
            return ("solarwinds", "SolarWinds")
        elif clean_hash.startswith('$citrix$'):
            return ("Citrix_NS10", "Citrix")
        elif clean_hash.startswith('$dahua$'):
            return ("dahua", "Dahua")
        elif clean_hash.startswith('$siemens$'):
            return ("Siemens-S7", "Siemens S7")
        elif clean_hash.startswith('$vmx$'):
            return ("vmx", "VMware VMX")
        elif clean_hash.startswith('$vnc$'):
            return ("VNC", "VNC")
        
        # ==================== BLOCKCHAIN/CRYPTO FORMATS ====================
        elif clean_hash.startswith('$bitcoin$'):
            return ("Bitcoin", "Bitcoin")
        elif clean_hash.startswith('$ethereum$'):
            return ("ethereum", "Ethereum")
        elif clean_hash.startswith('$litecoin$') or clean_hash.startswith('$bitshares$'):
            return ("bitshares", "Bitshares")
        elif clean_hash.startswith('$monero$'):
            return ("monero", "Monero")
        elif clean_hash.startswith('$tezos$'):
            return ("tezos", "Tezos")
        elif clean_hash.startswith('$electrum$'):
            return ("electrum", "Electrum")
        elif clean_hash.startswith('$multibit$'):
            return ("multibit", "MultiBit")
        
        # ==================== OTHER APPLICATION FORMATS ====================
        elif clean_hash.startswith('$android$'):
            return ("AndroidBackup", "Android Backup")
        elif clean_hash.startswith('$ansible$'):
            return ("ansible", "Ansible")
        elif clean_hash.startswith('$azure$'):
            return ("AzureAD", "Azure AD")
        elif clean_hash.startswith('$cloudkeychain$'):
            return ("cloudkeychain", "Cloud Keychain")
        elif clean_hash.startswith('$dashlane$'):
            return ("dashlane", "Dashlane")
        elif clean_hash.startswith('$enpass$'):
            return ("enpass", "Enpass")
        elif clean_hash.startswith('$gpg$') or clean_hash.startswith('$pgp$'):
            return ("gpg", "GPG/PGP")
        elif clean_hash.startswith('$keychain$'):
            return ("keychain", "Keychain")
        elif clean_hash.startswith('$keyring$'):
            return ("keyring", "Keyring")
        elif clean_hash.startswith('$keystore$'):
            return ("keystore", "Keystore")
        elif clean_hash.startswith('$kwallet$'):
            return ("kwallet", "KWallet")
        elif clean_hash.startswith('$lastpass$'):
            return ("LastPass", "LastPass")
        elif clean_hash.startswith('$lp$') or clean_hash.startswith('$lastpass-cli$'):
            return ("lpcli", "LastPass CLI")
        elif clean_hash.startswith('$putty$'):
            return ("PuTTY", "PuTTY")
        elif clean_hash.startswith('$pwsafe$') or clean_hash.startswith('$password$'):
            return ("pwsafe", "Password Safe")
        elif clean_hash.startswith('$signal$'):
            return ("Signal", "Signal")
        elif clean_hash.startswith('$telegram$'):
            return ("telegram", "Telegram")
        elif clean_hash.startswith('$VM$'):
            return ("OpenVMS", "OpenVMS")
        elif clean_hash.startswith('$axcrypt$'):
            return ("AxCrypt", "AxCrypt")
        elif clean_hash.startswith('$bestcrypt$'):
            return ("BestCrypt", "BestCrypt")
        elif clean_hash.startswith('$disk$'):
            return ("diskcryptor", "DiskCryptor")
        elif clean_hash.startswith('$saph$'):
            return ("saph", "SAP H")
        elif clean_hash.startswith('$sapb$'):
            return ("sapb", "SAP B")
        elif clean_hash.startswith('$sapg$'):
            return ("sapg", "SAP G")
        
        # ==================== LINKEDIN/LEET FORMATS ====================
        elif clean_hash.startswith('$linkedin$') or 'SHA1' in clean_hash.upper() and len(clean_hash) > 40:
            return ("Raw-SHA1-Linkedin", "LinkedIn SHA1")
        elif clean_hash.startswith('$leet$') or '$leet' in clean_hash.lower():
            return ("leet", "Leet")
        
        # ==================== RAW HASH FORMATS (by length) ====================
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("Raw-MD5", "Raw-MD5")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("Raw-MD4", "Raw-MD4")  # Same length, try MD5 first
        elif len(clean_hash) == 40 and re.match(r'^[0-9a-fA-F]{40}$', clean_hash):
            return ("Raw-SHA1", "Raw-SHA1")
        elif len(clean_hash) == 56 and re.match(r'^[0-9a-fA-F]{56}$', clean_hash):
            return ("Raw-SHA224", "Raw-SHA224")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("Raw-SHA256", "Raw-SHA256")
        elif len(clean_hash) == 96 and re.match(r'^[0-9a-fA-F]{96}$', clean_hash):
            return ("Raw-SHA384", "Raw-SHA384")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("Raw-SHA512", "Raw-SHA512")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("Raw-Keccak", "Raw-Keccak")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("Raw-Blake2", "Raw-Blake2")
        elif len(clean_hash) == 56 and re.match(r'^[0-9a-fA-F]{56}$', clean_hash):
            return ("Raw-SHA224", "Raw-SHA224")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("Raw-MD5u", "Raw-MD5u")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("Snefru-128", "Snefru-128")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("Snefru-256", "Snefru-256")
        elif len(clean_hash) == 40 and re.match(r'^[0-9a-fA-F]{40}$', clean_hash):
            return ("ripemd-160", "RIPEMD-160")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("ripemd-128", "RIPEMD-128")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("skein-256", "Skein-256")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("skein-512", "Skein-512")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("Stribog-256", "Stribog-256")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("Stribog-512", "Stribog-512")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("whirlpool", "Whirlpool")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("whirlpool0", "Whirlpool0")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("whirlpool1", "Whirlpool1")
        elif len(clean_hash) == 56 and re.match(r'^[0-9a-fA-F]{56}$', clean_hash):
            return ("HMAC-SHA224", "HMAC-SHA224")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("HMAC-SHA256", "HMAC-SHA256")
        elif len(clean_hash) == 96 and re.match(r'^[0-9a-fA-F]{96}$', clean_hash):
            return ("HMAC-SHA384", "HMAC-SHA384")
        elif len(clean_hash) == 128 and re.match(r'^[0-9a-fA-F]{128}$', clean_hash):
            return ("HMAC-SHA512", "HMAC-SHA512")
        elif len(clean_hash) == 40 and re.match(r'^[0-9a-fA-F]{40}$', clean_hash):
            return ("HMAC-SHA1", "HMAC-SHA1")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("HMAC-MD5", "HMAC-MD5")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("gost", "GOST")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("HAVAL-128-4", "HAVAL-128")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("HAVAL-256-3", "HAVAL-256")
        elif len(clean_hash) == 32 and re.match(r'^[0-9a-fA-F]{32}$', clean_hash):
            return ("MD2", "MD2")
        elif len(clean_hash) == 64 and re.match(r'^[0-9a-fA-F]{64}$', clean_hash):
            return ("mdc2", "MDC2")
        elif len(clean_hash) == 40 and re.match(r'^[0-9a-fA-F]{40}$', clean_hash):
            return ("has-160", "HAS-160")
        elif len(clean_hash) == 48 and re.match(r'^[0-9a-fA-F]{48}$', clean_hash):
            return ("Tiger", "Tiger")
        elif len(clean_hash) == 96 and re.match(r'^[0-9a-fA-F]{96}$', clean_hash):
            return ("Raw-SHA3", "Raw-SHA3")
        elif len(clean_hash) == 56 and re.match(r'^[0-9a-fA-F]{56}$', clean_hash):
            return ("Panama", "Panama")
        elif len(clean_hash) == 8 and re.match(r'^[0-9a-fA-F]{8}$', clean_hash):
            return ("CRC32", "CRC32")
        elif clean_hash.startswith('$salted$') or '$SSHA' in clean_hash:
            return ("Salted-SHA1", "Salted SHA1")
        elif clean_hash.startswith('$ssha512$'):
            return ("SSHA512", "SSHA512")
        elif clean_hash.startswith('$aix$'):
            return ("aix-ssha1", "AIX SSH")
        elif clean_hash.startswith('$racf$'):
            return ("RACF", "RACF")
        elif clean_hash.startswith('$as400$'):
            return ("as400-des", "AS400 DES")
        elif clean_hash.startswith('$qnx$'):
            return ("qnx", "QNX")
        elif clean_hash.startswith('$skey$'):
            return ("skey", "S/Key")
        elif clean_hash.startswith('$notes$'):
            return ("notes", "Lotus Notes")
        elif clean_hash.startswith('$lotus5$'):
            return ("lotus5", "Lotus 5")
        elif clean_hash.startswith('$lotus85$'):
            return ("lotus85", "Lotus 85")
        elif clean_hash.startswith('$domino$'):
            return ("dominosec", "Domino")
        elif clean_hash.startswith('$formspring$'):
            return ("FormSpring", "FormSpring")
        elif clean_hash.startswith('$hMailServer$'):
            return ("hMailServer", "hMailServer")
        elif clean_hash.startswith('$ipb2$'):
            return ("ipb2", "IPB2")
        elif clean_hash.startswith('$wbb3$'):
            return ("wbb3", "WoltLab BB3")
        elif clean_hash.startswith('$SL3$'):
            return ("SL3", "SL3")
        elif clean_hash.startswith('$solar$'):
            return ("solarwinds", "SolarWinds")
        elif clean_hash.startswith('$money$'):
            return ("money", "Money")
        elif clean_hash.startswith('$bfegg$'):
            return ("bfegg", "bfegg")
        elif clean_hash.startswith('$adxcrypt$'):
            return ("adxcrypt", "ADX Crypt")
        elif clean_hash.startswith('$agilekeychain$'):
            return ("agilekeychain", "Agile Keychain")
        elif clean_hash.startswith('$andOTP$'):
            return ("andOTP", "andOTP")
        elif clean_hash.startswith('$BKS$'):
            return ("BKS", "BKS")
        elif clean_hash.startswith('$blackberry$'):
            return ("Blackberry-ES10", "BlackBerry")
        elif clean_hash.startswith('$WoWSRP$'):
            return ("WoWSRP", "WoWSRP")
        elif clean_hash.startswith('$blockchain$'):
            return ("Blockchain", "Blockchain")
        elif clean_hash.startswith('$clipperz$'):
            return ("Clipperz", "Clipperz")
        elif clean_hash.startswith('$cq$'):
            return ("cq", "CQ")
        elif clean_hash.startswith('$cryptosafe$'):
            return ("cryptoSafe", "CryptoSafe")
        elif clean_hash.startswith('$dmd5$'):
            return ("dmd5", "DMD5")
        elif clean_hash.startswith('$dmg$'):
            return ("dmg", "DMG")
        elif clean_hash.startswith('$DPAPImk$'):
            return ("DPAPImk", "DPAPI Master Key")
        elif clean_hash.startswith('$dragonfly$'):
            return ("dragonfly3-32", "Dragonfly")
        elif clean_hash.startswith('$encfs$'):
            return ("EncFS", "EncFS")
        elif clean_hash.startswith('$epi$'):
            return ("EPI", "EPI")
        elif clean_hash.startswith('$episerver$'):
            return ("EPiServer", "EPiServer")
        elif clean_hash.startswith('$fde$'):
            return ("fde", "FDE")
        elif clean_hash.startswith('$hdaa$'):
            return ("hdaa", "HDAA")
        elif clean_hash.startswith('$hsrp$'):
            return ("hsrp", "HSRP")
        elif clean_hash.startswith('$known_hosts$'):
            return ("known_hosts", "Known Hosts")
        elif clean_hash.startswith('$kde$'):
            return ("kwallet", "KDE Wallet")
        elif clean_hash.startswith('$lp$'):
            return ("lp", "LastPass")
        elif clean_hash.startswith('$money$'):
            return ("money", "Money")
        elif clean_hash.startswith('$nk$'):
            return ("nk", "NK")
        elif clean_hash.startswith('$nsec3$'):
            return ("nsec3", "NSEC3")
        elif clean_hash.startswith('$o10glogon$'):
            return ("o10glogon", "O10G Logon")
        elif clean_hash.startswith('$o3logon$'):
            return ("o3logon", "O3 Logon")
        elif clean_hash.startswith('$o5logon$'):
            return ("o5logon", "O5 Logon")
        elif clean_hash.startswith('$openbsd$') or '$softraid' in clean_hash.lower():
            return ("OpenBSD-SoftRAID", "OpenBSD SoftRAID")
        elif clean_hash.startswith('$openssl$'):
            return ("openssl-enc", "OpenSSL Encryption")
        elif clean_hash.startswith('$padlock$'):
            return ("Padlock", "Padlock")
        elif clean_hash.startswith('$palshop$'):
            return ("Palshop", "Palshop")
        elif clean_hash.startswith('$pbkdf2$'):
            return ("PBKDF2-HMAC-SHA256", "PBKDF2")
        elif clean_hash.startswith('$pem$'):
            return ("PEM", "PEM")
        elif clean_hash.startswith('$pfx$'):
            return ("pfx", "PFX")
        elif clean_hash.startswith('$pgpdisk$'):
            return ("pgpdisk", "PGP Disk")
        elif clean_hash.startswith('$pgpsda$'):
            return ("pgpsda", "PGP SDA")
        elif clean_hash.startswith('$pgpwde$'):
            return ("pgpwde", "PGP WDE")
        elif clean_hash.startswith('$PHPS2$'):
            return ("PHPS2", "PHPS2")
        elif clean_hash.startswith('$po$'):
            return ("po", "PO")
        elif clean_hash.startswith('$RACF-KDFAES$'):
            return ("RACF-KDFAES", "RACF KDFAES")
        elif clean_hash.startswith('$radmin$'):
            return ("RAdmin", "RAdmin")
        elif clean_hash.startswith('$RAKP$'):
            return ("RAKP", "RAKP")
        elif clean_hash.startswith('$restic$'):
            return ("restic", "Restic")
        elif clean_hash.startswith('$rsvp$'):
            return ("rsvp", "RSVP")
        elif clean_hash.startswith('$RVARY$'):
            return ("RVARY", "RVARY")
        elif clean_hash.startswith('$sappse$'):
            return ("sappse", "SAP PSE")
        elif clean_hash.startswith('$sspr$'):
            return ("sspr", "SSPR")
        elif clean_hash.startswith('$strip$'):
            return ("STRIP", "STRIP")
        elif clean_hash.startswith('$sybase-prop$'):
            return ("Sybase-PROP", "Sybase PROP")
        elif clean_hash.startswith('$tcp-md5$'):
            return ("tcp-md5", "TCP MD5")
        elif clean_hash.startswith('$tripcode$'):
            return ("tripcode", "Tripcode")
        elif clean_hash.startswith('$vdi$'):
            return ("vdi", "VDI")
        elif clean_hash.startswith('$vtp$'):
            return ("vtp", "VTP")
        elif clean_hash.startswith('$xsha$'):
            return ("xsha", "XSHA")
        elif clean_hash.startswith('$xsha512$'):
            return ("xsha512", "XSHA512")
        elif clean_hash.startswith('$zed$'):
            return ("zed", "ZED")
        elif clean_hash.startswith('$ZipMonster$'):
            return ("ZipMonster", "ZipMonster")
        elif clean_hash == 'plaintext':
            return ("plaintext", "Plaintext")
        elif clean_hash == 'dummy':
            return ("dummy", "Dummy")
        
        # ==================== WIFI FORMATS ====================
        elif ':' in clean_hash and len(clean_hash.split(':')) == 4:
            return ("wpapsk", "WPA PSK")
        elif ':' in clean_hash and 'WPA' in clean_hash.upper():
            return ("wpapsk-pmk", "WPA PSK PMK")
        
        # ==================== DEFAULT FALLBACK ====================
        else:
            return ("", "Unknown (John will auto-detect)")
    
    def get_hash_input(self):
        """Get hash from user"""
        print()
        print(BLUE + "________________________ " + GREEN + "Hash Input" + BLUE + " _____________________________")
        print()
        
        hash_input = input(tag_gt() + "Enter hash: ").strip()
        
        if not hash_input:
            self.show_error("No hash provided")
            return False
        
        # Auto-detect hash format
        detected_format, detected_name = self.detect_hash_format(hash_input)
        self.hash_format = f"--format={detected_format}" if detected_format else ""
        
        print()
        if detected_format:
            self.show_info(f"Detected hash type: " + GREEN + f"{detected_name} ({detected_format})" + RESET)
        else:
            self.show_info(f"Hash type: " + YELLOW + f"{detected_name}" + RESET)
        
        # Format hash for John
        if ':' not in hash_input:
            formatted_hash = f"user:{hash_input}"
        else:
            formatted_hash = hash_input
        
        # Create hash file for John
        self.temp_dir = tempfile.mkdtemp(prefix="hash_crack_")
        self.hash_file = os.path.join(self.temp_dir, "hash.txt")
        
        try:
            with open(self.hash_file, 'w') as f:
                f.write(formatted_hash + '\n')
            
            print()
            self.show_success("Hash loaded successfully!")
            return True
            
        except Exception as e:
            self.show_error(f"Error creating hash file: {e}")
            return False
    
    def get_wordlist(self):
        """Get wordlist from user"""
        print()
        print(BLUE + "________________________ " + GREEN + "Wordlist" + BLUE + " _______________________________")
        print()
        print(YELLOW + "[1]" + RESET + f" Use default wordlist ({os.path.basename(self.default_wordlist)})")
        print(YELLOW + "[2]" + RESET + " Specify custom wordlist path")
        print(YELLOW + "[3]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select option (1-3): "))
            
            if choice == 1:
                if os.path.exists(self.default_wordlist):
                    return self.default_wordlist
                else:
                    self.show_error(f"Default wordlist not found: {self.default_wordlist}")
                    return None
            elif choice == 2:
                custom_path = input(tag_gt() + "Enter path to wordlist: ").strip()
                if os.path.exists(custom_path):
                    return custom_path
                else:
                    self.show_error(f"Wordlist not found: {custom_path}")
                    return None
            else:
                return None
                
        except ValueError:
            self.show_error("Please enter a valid number")
            return None
    
    def get_split_count(self, total_words):
        """Get number of parts to split wordlist into"""
        cpu_cores = cpu_count()
        recommended = min(cpu_cores, 8)
        
        print()
        print(BLUE + "________________________ " + GREEN + "Split Configuration" + BLUE + " ____________________")
        print()
        print(tag_hash() + f"Total words: " + YELLOW + f"{total_words:,}" + RESET)
        print(tag_hash() + f"CPU cores: " + YELLOW + f"{cpu_cores}" + RESET)
        print(tag_hash() + f"Recommended splits: " + GREEN + f"{recommended}" + RESET)
        print()
        print(YELLOW + "[1]" + RESET + f" Use recommended ({recommended} parts)")
        print(YELLOW + "[2]" + RESET + " Specify custom number of parts")
        print(YELLOW + "[3]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select option (1-3): "))
            
            if choice == 1:
                return recommended
            elif choice == 2:
                parts = int(input(tag_gt() + "Enter number of parts: "))
                if parts < 1:
                    self.show_error("Must be at least 1 part")
                    return None
                if parts > 32:
                    self.show_warning("Large number of parts may slow down system")
                    confirm = input(tag_question() + "Continue anyway? (y/n): ").lower()
                    if confirm != 'y':
                        return None
                return parts
            else:
                return None
        except ValueError:
            self.show_error("Please enter a valid number")
            return None
    
    def split_wordlist(self, wordlist_path, num_parts):
        """Split wordlist into multiple parts"""
        print()
        print(BLUE + "_______________________ " + GREEN + "Splitting Wordlist" + BLUE + " ______________________")
        print()
        print(tag_asterisk() + f"Splitting wordlist into " + YELLOW + f"{num_parts}" + RESET + " parts...")
        print()
        
        try:
            total_lines = self.count_words(wordlist_path)
            lines_per_part = total_lines // num_parts
            remainder = total_lines % num_parts
            
            self.wordlist_parts = []
            
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as infile:
                for part_num in range(num_parts):
                    part_file = os.path.join(self.temp_dir, f"part_{part_num + 1}.txt")
                    current_part_lines = lines_per_part + (1 if part_num < remainder else 0)
                    
                    with open(part_file, 'w', encoding='utf-8') as outfile:
                        for _ in range(current_part_lines):
                            line = infile.readline()
                            if not line:
                                break
                            outfile.write(line)
                    
                    if os.path.getsize(part_file) > 0:
                        self.wordlist_parts.append(part_file)
                        words = self.count_words(part_file)
                        size = self.format_size(os.path.getsize(part_file))
                        print(tag_plus() + f"Part {part_num + 1}: " + YELLOW + f"{words:,} words" + RESET + " " + CYAN + f"({size})" + RESET)
            
            if self.wordlist_parts:
                print()
                self.show_success(f"Split complete! " + GREEN + f"{len(self.wordlist_parts)}" + RESET + " parts created")
                return True
            else:
                self.show_error("Failed to create wordlist parts")
                return False
                
        except Exception as e:
            self.show_error(f"Error splitting wordlist: {e}")
            return False
    
    def select_rules(self):
        """Select rules for cracking"""
        print()
        print(BLUE + "_____________________________ " + GREEN + "Rules" + BLUE + " _____________________________")
        print()
        print(YELLOW + "[1]" + RESET + " No rules (fastest)")
        print(YELLOW + "[2]" + RESET + " Standard rules (recommended)")
        print(YELLOW + "[3]" + RESET + " All rules (slow but thorough)")
        print(BLUE + "_________________________________________________________________")
        print()
        
        choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        rules_map = {
            "1": [],
            "2": ["--rules"],
            "3": ["--rules=All"]
        }
        
        return rules_map.get(choice, ["--rules"])
    
    def crack_with_part(self, part_file, part_num, rules):
        """Run John on a specific wordlist part"""
        pot_file = os.path.join(self.temp_dir, f"john_part{part_num}.pot")
        
        cmd = [
            self.john_path,
            self.hash_file,
            "--wordlist=" + part_file,
            "--pot=" + pot_file,
            "--session=split_part" + str(part_num)
        ]
        
        # Add format if auto-detected
        if self.hash_format:
            cmd.append(self.hash_format)
        
        # Add rules
        cmd.extend(rules)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if os.path.exists(pot_file):
                with open(pot_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        for line in content.split('\n'):
                            if ':' in line:
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    password = parts[1]
                                    if password and not password.startswith('$'):
                                        with self.lock:
                                            if not self.stop_flag.is_set():
                                                self.cracked_password = password
                                                self.stop_flag.set()
                                        return True
            
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            pass
        
        return False
    
    def run_parallel_crack(self, rules):
        """Run multiple John instances in parallel"""
        print()
        print(BLUE + "______________________ " + GREEN + "Starting Parallel Attack" + BLUE + " _________________")
        print()
        print(tag_asterisk() + f"Running " + YELLOW + f"{len(self.wordlist_parts)}" + RESET + " parallel John instances...")
        print(tag_asterisk() + "Press " + RED + "Ctrl+C" + RESET + " to stop all instances")
        print()
        
        start_time = time.time()
        
        threads = []
        for idx, part_file in enumerate(self.wordlist_parts):
            thread = threading.Thread(
                target=self.crack_with_part,
                args=(part_file, idx + 1, rules),
                name=f"Part-{idx + 1}"
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.2)
        
        try:
            while any(thread.is_alive() for thread in threads):
                if self.stop_flag.is_set():
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            self.show_error("Stopping all cracking threads...")
            self.stop_flag.set()
        
        for thread in threads:
            thread.join(timeout=5)
        
        elapsed = time.time() - start_time
        print()
        print(tag_minus() + f"All threads completed in " + YELLOW + f"{elapsed:.1f} seconds" + RESET)
        
        return self.cracked_password is not None
    
    def display_results(self):
        """Display cracking results"""
        print()
        
        if self.cracked_password:
            print(BLUE + "_________________________________________________________________")
            print()
            print(tag_minus() + "Cracked Password Results: " + GREEN + f"{self.cracked_password}" + RESET)
            print()
            print(BLUE + "_________________________________________________________________")
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"cracked_{timestamp}.txt"
            
            with open(filename, "w") as outfile:
                outfile.write(f"{self.cracked_password}\n")
                
                for part_num in range(1, len(self.wordlist_parts) + 1):
                    pot_file = os.path.join(self.temp_dir, f"john_part{part_num}.pot")
                    if os.path.exists(pot_file):
                        with open(pot_file, 'r') as infile:
                            outfile.write(infile.read())
            
            print()
            print(tag_plus() + f" Results saved to: {filename}")
            print()
            print(BLUE + "_________________________________________________________________")
            print()
        else:
            print(BLUE + "_________________________________________________________________")
            print()
            print(tag_x() + "Password not found in wordlist")
            print()
            print(BLUE + "_________________________________________________________________")
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                self.wordlist_parts = []
            except:
                pass
    
    def run(self):
        """Main execution function"""
        if not self.check_tools():
            return
        
        # Get hash from user
        if not self.get_hash_input():
            return
        
        # Get wordlist
        wordlist_path = self.get_wordlist()
        if not wordlist_path:
            self.cleanup()
            return
        
        # Count words
        total_words = self.count_words(wordlist_path)
        if total_words == 0:
            self.show_error("Wordlist is empty")
            self.cleanup()
            return
        
        print()
        self.show_info(f"Wordlist: " + YELLOW + f"{os.path.basename(wordlist_path)}" + RESET + " (" + CYAN + f"{total_words:,} words" + RESET + ")")
        
        # Get split configuration
        num_parts = self.get_split_count(total_words)
        if not num_parts:
            self.cleanup()
            return
        
        # Split wordlist
        if not self.split_wordlist(wordlist_path, num_parts):
            self.cleanup()
            return
        
        # Select rules
        rules = self.select_rules()
        
        # Run parallel cracking
        password_found = self.run_parallel_crack(rules)
        
        # Display results
        self.display_results()
        
        # Cleanup
        self.cleanup()

def main():
    """Main function"""
    try:
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass
        
        splitter = WordlistSplitter()
        splitter.run()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
