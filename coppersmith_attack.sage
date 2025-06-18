# coppersmith_attack.sage

import sys

# Read inputs
lines = [line.strip() for line in sys.stdin.readlines()]
n = Integer(lines[0])
e = Integer(lines[1])
c = Integer(lines[2])
known = lines[3].replace("X", "\x00")

# Convert known part to integer
M = Integer(known.encode("hex"), 16)

# Create polynomial f(x) = (M + x)^e - c
P.<x> = PolynomialRing(Zmod(n))
f = (M + x)^e - c
f = f.monic()

# Try to find small root
roots = f.small_roots(epsilon=1/13)

# If found, convert to bytes
if roots:
    m = roots[0]
    recovered = M + m
    hex_data = hex(recovered)[2:]
    if len(hex_data) % 2:
        hex_data = "0" + hex_data
    print(bytearray.fromhex(hex_data).decode("utf-8", errors="replace"))
else:
    print("[!] No root found.")
