#!/usr/bin/env python3

import os
import re
import zipfile
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def extract_hidden_message(xlsx_file):
    try:
        with zipfile.ZipFile(xlsx_file, 'r') as z:
            hidden_msgs = []
            # Scan all XML files inside the Excel archive
            for f in z.namelist():
                if f.endswith(".xml"):
                    try:
                        data = z.read(f).decode("utf-8", errors="ignore")
                        # Regex: look for groups of 8-bit binary values
                        binary_blocks = re.findall(r'(?:[01]{8}\s+){3,}[01]{8}', data)
                        for block in binary_blocks:
                            bits = block.strip().split()
                            decoded = ''.join(chr(int(b, 2)) for b in bits)
                            hidden_msgs.append((f, decoded))
                    except Exception:
                        continue
            return hidden_msgs
    except Exception as e:
        print(Fore.RED + "[x]" + Style.RESET_ALL + f" Failed to open '{xlsx_file}': {e}")
        return None

def main():
    # Ask user for file
    xlsx_path = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + 
                      "Enter the Excel file name or full path (e.g., mylist.xlsx): ").strip()

    if not os.path.exists(xlsx_path):
        print(Fore.RED + "[x]" + Style.RESET_ALL + " File does not exist.")
        return

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + " Scanning for hidden binary messages...\n")
    messages = extract_hidden_message(xlsx_path)

    if not messages:
        print(Fore.RED + "[x]" + Style.RESET_ALL + " No hidden message found.")
        return

    print(Fore.BLUE + "_____________________________________________________________\n" + Style.RESET_ALL)
    for loc, msg in messages:
        print(Fore.GREEN + "[-]" + Style.RESET_ALL + f" Found hidden message in: {Fore.CYAN}{loc}" + Style.RESET_ALL + " is ")
        print(Fore.YELLOW + "    " + Style.RESET_ALL + msg)
    print(Fore.BLUE + "_____________________________________________________________\n" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
