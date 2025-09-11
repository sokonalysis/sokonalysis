#!/usr/bin/env python3

import base64
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

BASE64_STD = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
BASE64_URL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
KEEP_CHARS = set(BASE64_STD + BASE64_URL + "=")

def normalize_b64(s):
    """Clean input: remove junk, normalize URL-safe, strip whitespace."""
    s = s.strip().replace("\n", "").replace("\r", "")
    s = "".join(ch for ch in s if ch in KEEP_CHARS)
    s = s.replace("-", "+").replace("_", "/")
    return s

def try_decode_with_padding(s):
    """Try decoding with up to 3 padding variations."""
    for extra_pad in range(0, 4):
        candidate = s + ("=" * extra_pad)
        try:
            decoded = base64.b64decode(candidate, validate=True)
            return decoded, candidate
        except Exception:
            continue
    return None, None

def printable_ratio(b):
    if not b:
        return 0.0
    good = sum(1 for x in b if 32 <= x <= 126 or x in (9, 10, 13))
    return good / len(b)

def likely_text_score(b):
    if b is None:
        return 0.0
    ratio = printable_ratio(b)
    s = b.decode("utf-8", errors="ignore").lower()
    boost = 0.0
    if "flag{" in s or "ctf{" in s:
        boost += 2.0
    if s.startswith("{") and "}" in s:
        boost += 1.5  # boost possible flag structure
    return ratio + boost

def try_strategies(orig):
    """Try direct, cleaned, and single-deletion repairs."""
    s0 = orig
    candidates = []

    # Direct
    decoded, used = try_decode_with_padding(s0)
    if decoded: candidates.append(("direct", used, decoded, likely_text_score(decoded)))

    # Normalized
    s_norm = normalize_b64(s0)
    if s_norm != s0:
        decoded, used = try_decode_with_padding(s_norm)
        if decoded: candidates.append(("cleaned", used, decoded, likely_text_score(decoded)))

    # Deletion repair
    for i in range(len(s_norm)):
        s2 = s_norm[:i] + s_norm[i+1:]
        decoded, used = try_decode_with_padding(s2)
        if decoded:
            candidates.append((f"delete@{i}", used, decoded, likely_text_score(decoded)))

    return sorted(candidates, key=lambda x: -x[3])

def present_results(candidates, topn=5):
    if not candidates:
        print(Fore.RED + "[x] No valid candidates found.\n")
        return

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + f" Top {min(topn, len(candidates))} candidates:\n")
    for idx, (method, used, decoded, score) in enumerate(candidates[:topn], 1):
        text = decoded.decode("utf-8", errors="replace")
        printable_pct = printable_ratio(decoded) * 100
        print(Fore.BLUE + "─" * 60 + Style.RESET_ALL)
        print(Fore.YELLOW + f"{idx})" + Style.RESET_ALL +
              f" method: {Fore.CYAN}{method}{Style.RESET_ALL}  | " +
              f"score: {Fore.MAGENTA}{score:.3f}{Style.RESET_ALL}  | " +
              f"printable: {Fore.GREEN}{printable_pct:.1f}%")
        print(Fore.RED + "   repaired_b64:" + Style.RESET_ALL + f" {used}")
        print(Fore.GREEN + "   decoded_text:" + Style.RESET_ALL + f" {text}")
    print(Fore.BLUE + "─" * 60 + Style.RESET_ALL)

def main():
    # Exact input style you wanted
    inp = input(Fore.YELLOW + "[>] " + Style.RESET_ALL +
                "Paste the cipher (may be corrupted): ").strip()
    if not inp:
        print(Fore.RED + "[x] Error:" + Style.RESET_ALL + " No input provided.")
        sys.exit(1)

    print(Fore.GREEN + "\n[*]" + Style.RESET_ALL + " Trying automatic recovery...\n")
    candidates = try_strategies(inp)
    present_results(candidates)

if __name__ == "__main__":
    main()
