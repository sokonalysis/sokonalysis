#!/usr/bin/env python3

import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def get_grid(use_v=True):
    """Return Polybius grid: ADFGVX (6x6) or ADFGX (5x5)."""
    if use_v:
        # ADFGVX 6x6: letters + digits
        return {
            'A': {'A': 'A', 'D': 'B', 'F': 'C', 'G': 'D', 'V': 'E', 'X': 'F'},
            'D': {'A': 'G', 'D': 'H', 'F': 'I', 'G': 'J', 'V': 'K', 'X': 'L'},
            'F': {'A': 'M', 'D': 'N', 'F': 'O', 'G': 'P', 'V': 'Q', 'X': 'R'},
            'G': {'A': 'S', 'D': 'T', 'F': 'U', 'G': 'V', 'V': 'W', 'X': 'X'},
            'V': {'A': 'Y', 'D': 'Z', 'F': '0', 'G': '1', 'V': '2', 'X': '3'},
            'X': {'A': '4', 'D': '5', 'F': '6', 'G': '7', 'V': '8', 'X': '9'}
        }
    else:
        # ADFGX 5x5: letters only (I=J combined)
        return {
            'A': {'A': 'A', 'D': 'B', 'F': 'C', 'G': 'D', 'X': 'E'},
            'D': {'A': 'F', 'D': 'G', 'F': 'H', 'G': 'I/J', 'X': 'K'},
            'F': {'A': 'L', 'D': 'M', 'F': 'N', 'G': 'O', 'X': 'P'},
            'G': {'A': 'Q', 'D': 'R', 'F': 'S', 'G': 'T', 'X': 'U'},
            'X': {'A': 'V', 'D': 'W', 'F': 'X', 'G': 'Y', 'X': 'Z'}
        }

def adfgx_or_adfgvx(ciphertext):
    """Detect which cipher variant is used."""
    if "V" in ciphertext:
        return True  # ADFGVX (6x6)
    return False     # ADFGX (5x5)

def adfgvx_decrypt(ciphertext):
    use_v = adfgx_or_adfgvx(ciphertext)
    grid = get_grid(use_v)

    if len(ciphertext) % 2 != 0:
        print(Fore.RED + "[x] Error:" + Style.RESET_ALL + " Ciphertext length must be even.\n")
        sys.exit(1)

    plaintext = []
    for i in range(0, len(ciphertext), 2):
        row_key = ciphertext[i]
        col_key = ciphertext[i+1]
        if row_key in grid and col_key in grid[row_key]:
            plaintext.append(grid[row_key][col_key])
        else:
            plaintext.append('?')  # Invalid character pair
    
    return ''.join(plaintext), use_v

def main():
    ciphertext = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the ciphertext: ").strip().upper()

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + " Decrypting...\n")
    decrypted, used_v = adfgvx_decrypt(ciphertext)

    if used_v:
        print(Fore.RED + "[-]" + Style.RESET_ALL + " Detected: " + Fore.RED + "ADFGVX (6x6 grid)")
    else:
        print(Fore.RED + "[-]" + Style.RESET_ALL + " Detected: " + Fore.RED + "ADFGX (5x5 grid)")
        
    print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
    print(Fore.GREEN + "[-]" + Style.RESET_ALL + f" Decrypted text: {Fore.GREEN}{decrypted.upper()}")
    print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
