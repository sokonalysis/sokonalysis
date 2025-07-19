import sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import random

def hex_to_bytes(hex_str):
    return bytes.fromhex(hex_str)

def main():
    if len(sys.argv) != 2:
        print("Usage: python aes_decrypt.py <hex_encrypted_message>")
        sys.exit(1)

    hex_input = sys.argv[1]

    try:
        encrypted_message = hex_to_bytes(hex_input)
    except Exception as e:
        print(f"Error: Invalid hex input: {e}")
        sys.exit(1)

    random.seed(123456)
    key = random.randbytes(16)

    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_padded = cipher.decrypt(encrypted_message)

    try:
        decrypted = unpad(decrypted_padded, AES.block_size)
    except ValueError as e:
        print(f"Error: Padding error: {e}")
        sys.exit(1)

    print(decrypted.decode('utf-8', errors='replace'))

if __name__ == "__main__":
    main()
