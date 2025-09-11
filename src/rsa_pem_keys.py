#!/usr/bin/env python3

import os
import base64
from colorama import Fore, Style, init
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Initialize colorama
init(autoreset=True)

def load_private_key(path):
    try:
        with open(path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        print(Fore.GREEN + "[+]" + Style.RESET_ALL + f" Private key loaded from '{path}'")
        return private_key
    except Exception as e:
        print(Fore.RED + "[x] Failed to load private key:" + Style.RESET_ALL, e)
        return None

def decrypt_file(private_key, ciphertext_path):
    try:
        with open(ciphertext_path, "rb") as f:
            data = f.read()
        print(Fore.GREEN + "[*]" + Style.RESET_ALL + f" Ciphertext loaded from '{ciphertext_path}'")

        # Try base64 decoding first
        try:
            ciphertext = base64.b64decode(data)
            print(Fore.YELLOW + "[*]" + Style.RESET_ALL + " Base64 decoding applied")
        except Exception:
            ciphertext = data

        # Try OAEP padding
        try:
            plaintext = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            print(Fore.GREEN + "[+]" + Style.RESET_ALL + " Decryption successful with OAEP padding")
            return plaintext
        except Exception:
            # Fallback to PKCS1v15
            plaintext = private_key.decrypt(
                ciphertext,
                padding.PKCS1v15()
            )
            print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Decryption successful with PKCS1v15 padding")
            return plaintext

    except Exception as e:
        print(Fore.RED + "[x] Decryption failed:" + Style.RESET_ALL, e)
        return None

def main():
    key_path = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the private key file name or full path (e.g., key.pem): ").strip()
    if not os.path.exists(key_path):
        print(Fore.RED + "[x] Private key file does not exist.")
        return

    private_key = load_private_key(key_path)
    if not private_key:
        return

    cipher_path = input(Fore.YELLOW + "\n[>] " + Style.RESET_ALL + "Enter the ciphertext file name or full path: ").strip()
    if not os.path.exists(cipher_path):
        print(Fore.RED + "[x] Ciphertext file does not exist.")
        return

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + " Decrypting...\n")
    plaintext = decrypt_file(private_key, cipher_path)

    if plaintext:
        print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Decrypted text: " + Fore.GREEN + plaintext.decode(errors='ignore'))
        print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[x] Could not decrypt the file. Check if the ciphertext or key is correct.")

if __name__ == "__main__":
    main()
