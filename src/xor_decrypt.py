from colorama import Fore, Style, init
init(autoreset=True)

def xor_decrypt():
    
    key_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter key (hex): ").strip()
    cipher_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter ciphertext (hex): ").strip()

    try:
        key = bytes.fromhex(key_hex)
        cipher = bytes.fromhex(cipher_hex)
    except ValueError:
        print(Fore.RED + "[x] Invalid hex input. Please try again." + Style.RESET_ALL)
        return
    
    if len(key) != len(cipher):
        print(Fore.RED + f"[x] Key and ciphertext lengths differ: {len(key)} != {len(cipher)}" + Style.RESET_ALL)
        return

    plaintext = bytes([c ^ k for c, k in zip(cipher, key)])

    print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
    print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Raw Decrypted Bytes: " + Style.RESET_ALL + repr(plaintext))
    print(Fore.GREEN + "[-]" + Style.RESET_ALL + " As String (errors replaced): " + Style.RESET_ALL + plaintext.decode(errors='replace'))
    print(Fore.BLUE + "_________________________________________________________________" + Style.RESET_ALL)

if __name__ == "__main__":
    xor_decrypt()
