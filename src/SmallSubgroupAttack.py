from sympy import factorint, discrete_log
from Crypto.Util.number import long_to_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from hashlib import sha256
from colorama import Fore, Back, Style, init
init(autoreset=True)

def main():
    p = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter p: "))
    g = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter g: "))
    A = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter A: "))
    B = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter B: "))
    encrypted_flag_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter encrypted flag (hex): ")


    print("\n" + Fore.GREEN + "[*] " + Style.RESET_ALL + "Factoring p-1...")
    factors = factorint(p-1)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Factors of p-1: " + Fore.GREEN + f"{factors}" + Style.RESET_ALL)

    # Find order q of g
    q = None
    for f in factors:
        if pow(g, f, p) == 1:
            q = f
            print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Found order q of g: " + Fore.GREEN + f"{q}" + Style.RESET_ALL)
            break

    if q is None:
        print(Fore.RED + "[x] " + Style.RESET_ALL + "Could not find order of g.")
        return

    print("\n" + Fore.GREEN + "[*] " + Style.RESET_ALL + "Computing discrete log a such that g^a = A mod p...")
    a = discrete_log(p, A, g, order=q)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Discrete log a = " + Fore.GREEN + f"{a}" + Style.RESET_ALL)

    print("[*] Computing shared secret ss = B^a mod p...")
    ss = pow(B, a, p)

    print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Deriving AES key from shared secret...")
    key = sha256(long_to_bytes(ss)).digest()[:16]

    print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Decrypting flag ciphertext...")
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted_flag = bytes.fromhex(encrypted_flag_hex)
    plaintext_padded = cipher.decrypt(encrypted_flag)
    plaintext = unpad(plaintext_padded, 16)

    print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Flag: " + Fore.GREEN + plaintext.decode() + Style.RESET_ALL)
    print(Fore.BLUE + "_________________________________________________________________" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
