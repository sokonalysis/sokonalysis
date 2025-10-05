#!/usr/bin/env python3
"""
Interactive, colorful Office (Word) brute-force script for authorized CTF use.

Prompts the user for:
 - protected Word file (e.g., secret.docx)
 - wordlist path (e.g., rockyou.txt)

Requirements:
    pip install msoffcrypto-tool colorama tqdm

Author: ChatGPT (for authorized/CTF use only)
"""

import os
import io
import sys
from pathlib import Path
import msoffcrypto
from colorama import Fore, Style, init
from tqdm import tqdm

# initialize colorama
init(autoreset=True)

def info(msg):    print(Fore.CYAN + "[*] " + Style.RESET_ALL + msg)
def ok(msg):      print(Fore.GREEN + "[+] " + Style.RESET_ALL + msg)
def warn(msg):    print(Fore.YELLOW + "[!] " + Style.RESET_ALL + msg)
def err(msg):     print(Fore.RED + "[x] " + Style.RESET_ALL + msg)

def try_password_bytes(file_bytes, password, write_output_path=None):
    """
    Attempt to decrypt an Office file given its bytes and a password string.
    Returns True on success and optionally writes the decrypted file.
    """
    bio = io.BytesIO(file_bytes)
    try:
        office = msoffcrypto.OfficeFile(bio)
        office.load_key(password=password)
        dec = io.BytesIO()
        office.decrypt(dec)
        # If no exception -> success
        if write_output_path:
            with open(write_output_path, "wb") as fo:
                fo.write(dec.getvalue())
        return True
    except Exception:
        return False

def count_lines(path):
    # fast-ish line count
    with open(path, "rb") as f:
        return sum(1 for _ in f)

def main():
    print(Fore.BLUE + "\nOffice Word Bruteforce (CTF / authorized use only)\n" + Style.RESET_ALL)

    doc_path = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter protected Word file name or path (e.g., secret.docx): ").strip()
    if not doc_path:
        err("No file provided. Exiting.")
        return
    if not os.path.exists(doc_path):
        err(f"File not found: {doc_path}")
        return

    wordlist_path = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter wordlist file name (if in this current dir) or path (e.g., rockyou.txt) OR type 'wordlist.txt' for the local wordlist: ").strip()
    if not wordlist_path:
        err("No wordlist provided. Exiting.")
        return
    if not os.path.exists(wordlist_path):
        err(f"Wordlist not found: {wordlist_path}")
        return

    save_dir = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Optional: output directory to save decrypted file (press Enter to use current dir): \n").strip()
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    else:
        save_dir = "."

    # Load protected file bytes once
    info(f"Loading protected file: {doc_path}")
    try:
        file_bytes = Path(doc_path).read_bytes()
    except Exception as e:
        err(f"Failed to read protected file: {e}")
        return

    total_pw = None
    try:
        info("Counting passwords in wordlist (this may take a moment for large lists)...")
        total_pw = count_lines(wordlist_path)
    except Exception:
        warn("Could not count lines; progress bar will be indeterminate.")
        total_pw = None

    info("Starting brute-force (will try each password in the provided wordlist)...")
    found = None
    output_path = None
    try:
        with open(wordlist_path, "r", errors="ignore") as wl:
            iterator = (line.rstrip("\n\r") for line in wl)
            pbar = tqdm(iterator, total=total_pw, unit="pw", desc="Trying passwords", ncols=80)
            for raw_pw in pbar:
                if not raw_pw:
                    continue
                password = raw_pw
                # attempt
                ok_try = try_password_bytes(file_bytes, password, write_output_path=None)
                if ok_try:
                    found = password
                    pbar.close()
                    break
    except KeyboardInterrupt:
        warn("Interrupted by user.")
        return
    except Exception as e:
        err(f"Unexpected error while reading wordlist: {e}")
        return

    if found:
        ok(f"Password found: {found}")
        # write decrypted file
        out_name = f"{Path(doc_path).stem}_decrypted{Path(doc_path).suffix}"
        output_path = os.path.join(save_dir, out_name)
        info(f"Writing decrypted file to: {output_path}")
        success = try_password_bytes(file_bytes, found, write_output_path=output_path)
        if success:
            ok(f"Decrypted file written: {output_path}")
        else:
            warn("Password validated earlier but failed to write decrypted file (unexpected).")
    else:
        err("No matching password found in the provided wordlist.")

    print()  # newline for tidy output

if __name__ == "__main__":
    main()
