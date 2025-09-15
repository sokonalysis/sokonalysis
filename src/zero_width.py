#!/usr/bin/env python3

import os
from colorama import Fore, Style, init

# Initialize colorama for cross-platform terminal colors
init(autoreset=True)

def decode_whitespace_cipher(cipher_text):
    binary_map = {
        ' ': '0',
        '\t': '1'
    }
    binary_str = ''.join(binary_map[c] for c in cipher_text if c in binary_map)
    decoded_chars = [
        chr(int(binary_str[i:i+8], 2))
        for i in range(0, len(binary_str), 8)
        if len(binary_str[i:i+8]) == 8
    ]
    return ''.join(decoded_chars).strip()

def main():
    print(Fore.MAGENTA + "\n╔══════════════════════════════════════════╗")
    print("║     🕵️‍♂️  Whitespace Cipher Decoder      ║")
    print("╚══════════════════════════════════════════╝\n" + Style.RESET_ALL)

    user_input = input(Fore.YELLOW + "[>] " + Style.RESET_ALL +
                       "Enter the file name or full path (e.g., 'cipher.txt' or '/path/to/cipher.txt'): ").strip()

    if os.path.isfile(user_input):
        file_path = user_input
    else:
        file_path = os.path.join(os.getcwd(), user_input)
        if not os.path.isfile(file_path):
            print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
            print(Fore.RED + "[x]" + Style.RESET_ALL + " File not found.")
            print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
            return

    print(Fore.CYAN + "\n🔍 Inspecting and decoding...\n" + Style.RESET_ALL)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cipher_text = f.read()

        hidden_message = decode_whitespace_cipher(cipher_text)

        if hidden_message:
            print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
            print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Decoded Hidden Message: " +
                  Style.BRIGHT + Fore.GREEN + f"{hidden_message}")
            print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
        else:
            print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
            print(Fore.RED + "[!]" + Style.RESET_ALL + " No hidden message could be decoded.\n")
            print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)

    except Exception as e:
        print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.RED + "[x]" + Style.RESET_ALL + f" Error reading file: {e}\n")
        print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
