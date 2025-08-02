import hashlib
import string
from colorama import Fore, Style, init

init(autoreset=True)

# Prompt with [>] in yellow and message on same line
encoded_hex = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the encoded hex string: ").strip()

printable_chars = string.printable[:-6]  # printable chars except some whitespace

pairs = [c1 + c2 for c1 in printable_chars for c2 in printable_chars]

def sha512_hex(s):
    return hashlib.sha512(s.encode()).hexdigest()

print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Precomputing all trimmed reversed hashes...")

lookup = {}
for pair in pairs:
    full_hash = sha512_hex(pair)
    for a in range(1, 17):
        for b in range(1, 17):
            trimmed = full_hash[a:-b]
            reversed_trimmed = trimmed[::-1]
            lookup[reversed_trimmed] = (pair, a, b)

print(Fore.GREEN + "[*] " + Style.RESET_ALL + "Precompute done. Starting decoding...\n")

min_trim_len = 128 - 16 - 16  # 96
max_trim_len = 128 - 1 - 1    # 126
max_pad_len = 62  # max padding length in hex chars (31 bytes * 2)

pos = 0
length = len(encoded_hex)
recovered = ""

while pos < length:
    found = False
    for pad_left in range(0, max_pad_len + 1, 2):
        for pad_right in range(0, max_pad_len + 1, 2):
            for trim_len in range(min_trim_len, max_trim_len + 1, 2):
                start = pos + pad_left
                end = start + trim_len
                if end + pad_right > length:
                    continue
                candidate = encoded_hex[start:end]
                if candidate in lookup:
                    pair, a, b = lookup[candidate]
                    print(Fore.CYAN + f"[+] " + Style.RESET_ALL +
                          f"Found pair '{Fore.YELLOW + pair + Style.RESET_ALL}' at pos {pos} with " +
                          f"pad_left {pad_left//2}, pad_right {pad_right//2}, trim_len {trim_len}, a={a}, b={b}")
                    recovered += pair
                    pos = pos + pad_left + trim_len + pad_right
                    found = True
                    break
            if found:
                break
        if found:
            break
    if not found:
        pos += 2  # skip 1 byte if no match
print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Recovered flag: " + Fore.GREEN + recovered + Style.RESET_ALL)
print(Fore.BLUE + "_________________________________________________________________" + Style.RESET_ALL)
