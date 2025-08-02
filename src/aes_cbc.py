from base64 import b64decode
from Crypto.Cipher import AES
from colorama import Fore, Style, init
from urllib.parse import unquote  # For decoding URL-encoded base64 strings

# Initialize colorama
init(autoreset=True)

def decrypt_aes_cbc(key_b64, ciphertext_b64):
    try:
        print("\n" + Fore.GREEN + "[*] " + Style.RESET_ALL + "Decoding key and ciphertext from base64...")

        # Decode URL encoding first
        key_b64 = unquote(key_b64)
        ciphertext_b64 = unquote(ciphertext_b64)

        key = b64decode(key_b64)
        ciphertext = b64decode(ciphertext_b64)

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Extracting IV from ciphertext...")
        iv = ciphertext[:16]
        data = ciphertext[16:]

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Initializing AES cipher in CBC mode...")
        cipher = AES.new(key, AES.MODE_CBC, iv)

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Decrypting and stripping zero padding...")
        decrypted = cipher.decrypt(data)
        plaintext = decrypted.rstrip(b'\x00')

        print(Fore.BLUE + "\n_______________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Decrypted Output: " + Fore.GREEN + plaintext.decode('utf-8', errors='ignore') + Style.RESET_ALL)
        print(Fore.BLUE + "_______________________________________________________________\n" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[x] " + Style.RESET_ALL + "Error: " + str(e))

def main():
    key_b64 = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter base64-encoded AES key: ").strip()
    ciphertext_b64 = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter base64-encoded ciphertext (IV + data): ").strip()
    decrypt_aes_cbc(key_b64, ciphertext_b64)

if __name__ == "__main__":
    main()
from base64 import b64decode
from Crypto.Cipher import AES
from colorama import Fore, Style, init
from urllib.parse import unquote  # For decoding URL-encoded base64 strings

# Initialize colorama
init(autoreset=True)

def decrypt_aes_cbc(key_b64, ciphertext_b64):
    try:
        print("\n" + Fore.GREEN + "[*] " + Style.RESET_ALL + "Decoding key and ciphertext from base64...")

        # Decode URL encoding first
        key_b64 = unquote(key_b64)
        ciphertext_b64 = unquote(ciphertext_b64)

        key = b64decode(key_b64)
        ciphertext = b64decode(ciphertext_b64)

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Extracting IV from ciphertext...")
        iv = ciphertext[:16]
        data = ciphertext[16:]

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Initializing AES cipher in CBC mode...")
        cipher = AES.new(key, AES.MODE_CBC, iv)

        print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Decrypting and stripping zero padding...")
        decrypted = cipher.decrypt(data)
        plaintext = decrypted.rstrip(b'\x00')

        print(Fore.BLUE + "\n_______________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Decrypted Output: " + Fore.GREEN + plaintext.decode('utf-8', errors='ignore') + Style.RESET_ALL)
        print(Fore.BLUE + "_______________________________________________________________\n" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[x] " + Style.RESET_ALL + "Error: " + str(e))

def main():
    key_b64 = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter base64-encoded AES key: ").strip()
    ciphertext_b64 = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter base64-encoded ciphertext (IV + data): ").strip()
    decrypt_aes_cbc(key_b64, ciphertext_b64)

if __name__ == "__main__":
    main()
