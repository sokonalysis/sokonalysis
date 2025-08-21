from colorama import Fore, Style, init
import os
import subprocess
import sys

init(autoreset=True)

def check_command_exists(cmd):
    return subprocess.call(f"type {cmd}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def run_cmd(cmd, capture_output=False):
    try:
        if capture_output:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        else:
            subprocess.run(cmd, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[x] Command failed: {' '.join(cmd)}" + Style.RESET_ALL)
        if e.output:
            print(e.output.decode())
        sys.exit(1)

def main():
    print(Fore.CYAN + "    Put the zipped file in /sokonalysis/src/    " + Style.RESET_ALL)
    zip_file = input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter the ZIP filename (e.g., example.zip): ").strip()

    if not os.path.isfile(zip_file):
        print(Fore.RED + f"[x] File '{zip_file}' does not exist." + Style.RESET_ALL)
        sys.exit(1)

    # Check required tools
    for tool in ["zip2john", "john", "unzip"]:
        if not check_command_exists(tool):
            print(Fore.RED + f"[x] Required tool '{tool}' not found in PATH." + Style.RESET_ALL)
            sys.exit(1)

    hash_file = "zip_hash.txt"

    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Extracting hash with zip2john...")
    with open(hash_file, "w") as f:
        subprocess.run(["zip2john", zip_file], stdout=f, check=True)

    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Cracking password with john...")
    run_cmd(["john", hash_file])

    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Getting cracked password from john --show...")
    output = run_cmd(["john", "--show", hash_file], capture_output=True)
    print(output)

    # Parse password from john --show output
    password = None
    for line in output.splitlines():
        if ":" in line and not line.startswith("0 password hashes cracked"):
            parts = line.split(":")
            if len(parts) >= 2:
                password = parts[1].strip()
                break

    if not password:
        print(Fore.RED + "[x] Password not found or cracked." + Style.RESET_ALL)
        sys.exit(1)

    print(Fore.GREEN + f"[-] Password found: {password}" + Style.RESET_ALL)

    # Unzip with the cracked password
    print(Fore.CYAN + "[*]" + Style.RESET_ALL + " Extracting ZIP contents...")
    try:
        run_cmd(["unzip", "-P", password, zip_file])
        print(Fore.GREEN + "[-] Extraction complete!" + Style.RESET_ALL)
    except Exception:
        print(Fore.RED + "[x] Failed to unzip with the password." + Style.RESET_ALL)
        sys.exit(1)

if __name__ == "__main__":
    main()
