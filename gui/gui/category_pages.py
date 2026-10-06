# gui/category_pages.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from gui.card_grid import CardGrid
from gui.search_registry import register_options

import os
import sys

CATEGORY_DESCRIPTIONS = {
    "Symmetric": "Symmetric-key algorithms use the same cryptographic keys for both encryption of plaintext and decryption of ciphertext.",
    "Asymmetric": "Asymmetric cryptography uses pairs of keys: a public key for encryption and a private key for decryption, enabling secure communication without sharing secret keys beforehand.",
    "Hashing": "A hashing algorithm transforms input data of any size into a fixed-length string of characters called a hash value or message digest.",
    "Advanced": "Advanced password security tools for users and organizations to test system security by auditing weak passwords on user accounts, protected files, and network credentials.",
    "CTF": "Capture the Flag (CTF) is a popular cybersecurity competition where individuals or teams solve security puzzles, exploit vulnerabilities, and capture flags to earn points.",
    "Caesar Cipher": "A substitution cipher where each letter of the plaintext is shifted by a fixed number.",
    "Steganography": "Steganography is the practice of concealing messages or information within other non-secret data, such as images or audio files, using tools like steghide.", 
}

class CategoryPage(QWidget):
    """Modern category page with responsive grid cards matching landing page style."""
    
    def __init__(self, theme_manager, title, options, back_callback, on_option_clicked=None):
        super().__init__()
        self.theme = theme_manager
        self.title = title
        self.back_callback = back_callback
        self.options = options
        self.on_option_clicked = on_option_clicked
        self.card_grid = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setSpacing(20)
    
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        header.addWidget(back_btn)
        header.addStretch()
    
        title_lbl = QLabel(self.title)
        title_lbl.setObjectName("pageTitle")
    
        desc_text = CATEGORY_DESCRIPTIONS.get(self.title, "Select an operation from the options below")
        desc_lbl = QLabel(desc_text)
        desc_lbl.setObjectName("pageSubtitle")
        desc_lbl.setWordWrap(True)
    
        separator = QFrame()
        separator.setObjectName("separator")

        layout.addLayout(header)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addWidget(separator)

        if self.options:
            card_data = [(name, self._get_description(name)) for name, _ in self.options]
            self.card_grid = CardGrid()
            self.card_grid.add_cards(card_data, self.theme, self._on_card_clicked)
            layout.addWidget(self.card_grid)
    
    def _get_description(self, name):
        """Get description for a card by name."""
        desc_map = {
            "Hash Reverse": "Reverse any hash using John the Ripper with 100+ format support",
            "Online Hash Reverse": "Reverse hashes instantly using md5decrypt.net online database",
            "MD5 Hash": "Generate and reverse MD5 hashes with wordlist splitting",
            "SHA Hash": "Generate and reverse SHA-1, SHA-224, SHA-256, SHA-384, and SHA-512",
            "Verify File Integrity": "Compute file hash and compare with expected value to verify downloads",
            "Caesar Cipher": "A substitution cipher where each letter of the plaintext is shifted by a fixed number",
            "Wi-Fi": "Crack WPA/WPA2 handshake passwords using John the Ripper",
            "Rivest Shamir Adleman (RSA)": "Public-key encryption using a public key for encryption and a private key for decryption",
            "Diffie Hellman": "Key exchange protocol allowing two parties to establish a shared secret over an insecure channel",
            "Steganography": "Hide and extract data within images and audio files using steghide with brute force capabilities",
            "RSA": "RSA cryptographic challenges commonly found in CTF competitions",
            "Transposition Cipher": "A transposition cipher rearranges the letters of the plaintext.",
            "Documents": "Crack password-protected ZIP, RAR, PDF and Office files using brute force and wordlist attacks",
            "Operating Systems": "Audit and crack operating system user account passwords",
            "Base Encoding": "Encode and decode using Base2 through Base100 formats",
            "Morse Code": "Encode, decode, and analyze Morse code signals",
            "Text Translator": "Encode text to Morse code and decode Morse code back to text",
            "Audio Tools": "Generate Morse code audio, play back, and decode from audio files",
            "Substitution Cipher": "Encrypt and decrypt using custom substitution alphabets with frequency analysis",
            "Diffie-Hellman": "Diffie-Hellman key exchange attacks including small subgroup, Pohlig-Hellman, and MITM",
            "Zlib Compression": "Compress data with configurable levels and decompress Zlib (RFC 1950) data from hex or files", 
            "Zlib Compress": "Compress data using Zlib with configurable compression levels (1-9)", 
            "Zlib Decompress": "Decompress Zlib data from hex input or load from files with auto-detection",  
            "ADFGVX Cipher": "WWI-era German cipher using ADFGVX Polybius square with columnar transposition",
            "ADFGVX Encrypt": "Encrypt plaintext using ADFGVX/ADFGX cipher with keyword transposition",
            "ADFGVX Decrypt": "Decrypt ADFGVX/ADFGX ciphertext with auto-detection of grid type",
            "Symbols Ciphers": "Decode symbol-based ciphers: Braille, Pigpen, Runes, Wingdings, and more",
            "Atbash Cipher": "Simple substitution cipher where alphabet is reversed (A↔Z, B↔Y)",
            "Atbash Encrypt": "Encrypt plaintext using Atbash reverse alphabet substitution",
            "Atbash Decrypt": "Decrypt Atbash ciphertext back to plaintext (self-inverse)",
            "XOR Cipher": "XOR encryption/decryption tools including single-byte brute force",
            "Single-byte XOR": "Brute-force decrypt single-byte XOR ciphertext with English frequency scoring",
            "Multi-byte XOR": "Brute-force decrypt repeating multi-byte XOR ciphertext",
            "Pigpen Cipher": "Encode and decode using the Masonic/Freemason's Pigpen cipher",
            "Pigpen Encrypt": "Encrypt plaintext to Pigpen cipher symbols with export options",
            "Pigpen Decrypt": "Decrypt Pigpen cipher symbols by uploading an image and clicking symbols",
            "OpenSSL": "OpenSSL command-line utilities for cryptography, certificates, and secure communications",
            "AES": "Advanced Encryption Standard with ECB/CBC/CFB/OFB/CTR modes and 128/192/256-bit keys",
        }
        return desc_map.get(name, "")
    
    def _on_card_clicked(self, name):
        """Handle card click."""
        for opt_name, opt_callback in self.options:
            if opt_name == name:
                if opt_callback and callable(opt_callback):
                    opt_callback()
                elif self.on_option_clicked:
                    self.on_option_clicked(name)
                return
    
    def refresh_theme(self):
        """Re-apply theme to all cards."""
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)


# Register at module level
register_options("Symmetric", [
    ("Caesar Cipher", "A substitution cipher where each letter of the plaintext is shifted by a fixed number"),
    ("Transposition Cipher", "A transposition cipher rearranges the letters of the plaintext"),
])

register_options("Asymmetric", [
    ("Rivest Shamir Adleman (RSA)", "Public-key encryption using a public key for encryption and a private key for decryption"),
    ("Diffie Hellman", "Key exchange protocol allowing two parties to establish a shared secret over an insecure channel"),
])

register_options("Hashing", [
    ("Hash Reverse", "Reverse any hash using John the Ripper with 100+ format support"),
    ("Online Hash Reverse", "Reverse hashes using md5decrypt.net online database"),
    ("MD5 Hash", "Generate and reverse MD5 hashes with wordlist splitting"),
    ("SHA Hash", "Generate and reverse SHA-1, SHA-224, SHA-256, SHA-384, and SHA-512"),
    ("Verify File Integrity", "Compute file hash and compare with expected value to verify downloads"),
])

register_options("CTF", [
    ("RSA", "RSA cryptographic challenges commonly found in CTF competitions"),
    ("Diffie-Hellman", "Diffie-Hellman key exchange attacks including small subgroup, Pohlig-Hellman, and MITM"),
    ("AES", "Advanced Encryption Standard with ECB/CBC/CFB/OFB/CTR modes and 128/192/256-bit keys"), 
    ("Steganography", "Hide and extract data within images and audio files using steghide with brute force capabilities"),
    ("Base Encoding", "Encode and decode using Base2 through Base100 formats"),
    ("Morse Code", "Encode, decode, and analyze Morse code signals"),
    ("Substitution Cipher", "Encrypt and decrypt using custom substitution alphabets with frequency analysis"),
    ("Atbash Cipher", "Simple substitution cipher where alphabet is reversed"),
    ("Zlib Compression", "Compress and decompress data using Zlib (RFC 1950)"),
    ("ADFGVX Cipher", "WWI-era German cipher using ADFGVX Polybius square with transposition"),
    ("Symbols Ciphers", "Decode symbol-based ciphers: Braille, Pigpen, Runes, Wingdings, and more"),
])

register_options("Advanced", [
    ("Wi-Fi", "Crack WPA/WPA2 handshake passwords using John the Ripper"),
    ("Documents", "Crack password-protected ZIP, RAR, PDF and Office files using brute force and wordlist attacks"),
    ("Operating Systems", "Audit and crack operating system user account passwords"),
    ("OpenSSL", "OpenSSL command-line utilities for cryptography, certificates, and secure communications"),
])


def get_symmetric_options():
    return [
        ("Caesar Cipher", None),
        ("Transposition Cipher", None),
    ]

def get_asymmetric_options():
    return [
        ("Rivest Shamir Adleman (RSA)", None),
        ("Diffie Hellman", None),
    ]

def get_hashing_options():
    return [
        ("Hash Reverse", None),
        ("Online Hash Reverse", None),
        ("MD5 Hash", None),
        ("SHA Hash", None),
        ("Verify File Integrity", None),
    ]

def get_ctf_options():
    return [
        ("RSA", None),
        ("AES", None),
        ("Diffie-Hellman", None),
        ("Steganography", None),
        ("Base Encoding", None),
        ("Morse Code", None),
        ("Substitution Cipher", None),
        ("Atbash Cipher", None),
        ("Zlib Compression", None),
        ("ADFGVX Cipher", None),
        ("Symbols Ciphers", None),
    ]

def get_advanced_options():
    return [
        ("Wi-Fi", None),
        ("Documents", None),
        ("Operating Systems", None),
        ("OpenSSL", None),
    ]