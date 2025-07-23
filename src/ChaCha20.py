# attack.py
# Run this script from main.cpp when the user selects the attack option

def hex_to_bytes(hex_str):
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        print("[x] Invalid hex input.")
        exit(1)

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def main():
    print("[>] Enter the IV (hex): ")
    iv_hex = input().strip()

    print("[>] Enter the ciphertext of the known message (hex):")
    ciphertext1_hex = input().strip()

    print("[>] Enter the ciphertext of the FLAG (hex):")
    ciphertext2_hex = input().strip()

    ciphertext1 = hex_to_bytes(ciphertext1_hex)
    ciphertext2 = hex_to_bytes(ciphertext2_hex)

    print("\n[>] Enter the known plaintext message (as text):")
    user_input = input().encode()

    if len(user_input) != len(ciphertext1):
        print(f"[x] Your input must be {len(ciphertext1)} bytes to match ciphertext length.")
        return

    keystream = xor_bytes(ciphertext1, user_input)
    recovered_flag = xor_bytes(ciphertext2, keystream[:len(ciphertext2)])

    print("\n[-] Recovered FLAG:")
    try:
        print(recovered_flag.decode())
    except UnicodeDecodeError:
        print("[*] FLAG (raw bytes):", recovered_flag)

if __name__ == "__main__":
    main()
