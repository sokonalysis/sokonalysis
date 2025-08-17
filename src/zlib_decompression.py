from colorama import Fore, Style, init
import zlib
import sys

init(autoreset=True)

def decompress_zlib_file():
    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Please place the file you want to process inside the 'sokonalysis/src/' directory.")
    filename = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the name of the file to process: ").strip()

    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(Fore.RED + f"[x] File not found: {filename}" + Style.RESET_ALL)
        return

    # Possible common zlib headers
    possible_headers = [b'\x78\x01', b'\x78\x5e', b'\x78\x9c', b'\x78\xda']

    start = -1
    for header in possible_headers:
        start = data.find(header)
        if start != -1:
            break

    if start == -1:
        print(Fore.RED + "[x]" + Style.RESET_ALL + " No valid zlib header found in the file.")
        return

    clean_data = data[start:]

    try:
        decompressed = zlib.decompress(clean_data)
        print(Fore.BLUE + "\n_________________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Decompressed Data:" , decompressed.decode(errors='replace'))
        print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[x]" + Style.RESET_ALL + " Decompression failed: {e}")

if __name__ == "__main__":
    decompress_zlib_file()
