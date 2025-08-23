#!/usr/bin/env python3

import sys
from math import gcd
from colorama import Fore, Style, init

init(autoreset=True)

def modinv(a, m=256):
    a = a % m
    if gcd(a, m) != 1:
        return None
    t, newt = 0, 1
    r, newr = m, a
    while newr != 0:
        quotient = r // newr
        t, newt = newt, t - quotient * newt
        r, newr = newr, r - quotient * newr
    if t < 0:
        t += m
    return t

def decrypt(ct, m, n):
    m_inv = modinv(m, 256)
    if m_inv is None:
        return None
    pt = bytes([(m_inv * (c - n)) % 256 for c in ct])
    return pt

def looks_like_png(data):
    png_signature = b'\x89PNG\r\n\x1a\n'
    return data.startswith(png_signature)

def decrypt_affine_file():
    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Place the encrypted file in the current directory.")
    filename = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the name of the file to decrypt (e.g., enc.bin): ").strip()

    try:
        with open(filename, "rb") as f:
            ct = f.read()
    except FileNotFoundError:
        print(Fore.RED + f"[x] File not found: {filename}" + Style.RESET_ALL)
        sys.exit(1)

    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Starting brute-force key search...\n")

    for m in range(1, 256):
        if gcd(m, 256) != 1:
            continue
        for n in range(256):
            pt = decrypt(ct, m, n)
            if pt is None:
                continue
            if looks_like_png(pt):
                print(Fore.GREEN + f"[-] Success! Found keys: m = {m}, n = {n}")
            
                output_file = "decrypted_flag.png"
                with open(output_file, "wb") as out:
                    out.write(pt)
                print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
                print(Fore.GREEN + "[-]" + Style.RESET_ALL + f" Decrypted PNG saved as: {output_file}")
                print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
                return

    print(Fore.RED + "[x] Failed to find valid keys. File may not be an affine-encrypted PNG.")

if __name__ == "__main__":
    decrypt_affine_file()
