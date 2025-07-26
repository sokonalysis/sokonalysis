from Crypto.Util.number import *
from colorama import Fore, Style, init
import gmpy2

init(autoreset=True)

def fermat_factor(n):
    print(Fore.GREEN + "[*]" + Style.RESET_ALL + " Trying Fermat's factorization on n...")
    a = gmpy2.isqrt(n)
    if a * a < n:
        a += 1
    b2 = a * a - n
    tries = 0
    while not gmpy2.is_square(b2):
        a += 1
        b2 = a * a - n
        tries += 1
        if tries % 1000 == 0:
            print(Fore.YELLOW + f"  [+] Tried {tries} values...")
    b = gmpy2.isqrt(b2)
    p = a - b
    q = a + b
    print(Fore.GREEN + f"[-]" + Style.RESET_ALL + " Successfully factored n:")
    print(Fore.CYAN + f"    p = {p}")
    print(Fore.CYAN + f"    q = {q}")
    return int(p), int(q)

def main():
    n = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter modulus n: "))
    e = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter public exponent e: "))
    c = int(input(Fore.YELLOW + "[>] " + Style.RESET_ALL + "Enter ciphertext c: "))

    p, q = fermat_factor(n)

    phi = (p - 1) * (q - 1)
    d = inverse(e, phi)

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + " Decrypting ciphertext...")
    m = pow(c, d, n)
    try:
        flag = long_to_bytes(m).decode()
        print(Fore.BLUE + "_________________________________________________________________\n" + Style.RESET_ALL)
        print(Fore.GREEN + "[-]" + Style.RESET_ALL + " Decrypted flag: " + Fore.GREEN + flag + Style.RESET_ALL)
        print(Fore.BLUE + "_________________________________________________________________" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "[x]" + Style.RESET_ALL + " Failed to decode message as UTF-8. Raw output:")
        print(m)

if __name__ == "__main__":
    main()
