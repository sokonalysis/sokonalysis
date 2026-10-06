# gui/main_window.py
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QStatusBar, QLabel, QMessageBox, QToolBar, QToolButton, QMenu
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PySide6.QtCore import Qt, QSize, QTimer
import os
import sys
import platform

from gui.landing_page import LandingPage
from gui.category_pages import (
    CategoryPage, get_symmetric_options, get_asymmetric_options,
    get_hashing_options, get_ctf_options, get_advanced_options
)

from gui.hashing_page import HashingPage
from gui.online_hash_reverse import OnlineHashReversePage
from gui.md5_page import MD5Page
from gui.md5_generate import MD5GeneratePage
from gui.md5_reverse import MD5ReversePage
from gui.verify_hash_page import VerifyHashPage

from gui.config_page import ConfigPage
from gui.sha_page import SHAPage
from gui.sha_generate import SHAGeneratePage
from gui.sha_reverse import SHAReversePage

from gui.wifi_page import WiFiPage
from gui.wifi_capture_page import WiFiCapturePage

from gui.john_config_page import JohnConfigPage

from gui.caesar_page import CaesarPage
from gui.caesar_bruteforce import CaesarBruteForcePage
from gui.caesar_basic import CaesarBasicPage
from gui.caesar_poly_page import CaesarPolyPage
from gui.caesar_polyalphabetic import CaesarPolyalphabeticPage
from gui.caesar_vigenere_page import CaesarVigenerePage
from gui.caesar_kasiski import CaesarKasiskiPage
from gui.caesar_friedman import CaesarFriedmanPage
from gui.caesar_sequence import CaesarSequencePage

from gui.transposition_page import TranspositionPage
from gui.transposition_basic import TranspositionBasicPage
from gui.transposition_columnar import TranspositionColumnarPage
from gui.transposition_railfence import TranspositionRailFencePage

from gui.rsa_page import RSAPage
from gui.rsa_basic import RSABasicPage

from gui.diffie_hellman_page import DiffieHellmanPage
from gui.diffie_hellman_basic import DiffieHellmanBasicPage
from gui.diffie_hellman_mitm import DiffieHellmanMITMPage

from gui.ctf_rsa_page import CTFRSAPage
from gui.ctf_rsa_factordb import CTF_RSA_FactorDBPage
from gui.ctf_rsa_standard import CTF_RSA_StandardPage
from gui.ctf_rsa_multiprime import CTF_RSA_MultiPrimePage
from gui.ctf_rsa_fermat import CTF_RSA_FermatPage
from gui.ctf_rsa_common_modulus import CTF_RSA_CommonModulusPage
from gui.ctf_rsa_factor_decrypt import CTF_RSA_FactorDecryptPage
from gui.ctf_rsa_enc_decrypt import CTF_RSA_EncDecryptPage
from gui.ctf_rsa_low_exponent import CTF_RSA_LowExponentPage
from gui.ctf_rsa_franklin_reiter import CTF_RSA_FranklinReiterPage
from gui.ctf_rsa_coppersmith import CTF_RSA_CoppersmithPage
from gui.ctf_rsa_certificate_decoder_page import CTFRSACertificateDecoderPage

from gui.ctf_aes_page import CTFAesPage
from gui.ctf_aes_ecb_page import CTFAesECBPage
from gui.ctf_aes_ecb_decrypt import CTF_AES_ECB_DecryptPage

from gui.ctf_diffie_hellman_page import CTFDiffieHellmanPage
from gui.ctf_dh_encrypt import CTF_DH_EncryptPage
from gui.ctf_dh_small_numbers import CTF_DH_SmallNumbersPage

from gui.crack_files_page import CrackFilesPage

from gui.caesar_hybrid import CaesarHybridPage

from gui.steganography_page import SteganographyPage
from gui.steganography_embed import SteganographyEmbedPage
from gui.steganography_extract import SteganographyExtractPage
from gui.stego_visual_crypto_page import StegoVisualCryptoPage
from gui.stego_visual_crypto_encrypt import StegoVisualCryptoEncryptPage
from gui.stego_visual_crypto_decrypt import StegoVisualCryptoDecryptPage

from gui.wifi_options_page import WiFiOptionsPage

from gui.documents_page import DocumentsPage
from gui.crack_zip_page import CrackZipPage
from gui.crack_rar_page import CrackRarPage
from gui.crack_pdf_page import CrackPdfPage
from gui.crack_office_page import CrackOfficePage
from gui.crack_7z_page import Crack7zPage

from gui.linux_options_page import LinuxOptionsPage
from gui.linux_passwd_shadow import LinuxPasswdShadowPage
from gui.linux_live_system import LiveSystemPage

from gui.windows_options_page import WindowsOptionsPage
from gui.windows_sam_system import WindowsSAMSystemPage

from gui.openssl_page import OpenSSLPage
from gui.openssl_generate_rsa import OpenSSLGenerateRSAPage
from gui.openssl_generate_ec import OpenSSLGenerateECPage
from gui.openssl_certificate_management import OpenSSLCertificateManagementPage
from gui.openssl_encrypt_decrypt import OpenSSLEncryptDecryptPage

from gui.user_guide_page import UserGuidePage

from gui.license_page import LicensePage

from gui.ctf_base_page import CTFBasePage
from gui.base2_page import Base2Page
from gui.base16_page import Base16Page
from gui.base32_page import Base32Page
from gui.base36_page import Base36Page
from gui.base45_page import Base45Page
from gui.base58_page import Base58Page
from gui.base62_page import Base62Page
from gui.base64_page import Base64Page
from gui.base85_page import Base85Page
from gui.base91_page import Base91Page
from gui.base92_page import Base92Page
from gui.base100_page import Base100Page

from gui.search_page import SearchPage

from gui.about_page import AboutDialog

from gui.updater import check_for_updates

from gui.morse_code_page import MorseCodePage
from gui.morse_text_page import MorseTextPage
from gui.morse_audio_page import MorseAudioPage

from gui.substitution_page import SubstitutionPage
from gui.substitution_decrypt_key import SubstitutionDecryptKeyPage
from gui.substitution_encrypt_key import SubstitutionEncryptKeyPage
from gui.substitution_frequency import SubstitutionFrequencyPage

from gui.zlib_page import ZlibPage
from gui.zlib_compression_page import ZlibCompressionPage
from gui.zlib_decompression_page import ZlibDecompressionPage

from gui.adfgvx_page import ADFGVXPage
from gui.adfgvx_decrypt import ADFGVXDecryptPage
from gui.adfgvx_encrypt import ADFGVXEncryptPage

from gui.ctf_symbols_page import CTFSymbolsPage
from gui.ctf_pigpen_page import CTFPigpenPage
from gui.ctf_pigpen_encrypt import PigpenEncryptPage
from gui.ctf_pigpen_decrypt import PigpenDecryptPage
from gui.ctf_navy_page import CTFNavyPage
from gui.ctf_navy_encrypt import NavyEncryptPage
from gui.ctf_navy_decrypt import NavyDecryptPage

from gui.ctf_atbash_page import CTFAtbashPage
from gui.ctf_atbash_encrypt import AtbashEncryptPage
from gui.ctf_atbash_decrypt import AtbashDecryptPage

from gui.json_config_page import JsonConfigPage
from gui.layout_manager import layout_manager
from gui.search_registry import get_all_options
from gui.utils import get_version, get_os_info
from gui.header import HeaderToolbar
from gui.footer import Footer
from gui.user_preferences import user_prefs


class MainWindow(QMainWindow):
    """Professional main application window."""
    
    def __init__(self, theme_manager):
        super().__init__()
        self.theme = theme_manager
        self.setWindowTitle("sokonalysis")
    
        # ===== Use layout manager for sizing =====
        from gui.layout_manager import layout_manager
    
        # Get window size and position
        saved_geom = user_prefs.window_geometry
        if saved_geom:
            try:
                x, y, w, h = saved_geom
                self.setGeometry(x, y, w, h)
            except:
                width, height = layout_manager.get_window_size()
                x, y = layout_manager.get_window_position()
                self.setGeometry(x, y, width, height)
        else:
            width, height = layout_manager.get_window_size()
            x, y = layout_manager.get_window_position()
            self.setGeometry(x, y, width, height)
    
    
        # Set minimum size
        min_w, min_h = layout_manager.get_minimum_size()
        self.setMinimumSize(min_w, min_h)
        # ===== END =====
    
        self.current_layout = "default"
        
        icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'logo.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.landing_page = LandingPage(theme_manager, self._show_category)
        self.landing_page.search_requested.connect(self._handle_search)
        self.stack.addWidget(self.landing_page)
        self.category_pages = {}
        self.shared_wordlist_path = user_prefs.wordlist_path
        self.shared_split_parts = user_prefs.split_parts
        self.shared_json_path = user_prefs.json_path
        
        # ===== CREATE HEADER =====
        self.header = HeaderToolbar(self, theme_manager)
        area_map = {
            "left": Qt.ToolBarArea.LeftToolBarArea,
            "right": Qt.ToolBarArea.RightToolBarArea,
        }
        saved_area = user_prefs.last_toolbar_area
        self.addToolBar(area_map.get(saved_area, Qt.ToolBarArea.LeftToolBarArea), self.header.get_toolbar())
        # ===== END HEADER =====
        
        # ===== CREATE FOOTER =====
        self.footer = Footer(self, theme_manager)
        self.setStatusBar(self.footer.get_status_bar())
        # ===== END FOOTER =====
        
        self._apply_theme()
        self.theme.theme_changed.connect(self._on_theme_changed)
        if user_prefs.theme == "light" and self.theme.is_dark:
            QTimer.singleShot(300, lambda: self._toggle_theme())
        elif user_prefs.theme == "dark" and not self.theme.is_dark:
            QTimer.singleShot(300, lambda: self._toggle_theme())

        saved_layout = user_prefs.layout

        if saved_layout != "default":
            QTimer.singleShot(100, lambda: self._apply_layout(saved_layout))

        if user_prefs.window_maximized:
            QTimer.singleShot(200, lambda: self.showMaximized())

    def changeEvent(self, event):
        """Detect window state changes and apply layouts."""
        if event.type() == event.Type.WindowStateChange:
            if self.isMaximized():
                if self.current_layout != "wide":
                    self._apply_layout("wide")
            else:
                if self.current_layout == "wide":
                    self._apply_layout("compact")
        super().changeEvent(event)

    def closeEvent(self, event):
        geo = self.geometry()
        user_prefs.set_window_geometry((geo.x(), geo.y(), geo.width(), geo.height()))
        user_prefs.set_window_maximized(self.isMaximized())
        user_prefs.set_layout(self.current_layout)
        super().closeEvent(event)

    def _handle_search(self, query):
        page_key = "search"
        if page_key in self.category_pages:
            self.stack.removeWidget(self.category_pages[page_key])
            self.category_pages[page_key].deleteLater()
            del self.category_pages[page_key]
    
        all_options = get_all_options()
        page = SearchPage(self.theme, all_options, lambda: self._show_landing())
        page.option_selected.connect(self._on_category_option_clicked)
        self.category_pages[page_key] = page
        self.stack.addWidget(page)
    
        self.stack.setCurrentWidget(page)
        page.search_input.setText(query)
        page._on_search(query)
    
        self.stack.setCurrentWidget(self.category_pages[page_key])
        # Pre-fill search
        self.category_pages[page_key].search_input.setText(query)
        self.category_pages[page_key]._on_search(query)
    
    def _apply_layout(self, layout_type):
        """Apply different layout styles."""
        from gui.layout_manager import layout_manager
    
        layout_manager.set_layout(layout_type)
        self.current_layout = layout_type
    
        if layout_type == "wide":
            self.showMaximized()
        else:
            if self.isMaximized():
                self.showNormal()
        
            # Get window size and position from layout manager
            width, height = layout_manager.get_window_size()
            x, y = layout_manager.get_window_position()
            self.setGeometry(x, y, width, height)
        
            # Update minimum size
            min_w, min_h = layout_manager.get_minimum_size()
            self.setMinimumSize(min_w, min_h)
    
        self.footer.update_version_text()
    
        # Refresh current page
        current = self.stack.currentWidget()
        if hasattr(current, 'refresh_theme'):
            current.refresh_theme()
        
        # Refresh current page to update font sizes
        current = self.stack.currentWidget()
        if hasattr(current, 'refresh_theme'):
            current.refresh_theme()
    
    
    def _toggle_theme(self):
        self.theme.toggle()
        self.header.update_theme_action_text(self.theme.is_dark)
        user_prefs.set_theme("dark" if self.theme.is_dark else "light")
    
    def _on_theme_changed(self, theme_name):
        self._apply_theme()
    
    def _apply_theme(self):
        self.setStyleSheet(self.theme.stylesheet())
        self.header.update_style()
        self.footer.update_style()

        saved_layout = self.current_layout
        layout_manager.set_layout(saved_layout)
        
        # Refresh landing page
        if hasattr(self.landing_page, 'refresh_theme'):
            self.landing_page.refresh_theme()
        # Refresh current page
        current = self.stack.currentWidget()
        if hasattr(current, 'refresh_theme'):
            current.refresh_theme()
        # Force refresh ALL cached pages
        for key, page in self.category_pages.items():
            if hasattr(page, 'refresh_theme'):
                page.refresh_theme()
    
    def _show_category(self, category_name):
        if category_name not in self.category_pages:
            options_map = {
                "Symmetric": get_symmetric_options(),
                "Asymmetric": get_asymmetric_options(),
                "Hashing": get_hashing_options(),
                "CTF": get_ctf_options(),
                "Advanced": get_advanced_options(),
            }
            
            page = CategoryPage(
                self.theme,
                category_name,
                options_map.get(category_name, []),
                self._show_landing,
                on_option_clicked=self._on_category_option_clicked if category_name in ["Hashing", "Advanced", "Symmetric", "Asymmetric", "CTF"] else None
            )
            self.category_pages[category_name] = page
            self.stack.addWidget(page)
        
        self.stack.setCurrentWidget(self.category_pages[category_name])
    
    def _on_category_option_clicked(self, option_name):

        LandingPage.record_activity(option_name)

        if option_name == "Caesar Cipher":
            self._show_caesar_page()

        elif option_name == "Hash Reverse":
            self._show_hashing_detail()
        elif option_name == "Online Hash Reverse":
            self._show_online_hash_reverse()
        elif option_name == "MD5 Hash":
            self._show_md5_page()
        elif option_name == "MD5 Generate":
            self._show_md5_generate()
        elif option_name == "MD5 Reverse":
            self._show_md5_reverse()
        elif option_name == "SHA Hash":
            self._show_sha_page()
        elif option_name == "SHA Generate":
            self._show_sha_generate()
        elif option_name == "SHA Reverse":
            self._show_sha_reverse()
        elif option_name == "Verify File Integrity":
            self._show_verify_hash_page()

        elif option_name == "Wi-Fi":
            self._show_wifi_options_page()
        elif option_name == "Handshake Capture":
            self._show_wifi_capture_page()
        elif option_name == "Handshake Cracking":
            self._show_wifi_page()

        elif option_name == "Brute Force Decrypt":
            self._show_caesar_bruteforce()
        elif option_name == "Basic Shift":
            self._show_caesar_basic()
        elif option_name == "Polyalphabetic":
            self._show_caesar_poly_page()
        elif option_name == "Keyword-based":
            self._show_caesar_polyalphabetic()
        elif option_name == "Vigenère":
            self._show_caesar_vigenere_page()
        elif option_name == "Kasiski Examination":
            self._show_caesar_kasiski()
        elif option_name == "Friedman Test":
            self._show_caesar_friedman()
        elif option_name == "Sequence-based":
            self._show_caesar_sequence()
        elif option_name == "Transposition Cipher":
            self._show_transposition_page()
        elif option_name == "Basic Transposition":
            self._show_transposition_basic()
        elif option_name == "Columnar Transposition":
            self._show_transposition_columnar()
        elif option_name == "Rail Fence":
            self._show_transposition_railfence()

        elif option_name == "Rivest Shamir Adleman (RSA)":
            self._show_rsa_page()
        elif option_name == "Basic RSA":
            self._show_rsa_basic()
        elif option_name == "Diffie Hellman":
            self._show_diffie_hellman_page()
        elif option_name == "Basic Operation":
            self._show_diffie_hellman_basic()
        elif option_name == "MITM Attack":
            self._show_diffie_hellman_mitm()

        elif option_name == "RSA":
            self._show_ctf_rsa_page()
        elif option_name == "FactorDB":
            self._show_ctf_rsa_factordb()
        elif option_name == "Standard RSA":
            self._show_ctf_rsa_standard()
        elif option_name == "Factor & Decrypt":
            self._show_ctf_rsa_factor_decrypt()
        elif option_name == "Decrypt .enc":
            self._show_ctf_rsa_enc_decrypt()
        elif option_name == "Low Exponent":
            self._show_ctf_rsa_low_exponent()
        elif option_name == "Multi-Prime":
            self._show_ctf_rsa_multiprime()
        elif option_name == "Franklin-Reiter":
            self._show_franklin_reiter()
        elif option_name == "Fermat's Factorization":
            self._show_ctf_rsa_fermat()
        elif option_name == "Common Modulus":
            self._show_ctf_rsa_common_modulus()
        elif option_name == "Coppersmith's Attack":
            self._show_ctf_rsa_coppersmith()
        elif option_name == "Certificate Decoder":
            self._show_ctf_rsa_certificate_decoder()


        elif option_name == "AES":
            self._show_ctf_aes_page()

        elif option_name == "ECB":
            self._show_ctf_aes_ecb()
        elif option_name == "Manual Decrypt":
            self._show_ctf_aes_ecb_decrypt()
       
        elif option_name == "CBC":
            self._show_ctf_aes_cbc()
        elif option_name == "CFB":
            self._show_ctf_aes_cfb()
        elif option_name == "OFB":
            self._show_ctf_aes_ofb()
        elif option_name == "CTR":
            self._show_ctf_aes_ctr()


        elif option_name == "Diffie-Hellman":
            self._show_ctf_diffie_hellman()
        elif option_name == "Encrypt Message":
            self._show_ctf_dh_encrypt()
        elif option_name == "Small Numbers":
            self._show_ctf_dh_small_numbers()

        elif option_name == "Documents":
            self._show_documents_page()
        elif option_name == "Crack Protected Files":
            self._show_documents_page()
        elif option_name == "Zip File":
            self._show_crack_zip_page()
        elif option_name == "Rar File":
            self._show_crack_rar_page()
        elif option_name == "PDF File":
            self._show_crack_pdf_page()
        elif option_name == "Office Document":
            self._show_crack_office_page()
        elif option_name == "Hybrid Approach":
            self._show_caesar_hybrid()
        elif option_name == "7z File":
            self._show_crack_7z_page()

        elif option_name == "OpenSSL":
            self._show_openssl_page()
        elif option_name == "Generate RSA Key":
            self._show_openssl_generate_rsa()
        elif option_name == "Generate EC Key":
            self._show_openssl_generate_ec()
        elif option_name == "Certificate Management":
            self._show_openssl_certificate_management()
        elif option_name == "Encrypt/Decrypt":
            self._show_openssl_encrypt_decrypt()

        elif option_name == "Steganography":
            self._show_steganography_page()
        elif option_name == "Embed Data":
            self._show_steganography_embed()
        elif option_name == "Extract Data":
            self._show_steganography_extract()
        elif option_name == "Visual Cryptography":
            self._show_visual_crypto()
        elif option_name == "Encrypt Image":
            self._show_visual_crypto_encrypt()
        elif option_name == "Decrypt Image":
            self._show_visual_crypto_decrypt()

        elif option_name == "Operating Systems":
            self._show_os_page()
        elif option_name == "Linux":
            self._show_linux_options_page()
        elif option_name == "Password Cracking":
            self._show_linux_password_cracking_page()
        elif option_name == "passwd & shadow":
            self._show_linux_passwd_shadow_page()
        elif option_name == "Live System":
            self._show_live_system_page()

        elif option_name == "Windows":
            self._show_windows_options_page()
        elif option_name == "SAM & SYSTEM":
            self._show_windows_sam_system_page()

        elif option_name == "Base Encoding":
            self._show_ctf_base_page()
        elif option_name == "Base2":
            self._show_base2_page()
        elif option_name == "Base16":
            self._show_base16_page()
        elif option_name == "Base32":
            self._show_base32_page()
        elif option_name == "Base36":
            self._show_base36_page()
        elif option_name == "Base45":
            self._show_base45_page()
        elif option_name == "Base58":
            self._show_base58_page()
        elif option_name == "Base62":
            self._show_base62_page()
        elif option_name == "Base64":
            self._show_base64_page()
        elif option_name == "Base85":
            self._show_base85_page()
        elif option_name == "Base91":
            self._show_base91_page()
        elif option_name == "Base92":
            self._show_base92_page()
        elif option_name == "Base💯":
            self._show_base100_page()

        elif option_name == "Morse Code":
            self._show_morse_code_page()
        elif option_name == "Text Translator":
            self._show_morse_text_page()
        elif option_name == "Audio Tools":
            self._show_morse_audio_page()

        elif option_name == "Substitution Cipher":
            self._show_substitution_page()
        elif option_name == "Decrypt with Known Key":
            self._show_substitution_decrypt_key()
        elif option_name == "Encrypt with Known Key":
            self._show_substitution_encrypt_key()
        elif option_name == "Frequency Analysis":
            self._show_substitution_frequency()

        elif option_name == "Zlib Compression":
            self._show_zlib_page()
        elif option_name == "Zlib Compress":
            self._show_zlib_compression()
        elif option_name == "Zlib Decompress":
             self._show_zlib_decompression()

        elif option_name == "ADFGVX Cipher":
            self._show_adfgvx_page()
        elif option_name == "ADFGVX Encrypt":
            self._show_adfgvx_encrypt()
        elif option_name == "ADFGVX Decrypt":
            self._show_adfgvx_decrypt()

        elif option_name == "Symbols Ciphers":
            self._show_ctf_symbols_page()
        elif option_name == "Pigpen Cipher":
            self._show_ctf_pigpen_page()
        elif option_name == "Pigpen Encrypt":
            self._show_ctf_pigpen_encrypt()
        elif option_name == "Pigpen Decrypt":
            self._show_ctf_pigpen_decrypt()
        elif option_name == "Navy Signals Code":
            self._show_ctf_navy_page()
        elif option_name == "Navy Encrypt":
            self._show_ctf_navy_encrypt()
        elif option_name == "Navy Decrypt":
            self._show_ctf_navy_decrypt()

        elif option_name == "Atbash Cipher":
            self._show_ctf_atbash_page()
        elif option_name == "Atbash Encrypt":
            self._show_ctf_atbash_encrypt()
        elif option_name == "Atbash Decrypt":
            self._show_ctf_atbash_decrypt()




    
    def _show_hashing_detail(self):
        page_key = "hashing_detail"
        if page_key not in self.category_pages:
            page = HashingPage(
                self.theme,
                lambda: self._show_category("Hashing"),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(
                self.shared_wordlist_path, self.shared_split_parts
            )
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_online_hash_reverse(self):
        page_key = "online_hash_reverse"
        if page_key not in self.category_pages:
            page = OnlineHashReversePage(self.theme, lambda: self._show_category("Hashing"))
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])
    
    def _show_md5_page(self):
        page_key = "md5_page"
        if page_key not in self.category_pages:
            page = MD5Page(self.theme, lambda: self._show_category("Hashing"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_md5_generate(self):
        page_key = "md5_generate"
        if page_key not in self.category_pages:
            page = MD5GeneratePage(self.theme, lambda: self._show_md5_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_md5_reverse(self):
        page_key = "md5_reverse"
        if page_key not in self.category_pages:
            page = MD5ReversePage(
                self.theme,
                lambda: self._show_md5_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
        self.stack.setCurrentWidget(self.category_pages[page_key])
    
    def _show_sha_page(self):
        page_key = "sha_page"
        if page_key not in self.category_pages:
            page = SHAPage(self.theme, lambda: self._show_category("Hashing"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_sha_generate(self):
        page_key = "sha_generate"
        if page_key not in self.category_pages:
            page = SHAGeneratePage(self.theme, lambda: self._show_sha_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_sha_reverse(self):
        page_key = "sha_reverse"
        if page_key not in self.category_pages:
            page = SHAReversePage(
                self.theme,
                lambda: self._show_sha_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.stack.setCurrentWidget(self.category_pages[page_key])
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_verify_hash_page(self):
        page_key = "verify_hash_page"
        if page_key not in self.category_pages:
            page = VerifyHashPage(self.theme, lambda: self._show_category("Hashing"))
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])





    def _show_wifi_options_page(self):
        page_key = "wifi_options_page"
        if page_key not in self.category_pages:
            page = WiFiOptionsPage(self.theme, lambda: self._show_category("Advanced"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_wifi_page(self):
        page_key = "wifi_page"
        if page_key not in self.category_pages:
            page = WiFiPage(
                self.theme,
                lambda: self._show_wifi_options_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(
                self.shared_wordlist_path, self.shared_split_parts
            )
            self.category_pages[page_key].back_callback = lambda: self._show_wifi_options_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])





    def _show_wifi_capture_page(self):
        page_key = "wifi_capture_page"
        if page_key not in self.category_pages:
            page = WiFiCapturePage(
                self.theme,
                lambda: self._show_wifi_options_page(),
                handshake_file_callback=self._on_handshake_captured
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].back_callback = lambda: self._show_wifi_options_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _on_handshake_captured(self, handshake_file):
        """Handle captured handshake file - navigate to cracking page with file pre-loaded."""
        self._show_wifi_page()
        if "wifi_page" in self.category_pages:
            wifi_page = self.category_pages["wifi_page"]
            wifi_page.handshake_path = handshake_file
            wifi_page.handshake_path_input.setText(handshake_file)
            wifi_page._update_file_preview(handshake_file)
            wifi_page.start_btn.setEnabled(bool(self.shared_wordlist_path) and wifi_page.john_ok)


    def _show_caesar_page(self):
        page_key = "caesar_page"
        if page_key not in self.category_pages:
            page = CaesarPage(self.theme, lambda: self._show_category("Symmetric"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_bruteforce(self):
        page_key = "caesar_bruteforce"
        if page_key not in self.category_pages:
            page = CaesarBruteForcePage(
                self.theme,
                lambda: self._show_caesar_page(),
                wordlist_path=self.shared_wordlist_path
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(
                self.shared_wordlist_path, self.shared_split_parts
            )
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_basic(self):
        page_key = "caesar_basic"
        if page_key not in self.category_pages:
            page = CaesarBasicPage(self.theme, lambda: self._show_caesar_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_poly_page(self):
        page_key = "caesar_poly_page"
        if page_key not in self.category_pages:
            page = CaesarPolyPage(self.theme, lambda: self._show_caesar_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_polyalphabetic(self):
        page_key = "caesar_polyalphabetic"
        if page_key not in self.category_pages:
            page = CaesarPolyalphabeticPage(self.theme, lambda: self._show_caesar_poly_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_vigenere_page(self):
        page_key = "caesar_vigenere_page"
        if page_key not in self.category_pages:
            page = CaesarVigenerePage(self.theme, lambda: self._show_caesar_poly_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_kasiski(self):
        page_key = "caesar_kasiski"
        if page_key not in self.category_pages:
            page = CaesarKasiskiPage(self.theme, lambda: self._show_caesar_vigenere_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_friedman(self):
        page_key = "caesar_friedman"
        if page_key not in self.category_pages:
            page = CaesarFriedmanPage(self.theme, lambda: self._show_caesar_vigenere_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_caesar_sequence(self):               
        page_key = "caesar_sequence"
        if page_key not in self.category_pages:
            page = CaesarSequencePage(self.theme, lambda: self._show_caesar_poly_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_transposition_page(self):
        page_key = "transposition_page"
        if page_key not in self.category_pages:
            page = TranspositionPage(self.theme, lambda: self._show_category("Symmetric"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_transposition_basic(self):
        page_key = "transposition_basic"
        if page_key not in self.category_pages:
            page = TranspositionBasicPage(self.theme, lambda: self._show_transposition_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_transposition_columnar(self):
        page_key = "transposition_columnar"
        if page_key not in self.category_pages:
            page = TranspositionColumnarPage(self.theme, lambda: self._show_transposition_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_transposition_railfence(self):
        page_key = "transposition_railfence"
        if page_key not in self.category_pages:
            page = TranspositionRailFencePage(self.theme, lambda: self._show_transposition_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_rsa_page(self):
        page_key = "rsa_page"
        if page_key not in self.category_pages:
            page = RSAPage(self.theme, lambda: self._show_category("Asymmetric"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_rsa_basic(self):
        page_key = "rsa_basic"
        if page_key not in self.category_pages:
            page = RSABasicPage(self.theme, lambda: self._show_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_diffie_hellman_page(self):
        page_key = "diffie_hellman_page"
        if page_key not in self.category_pages:
            page = DiffieHellmanPage(self.theme, lambda: self._show_category("Asymmetric"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_diffie_hellman_basic(self):
        page_key = "diffie_hellman_basic"
        if page_key not in self.category_pages:
            page = DiffieHellmanBasicPage(self.theme, lambda: self._show_diffie_hellman_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_diffie_hellman_mitm(self):
        page_key = "diffie_hellman_mitm"
        if page_key not in self.category_pages:
            page = DiffieHellmanMITMPage(self.theme, lambda: self._show_diffie_hellman_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_ctf_rsa_page(self):
        page_key = "ctf_rsa_page"
        if page_key not in self.category_pages:
            page = CTFRSAPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_factordb(self):
        page_key = "ctf_rsa_factordb"
        if page_key not in self.category_pages:
            page = CTF_RSA_FactorDBPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_standard(self):
        page_key = "ctf_rsa_standard"
        if page_key not in self.category_pages:
            page = CTF_RSA_StandardPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_factor_decrypt(self):
        page_key = "ctf_rsa_factor_decrypt"
        if page_key not in self.category_pages:
            page = CTF_RSA_FactorDecryptPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_enc_decrypt(self):
        page_key = "ctf_rsa_enc_decrypt"
        if page_key not in self.category_pages:
            page = CTF_RSA_EncDecryptPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_low_exponent(self):
        page_key = "ctf_rsa_low_exponent"
        if page_key not in self.category_pages:
            page = CTF_RSA_LowExponentPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_multiprime(self):
        page_key = "ctf_rsa_multiprime"
        if page_key not in self.category_pages:
            page = CTF_RSA_MultiPrimePage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_franklin_reiter(self):
        page_key = "franklin_reiter"
        if page_key not in self.category_pages:
            page = CTF_RSA_FranklinReiterPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_fermat(self):
        page_key = "ctf_rsa_fermat"
        if page_key not in self.category_pages:
            page = CTF_RSA_FermatPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_common_modulus(self):
        page_key = "ctf_rsa_common_modulus"
        if page_key not in self.category_pages:
            page = CTF_RSA_CommonModulusPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_rsa_coppersmith(self):
        page_key = "ctf_rsa_coppersmith"
        if page_key not in self.category_pages:
            page = CTF_RSA_CoppersmithPage(self.theme, lambda: self._show_ctf_rsa_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])
    
    def _show_ctf_rsa_certificate_decoder(self):
        page_key = "ctf_rsa_certificate_decoder"
        if page_key not in self.category_pages:
            page = CTFRSACertificateDecoderPage(
                self.theme,
                lambda: self._show_ctf_rsa_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])









    def _show_ctf_aes_page(self):
        page_key = "ctf_aes_page"
        if page_key not in self.category_pages:
            page = CTFAesPage(
                self.theme,
                lambda: self._show_category("CTF"),
                self._on_category_option_clicked
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_aes_ecb(self):
        page_key = "ctf_aes_ecb_page"
        if page_key not in self.category_pages:
            page = CTFAesECBPage(
                self.theme,
                lambda: self._show_ctf_aes_page(),
                self._on_category_option_clicked
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_aes_ecb_decrypt(self):
        page_key = "ctf_aes_ecb_decrypt"
        if page_key not in self.category_pages:
            page = CTF_AES_ECB_DecryptPage(
                self.theme,
                lambda: self._show_ctf_aes_ecb(),
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])





    def _show_ctf_diffie_hellman(self):
        page_key = "ctf_diffie_hellman"
        if page_key not in self.category_pages:
            page = CTFDiffieHellmanPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_dh_encrypt(self):
        page_key = "ctf_dh_encrypt"
        if page_key not in self.category_pages:
            page = CTF_DH_EncryptPage(self.theme, lambda: self._show_ctf_diffie_hellman())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_dh_small_numbers(self):
        page_key = "ctf_dh_small_numbers"
        if page_key not in self.category_pages:
            page = CTF_DH_SmallNumbersPage(self.theme, lambda: self._show_ctf_diffie_hellman())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_documents_page(self):
        page_key = "documents_page"
        if page_key not in self.category_pages:
            page = DocumentsPage(self.theme, lambda: self._show_category("Advanced"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_crack_zip_page(self):
        page_key = "crack_zip_page"
        if page_key not in self.category_pages:
            page = CrackZipPage(
                self.theme, 
                lambda: self._show_documents_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_documents_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_crack_rar_page(self):
        page_key = "crack_rar_page"
        if page_key not in self.category_pages:
            page = CrackRarPage(
                self.theme,
                lambda: self._show_documents_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_documents_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_crack_pdf_page(self):
        page_key = "crack_pdf_page"
        if page_key not in self.category_pages:
            page = CrackPdfPage(
                self.theme,
                lambda: self._show_documents_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_documents_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_crack_office_page(self):
        page_key = "crack_office_page"
        if page_key not in self.category_pages:
            page = CrackOfficePage(
                self.theme,
                lambda: self._show_documents_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_documents_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])


    def _show_crack_7z_page(self):
        page_key = "crack_7z_page"
        if page_key not in self.category_pages:
            page = Crack7zPage(
                self.theme,
                lambda: self._show_documents_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_documents_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])









    def _show_openssl_page(self):
        page_key = "openssl"
        if page_key not in self.category_pages:
            page = OpenSSLPage(
                self.theme, 
                lambda: self._show_category("Advanced"), 
                self._on_category_option_clicked
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_openssl_generate_rsa(self):
        page_key = "openssl_generate_rsa"
        if page_key not in self.category_pages:
            page = OpenSSLGenerateRSAPage(
                self.theme,
                lambda: self._show_openssl_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_openssl_generate_ec(self):
        page_key = "openssl_generate_ec"
        if page_key not in self.category_pages:
            page = OpenSSLGenerateECPage(
                self.theme,
                lambda: self._show_openssl_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_openssl_certificate_management(self):
        page_key = "openssl_certificate_management"
        if page_key not in self.category_pages:
            page = OpenSSLCertificateManagementPage(
                self.theme,
                lambda: self._show_openssl_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_openssl_encrypt_decrypt(self):
        page_key = "openssl_encrypt_decrypt"
        if page_key not in self.category_pages:
            page = OpenSSLEncryptDecryptPage(
                self.theme,
                lambda: self._show_openssl_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_caesar_hybrid(self):
        page_key = "caesar_hybrid"
        if page_key not in self.category_pages:
            page = CaesarHybridPage(self.theme, lambda: self._show_caesar_vigenere_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_steganography_page(self):
        page_key = "steganography_page"
        if page_key not in self.category_pages:
            page = SteganographyPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_steganography_embed(self):
        page_key = "steganography_embed"
        if page_key not in self.category_pages:
            page = SteganographyEmbedPage(self.theme, lambda: self._show_steganography_page(), self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_steganography_extract(self):
        page_key = "steganography_extract"
        if page_key not in self.category_pages:
            page = SteganographyExtractPage(
                self.theme,
                lambda: self._show_steganography_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(
                self.shared_wordlist_path, self.shared_split_parts
            )
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_visual_crypto(self):
        page_key = "visual_crypto_page"
        if page_key not in self.category_pages:
            page = StegoVisualCryptoPage(self.theme, lambda: self._show_steganography_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_visual_crypto_encrypt(self):
        page_key = "visual_crypto_encrypt"
        if page_key not in self.category_pages:
            page = StegoVisualCryptoEncryptPage(self.theme, lambda: self._show_visual_crypto())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_visual_crypto_decrypt(self):
        page_key = "visual_crypto_decrypt"
        if page_key not in self.category_pages:
            page = StegoVisualCryptoDecryptPage(self.theme, lambda: self._show_visual_crypto())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_os_page(self):
        page_key = "os_page"
        if page_key not in self.category_pages:
            from gui.os_page import OSPage
            page = OSPage(self.theme, lambda: self._show_category("Advanced"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_linux_options_page(self):
        page_key = "linux_options_page"
        if page_key not in self.category_pages:
            from gui.linux_options_page import LinuxOptionsPage
            page = LinuxOptionsPage(self.theme, lambda: self._show_os_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_linux_passwd_shadow_page(self):
        page_key = "linux_passwd_shadow"
        if page_key not in self.category_pages:
            page = LinuxPasswdShadowPage(
                self.theme,
                lambda: self._show_linux_password_cracking_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_linux_password_cracking_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_live_system_page(self):
        page_key = "linux_live_system"
        if page_key not in self.category_pages:
            page = LiveSystemPage(
                self.theme,
                lambda: self._show_linux_password_cracking_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_linux_password_cracking_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_linux_password_cracking_page(self):
        page_key = "linux_password_cracking"
        if page_key not in self.category_pages:
            from gui.linux_password_cracking import LinuxPasswordCrackingPage
            page = LinuxPasswordCrackingPage(self.theme, lambda: self._show_linux_options_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_windows_options_page(self):
        page_key = "windows_options_page"
        if page_key not in self.category_pages:
            from gui.windows_options_page import WindowsOptionsPage
            page = WindowsOptionsPage(self.theme, lambda: self._show_os_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_windows_sam_system_page(self):
        page_key = "windows_sam_system"
        if page_key not in self.category_pages:
            page = WindowsSAMSystemPage(
                self.theme,
                lambda: self._show_windows_options_page(),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].set_wordlist_config(self.shared_wordlist_path, self.shared_split_parts)
            self.category_pages[page_key].back_callback = lambda: self._show_windows_options_page()
        self.stack.setCurrentWidget(self.category_pages[page_key])







    def _show_ctf_base_page(self):
        page_key = "ctf_base_page"
        if page_key not in self.category_pages:
            page = CTFBasePage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base2_page(self):
        page_key = "base2_page"
        if page_key not in self.category_pages:
            page = Base2Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base16_page(self):
        page_key = "base16_page"
        if page_key not in self.category_pages:
            page = Base16Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base32_page(self):
        page_key = "base32_page"
        if page_key not in self.category_pages:
            page = Base32Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base36_page(self):
        page_key = "base36_page"
        if page_key not in self.category_pages:
            page = Base36Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base45_page(self):
        page_key = "base45_page"
        if page_key not in self.category_pages:
            page = Base45Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base58_page(self):
        page_key = "base58_page"
        if page_key not in self.category_pages:
            page = Base58Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base62_page(self):
        page_key = "base62_page"
        if page_key not in self.category_pages:
            page = Base62Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base64_page(self):
        page_key = "base64_page"
        if page_key not in self.category_pages:
            page = Base64Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base85_page(self):
        page_key = "base85_page"
        if page_key not in self.category_pages:
            page = Base85Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base91_page(self):
        page_key = "base91_page"
        if page_key not in self.category_pages:
            page = Base91Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base92_page(self):
        page_key = "base92_page"
        if page_key not in self.category_pages:
            page = Base92Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_base100_page(self):
        page_key = "base100_page"
        if page_key not in self.category_pages:
            page = Base100Page(self.theme, lambda: self._show_ctf_base_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_morse_code_page(self):
        page_key = "morse_code_page"
        if page_key not in self.category_pages:
            page = MorseCodePage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_morse_text_page(self):
        page_key = "morse_text_page"
        if page_key not in self.category_pages:
            page = MorseTextPage(self.theme, lambda: self._show_category("CTF"))
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_morse_audio_page(self):
        page_key = "morse_audio_page"
        if page_key not in self.category_pages:
            page = MorseAudioPage(self.theme, lambda: self._show_morse_code_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_substitution_page(self):
        page_key = "substitution_page"
        if page_key not in self.category_pages:
            page = SubstitutionPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_substitution_decrypt_key(self):
        page_key = "substitution_decrypt_key"
        if page_key not in self.category_pages:
            page = SubstitutionDecryptKeyPage(self.theme, lambda: self._show_substitution_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_substitution_encrypt_key(self):
        page_key = "substitution_encrypt_key"
        if page_key not in self.category_pages:
            page = SubstitutionEncryptKeyPage(self.theme, lambda: self._show_substitution_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_substitution_frequency(self):
        page_key = "substitution_frequency"
        if page_key not in self.category_pages:
            page = SubstitutionFrequencyPage(
                self.theme, 
                lambda: self._show_substitution_page(),
                quadgram_file=self.shared_json_path  # May be empty (uses system default)
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            # Only update if a custom file was configured
            if self.shared_json_path:
                self.category_pages[page_key].set_quadgram_file(self.shared_json_path)
        self.stack.setCurrentWidget(self.category_pages[page_key])




    def _show_zlib_page(self):
        """Show Zlib main options page."""
        page_key = "zlib_page"
        if page_key not in self.category_pages:
            page = ZlibPage(
                self.theme,
                lambda: self._show_category("CTF"),
                self._on_category_option_clicked
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_zlib_compression(self):
        """Show Zlib compression page."""
        page_key = "zlib_compression"
        if page_key not in self.category_pages:
            page = ZlibCompressionPage(
                self.theme,
                lambda: self._show_zlib_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_zlib_decompression(self):
        """Show Zlib decompression page."""
        page_key = "zlib_decompression"
        if page_key not in self.category_pages:
            page = ZlibDecompressionPage(
                self.theme,
                lambda: self._show_zlib_page()
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])




    def _show_adfgvx_page(self):
        page_key = "adfgvx_page"
        if page_key not in self.category_pages:
            page = ADFGVXPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_adfgvx_decrypt(self):
        page_key = "adfgvx_decrypt"
        if page_key not in self.category_pages:
            page = ADFGVXDecryptPage(self.theme, lambda: self._show_adfgvx_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_adfgvx_encrypt(self):
        page_key = "adfgvx_encrypt"
        if page_key not in self.category_pages:
            page = ADFGVXEncryptPage(self.theme, lambda: self._show_adfgvx_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])





    def _show_ctf_symbols_page(self):
        page_key = "ctf_symbols_page"
        if page_key not in self.category_pages:
            page = CTFSymbolsPage(
                self.theme,
                lambda: self._show_category("CTF"),
                self._on_category_option_clicked
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_pigpen_page(self):
        page_key = "ctf_pigpen_page"
        if page_key not in self.category_pages:
            page = CTFPigpenPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_pigpen_encrypt(self):
        page_key = "ctf_pigpen_encrypt"
        if page_key not in self.category_pages:
            page = PigpenEncryptPage(self.theme, lambda: self._show_ctf_pigpen_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_pigpen_decrypt(self):
        page_key = "ctf_pigpen_decrypt"
        if page_key not in self.category_pages:
            page = PigpenDecryptPage(self.theme, lambda: self._show_ctf_pigpen_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_navy_page(self):
        page_key = "ctf_navy_page"
        if page_key not in self.category_pages:
            page = CTFNavyPage(self.theme, lambda: self._show_ctf_symbols_page(), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_navy_encrypt(self):
        page_key = "ctf_navy_encrypt"
        if page_key not in self.category_pages:
            page = NavyEncryptPage(self.theme, lambda: self._show_ctf_navy_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_navy_decrypt(self):
        page_key = "ctf_navy_decrypt"
        if page_key not in self.category_pages:
            page = NavyDecryptPage(self.theme, lambda: self._show_ctf_navy_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])






    def _show_ctf_atbash_page(self):
        page_key = "ctf_atbash_page"
        if page_key not in self.category_pages:
            page = CTFAtbashPage(self.theme, lambda: self._show_category("CTF"), self._on_category_option_clicked)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_ctf_atbash_encrypt(self):
        page_key = "ctf_atbash_encrypt"
        if page_key not in self.category_pages:
            page = AtbashEncryptPage(self.theme, lambda: self._show_ctf_atbash_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])


    def _show_ctf_atbash_decrypt(self):
        page_key = "ctf_atbash_decrypt"
        if page_key not in self.category_pages:
            page = AtbashDecryptPage(self.theme, lambda: self._show_ctf_atbash_page())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])





    
    def _show_configurations(self):
        page_key = "config"
        previous_widget = self.stack.currentWidget()
    
        if page_key not in self.category_pages:
            page = ConfigPage(
                self.theme,
                lambda: self.stack.setCurrentWidget(previous_widget),
                wordlist_path=self.shared_wordlist_path,
                split_parts=self.shared_split_parts
            )
            page.wordlist_configured.connect(self._on_wordlist_configured)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].back_callback = lambda: self.stack.setCurrentWidget(previous_widget)
            self.category_pages[page_key].wordlist_path = self.shared_wordlist_path
            self.category_pages[page_key].split_parts = self.shared_split_parts
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _show_json_config(self):
        page_key = "json_config"
        previous_widget = self.stack.currentWidget()
    
        if page_key not in self.category_pages:
            page = JsonConfigPage(
                self.theme,
                lambda: self.stack.setCurrentWidget(previous_widget),
                json_path=self.shared_json_path
            )
            page.json_configured.connect(self._on_json_configured)
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].back_callback = lambda: self.stack.setCurrentWidget(previous_widget)
            self.category_pages[page_key].json_path = self.shared_json_path
        self.stack.setCurrentWidget(self.category_pages[page_key])

    def _on_json_configured(self, json_path):
        """Handle JSON quadgram file configuration."""
        self.shared_json_path = json_path
        user_prefs.set_json_path(json_path)
    
        # Update substitution frequency page if already cached
        if "substitution_frequency" in self.category_pages:
            self.category_pages["substitution_frequency"].set_quadgram_file(json_path)
    
    def _show_john_config(self):
        page_key = "john_config"
        previous_widget = self.stack.currentWidget()
    
        if page_key not in self.category_pages:
            page = JohnConfigPage(
                self.theme,
                lambda: self.stack.setCurrentWidget(previous_widget)
            )
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        else:
            self.category_pages[page_key].back_callback = lambda: self.stack.setCurrentWidget(previous_widget)
        self.stack.setCurrentWidget(self.category_pages[page_key])
    
    def _on_wordlist_configured(self, wordlist_path, split_parts):
        self.shared_wordlist_path = wordlist_path
        self.shared_split_parts = split_parts
        user_prefs.set_wordlist(wordlist_path, split_parts)
        
        for key in ["hashing_detail", "md5_reverse", "sha_reverse", "wifi_page", "caesar_bruteforce", "crack_zip_page", "crack_rar_page", "crack_7z_page", "crack_pdf_page", "crack_office_page", "steganography_extract", "linux_passwd_shadow", "linux_live_system", "windows_sam_system"]:
            if key in self.category_pages:
                self.category_pages[key].set_wordlist_config(wordlist_path, split_parts)
    
    def _show_landing(self):
        self.stack.setCurrentWidget(self.landing_page)
    
    def _show_user_guide(self):
        page_key = "user_guide"
        if page_key not in self.category_pages:
            page = UserGuidePage(self.theme, lambda: self._show_landing())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])
    
    def _show_about(self):
        dialog = AboutDialog(self.theme, self)
        dialog.exec()

    def _show_license(self):
        page_key = "license"
        if page_key not in self.category_pages:
            page = LicensePage(self.theme, lambda: self._show_landing())
            self.category_pages[page_key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.category_pages[page_key])