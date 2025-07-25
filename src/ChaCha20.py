# Run this script from main.cpp when the user selects the attack option

from colorama import Fore, Style, init
init(autoreset=True)

def hex_to_bytes(hex_str):
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        print(Fore.RED + "[x] " + Style.RESET_ALL + "Invalid hex input.")
        exit(1)

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def main():
    iv_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the IV (hex): ")
    ciphertext1_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the ciphertext of the known message (hex): ")
    ciphertext2_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the ciphertext of the FLAG (hex): ")

    ciphertext1 = hex_to_bytes(ciphertext1_hex)
    ciphertext2 = hex_to_bytes(ciphertext2_hex)

    user_input = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the known plaintext message (as text): ").encode()

    if len(user_input) != len(ciphertext1):
        print(Fore.RED + "[x] " + Style.RESET_ALL + "Your input must be" + Fore.GREEN + f" {len(ciphertext1)} " + Style.RESET_ALL + "bytes to match ciphertext length.")
        return

    keystream = xor_bytes(ciphertext1, user_input)
    recovered_flag = xor_bytes(ciphertext2, keystream[:len(ciphertext2)])

    print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
    try:
        print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Recovered FLAG: " + Fore.GREEN + recovered_flag.decode() + Style.RESET_ALL)
    except UnicodeDecodeError:
        print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Recovered FLAG: " + Fore.GREEN + str(recovered_flag) + Style.RESET_ALL)
    print(Fore.BLUE + "_________________________________________________________________" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
