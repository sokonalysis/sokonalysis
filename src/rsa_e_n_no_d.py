from Crypto.Util.number import inverse
from colorama import Fore, Style, init

init(autoreset=True)

def main():

    # Input number of prime factors
    num_factors = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter number of prime factors of N: "))
    factors = []
    for i in range(num_factors):
        f = int(input(Fore.YELLOW + f"[>] " + Style.RESET_ALL + f"Enter prime factor {i+1}: "))
        factors.append(f)
    N = 1
    for f in factors:
        N *= f
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + f"Computed modulus N = {N}\n")

    # Input number of exponents
    num_exponents = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter number of public exponents (layers of encryption): "))
    exponents = []
    for i in range(num_exponents):
        e = int(input(Fore.YELLOW + f"[>] " + Style.RESET_ALL + f"Enter exponent e{i+1}: "))
        exponents.append(e)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + f"Using exponents: {exponents}\n")

    # Compute Euler's totient φ(N)
    phi = 1
    for f in factors:
        phi *= (f - 1)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Calculated Euler's totient φ(N)\n")

    # Calculate private keys d_i
    try:
        d = tuple(inverse(e, phi) for e in exponents)
    except Exception as ex:
        print(Fore.RED + "[x] " + Style.RESET_ALL + f"Error computing modular inverses: {ex}")
        return
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Private exponents computed:")
    for i, val in enumerate(d, 1):
        print(Fore.GREEN + f"  d{i} = {val}")

    # Input ciphertext
    cipher = int(input(Fore.YELLOW + "\n[>] " + Style.RESET_ALL + "Enter ciphertext (decimal): "))
    print(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Ciphertext received.\n")

    print(Fore.CYAN + "[*] Starting layered decryption steps...\n")

    # Reverse decryption with incremental subtraction of 1 after every step except last
    current = cipher
    for i in reversed(range(num_exponents)):
        current = pow(current, d[i], N)
        print(Fore.GREEN + f"[-] " + Style.RESET_ALL + f"After decrypting with d{i+1}: {current}\n")
        if i != 0:
            current = (current - 1) % N
            print(Fore.GREEN + f"[-] " + Style.RESET_ALL + f"Subtracting 1: {current}\n")

    # current now holds M
    M = current

    # Convert M back to flag string
    flag_hex = hex(M)[2:]
    if len(flag_hex) % 2:
        flag_hex = '0' + flag_hex

    try:
        flag_bytes = bytes.fromhex(flag_hex)
        flag_str = flag_bytes.decode()
    except Exception as ex:
        flag_str = f"<Error decoding flag: {ex}>"

    print(Fore.BLUE + "______________________________________________________________\n" + Style.RESET_ALL)
    print(Fore.GREEN + "[-] " + Style.RESET_ALL + "Recovered flag: " + Fore.GREEN + flag_str + Style.RESET_ALL)
    print(Fore.BLUE + "______________________________________________________________" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
