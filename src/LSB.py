#!/usr/bin/env python3
# colorful_extract_blue_lsb.py
# Extracts LSBs from the BLUE channel of the first pixels of a PNG and prints candidate messages.

import sys
from PIL import Image
from colorama import Fore, Style, init

init(autoreset=True)

MAX_PIXELS = 4096  # how many pixels to check

def bits_to_bytes(bits, msb_first=True):
    out = []
    if msb_first:
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) < 8:
                break
            val = 0
            for b in byte_bits:
                val = (val << 1) | b
            out.append(val)
    else:
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            if len(byte_bits) < 8:
                break
            val = 0
            for j, b in enumerate(byte_bits):
                val |= (b << j)
            out.append(val)
    return bytes(out)

def printable(s):
    try:
        ts = s.decode('utf-8', errors='strict')
    except:
        ts = None
    if ts:
        good = sum(1 for c in ts if 32 <= ord(c) <= 126 or c in '\r\n\t')
        return ts if good / max(1, len(ts)) > 0.6 else None
    return None

def extract(png, max_pixels=4096):
    im = Image.open(png)
    im = im.convert('RGBA')
    w,h = im.size
    total = min(w*h, max_pixels)
    pixels = im.getdata()
    bits = []
    for i in range(total):
        r,g,b,a = pixels[i]
        bits.append(b & 1)
    return bits

def try_and_print(bits, label):
    for msb_first in (True, False):
        byts = bits_to_bytes(bits, msb_first=msb_first)
        if 0 in byts:
            byts = byts[:byts.index(0)]
        text = printable(byts)
        mode = "MSB-first" if msb_first else "LSB-first"
        print(Fore.CYAN + f"\n[{label}] Interpretation: {mode}" + Style.RESET_ALL)
        if text:
            print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
            print(Fore.GREEN + "Decoded (utf-8): " + Style.RESET_ALL + text)
            print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + "Raw bytes (hex): " + Style.RESET_ALL + byts.hex())
            try:
                print(Fore.YELLOW + "Raw ASCII (best-effort): " + Style.RESET_ALL + byts.decode('latin-1', errors='replace'))
            except:
                pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        PNG = sys.argv[1]
    else:
        PNG = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter path to the PNG (or filename if in same folder): ").strip()

    try:
        bits = extract(PNG, MAX_PIXELS)
    except FileNotFoundError:
        print(Fore.RED + f"[x] File not found: {PNG}" + Style.RESET_ALL)
        sys.exit(1)

    print(Fore.CYAN + f"\n[*] Extracted {len(bits)} LSB bits from blue channel (first {MAX_PIXELS} pixels cap)." + Style.RESET_ALL)

    for n_bits in (8*8, 8*16, 8*32, len(bits)):
        if n_bits > len(bits):
            continue
        print(Fore.MAGENTA + f"\nTrying first {n_bits//8} bytes ({n_bits} bits)" + Style.RESET_ALL)
        try_and_print(bits[:n_bits], label=f"first {n_bits} bits")

    print(Fore.CYAN + "\nDone" + Style.RESET_ALL)
