from sympy import factorint, discrete_log
from Crypto.Util.number import long_to_bytes
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from hashlib import sha256

def main():
    print("[>] Enter p:")
    p = int(input().strip())

    print("[>] Enter g:")
    g = int(input().strip())

    print("[>] Enter A:")
    A = int(input().strip())

    print("[>] Enter B:")
    B = int(input().strip())

    print("[>] Enter encrypted flag (hex):")
    encrypted_flag_hex = input().strip()

    print("[*] Factoring p-1...")
    factors = factorint(p-1)
    print(f"[*] Factors of p-1: {factors}")

    # Find order q of g
    q = None
    for f in factors:
        if pow(g, f, p) == 1:
            q = f
            print(f"[*] Found order q of g: {q}")
            break

    if q is None:
        print("[x] Could not find order of g.")
        return

    print("[*] Computing discrete log a such that g^a = A mod p...")
    a = discrete_log(p, A, g, order=q)
    print(f"[*] Discrete log a = {a}")

    print("[*] Computing shared secret ss = B^a mod p...")
    ss = pow(B, a, p)

    print("[*] Deriving AES key from shared secret...")
    key = sha256(long_to_bytes(ss)).digest()[:16]

    print("[*] Decrypting flag ciphertext...")
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted_flag = bytes.fromhex(encrypted_flag_hex)
    plaintext_padded = cipher.decrypt(encrypted_flag)
    plaintext = unpad(plaintext_padded, 16)

    print("[-] Flag:", plaintext.decode())

if __name__ == "__main__":
    main()
