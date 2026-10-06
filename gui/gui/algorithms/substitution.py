# gui/algorithms/substitution.py
"""
Substitution cipher algorithms.

No Qt, no signals, no UI. Callable from ai_assistant, CLI, tests.

Public API:
    encrypt(plaintext, key)             -> str
    decrypt(ciphertext, key)            -> str
    crack(ciphertext, quadgram_path)    -> (plaintext, key_str) or raises
    validate_key(key)                   -> None or raises ValueError

A key is a 26-letter permutation of the alphabet, e.g.
'QWERTYUIOPASDFGHJKLZXCVBNM'.

  Encrypt: plaintext A->key[0], B->key[1], ...
  Decrypt: ciphertext key[0]->A, key[1]->B, ...
"""
import json
import math
import os
import random
import string
import time


_ALPHABET = string.ascii_uppercase


def validate_key(key):
    """Raise ValueError if key is not a valid 26-letter permutation."""
    if not key:
        raise ValueError("Key is empty.")
    if len(key) != 26:
        raise ValueError("Key must be exactly 26 letters.")
    if not key.isalpha():
        raise ValueError("Key must contain only letters.")
    upper = key.upper()
    if len(set(upper)) != 26:
        raise ValueError("Key must contain 26 unique letters.")
    return upper


# --------------------------------------------------------------------- #
# Encrypt / Decrypt
# --------------------------------------------------------------------- #
def encrypt(plaintext, key):
    """Encrypt plaintext using a substitution key. Returns the ciphertext."""
    key = validate_key(key)
    trans = {}
    for i, plain_letter in enumerate(_ALPHABET):
        trans[plain_letter] = key[i]
        trans[plain_letter.lower()] = key[i].lower()
    return ''.join(trans.get(c, c) for c in plaintext)


def decrypt(ciphertext, key):
    """Decrypt ciphertext using a substitution key. Returns plaintext."""
    key = validate_key(key)
    trans = {}
    for i, cipher_letter in enumerate(key):
        trans[cipher_letter] = _ALPHABET[i]
        trans[cipher_letter.lower()] = _ALPHABET[i].lower()
    return ''.join(trans.get(c, c) for c in ciphertext)


# --------------------------------------------------------------------- #
# Crack (hill climbing against quadgrams)
# --------------------------------------------------------------------- #
def crack(ciphertext, quadgram_path, max_rounds=10000, consolidate=3,
          cancelled_check=None, progress_cb=None):
    """
    Break a substitution cipher using hill climbing on quadgram fitness.

    Returns (plaintext, key_str).
    Raises FileNotFoundError if quadgram JSON is missing.
    Raises ValueError if ciphertext is too short.
    """
    def log(msg):
        if progress_cb:
            progress_cb(msg)

    if not quadgram_path or not os.path.exists(quadgram_path):
        raise FileNotFoundError(f"Quadgram file not found: {quadgram_path}")

    with open(quadgram_path, 'r') as f:
        obj = json.load(f)

    alphabet = obj["alphabet"]
    alphabet_len = len(alphabet)
    quadgrams = obj["quadgrams"]

    cipher_bin = list(_text_iterator(ciphertext, alphabet))
    if len(cipher_bin) < 4:
        raise ValueError("Ciphertext is too short (needs at least 4 alphabet characters).")

    char_positions = []
    for idx in range(alphabet_len):
        char_positions.append([i for i, x in enumerate(cipher_bin) if x == idx])

    log(f"Alphabet: {alphabet}")
    log(f"Starting hill-climbing (max {max_rounds} rounds)...")

    local_maximum = 0
    local_maximum_hit = 1
    key = list(range(alphabet_len))
    best_key = key.copy()
    nbr_keys = 0
    start_time = time.time()
    round_cntr = 0

    for round_cntr in range(max_rounds):
        if cancelled_check and cancelled_check():
            log("Cracking cancelled.")
            break

        random.shuffle(key)
        fitness, tmp_nbr_keys = _hill_climbing(
            key, cipher_bin, char_positions, quadgrams, alphabet_len,
            cancelled_check
        )
        nbr_keys += tmp_nbr_keys

        if fitness > local_maximum:
            local_maximum = fitness
            local_maximum_hit = 1
            best_key = key.copy()
        elif fitness == local_maximum:
            local_maximum_hit += 1
            if local_maximum_hit >= consolidate:
                break

    key_str = ''.join(alphabet[x] for x in best_key)
    plaintext = _decrypt_with_key(ciphertext, best_key, alphabet)

    seconds = time.time() - start_time
    log(f"Solved in {seconds:.2f}s ({round_cntr + 1} rounds, "
        f"{nbr_keys:,} keys tried).")

    return plaintext, key_str


# --------------------------------------------------------------------- #
# Crack internals
# --------------------------------------------------------------------- #
def _text_iterator(txt, alphabet):
    trans = {val: key for key, val in enumerate(alphabet.lower())}
    for char in txt.lower():
        val = trans.get(char)
        if val is not None:
            yield val


def _hill_climbing(key, cipher_bin, char_positions, quadgrams, alphabet_len,
                   cancelled_check):
    plaintext = [key.index(idx) for idx in cipher_bin]
    nbr_keys = 0
    max_fitness = 0
    better_key = True

    while better_key:
        if cancelled_check and cancelled_check():
            return max_fitness, nbr_keys
        better_key = False
        for idx1 in range(alphabet_len - 1):
            for idx2 in range(idx1 + 1, alphabet_len):
                ch1 = key[idx1]
                ch2 = key[idx2]

                for idx in char_positions[ch1]:
                    plaintext[idx] = idx2
                for idx in char_positions[ch2]:
                    plaintext[idx] = idx1

                nbr_keys += 1
                tmp_fitness = 0
                quad_idx = (plaintext[0] << 10) + (plaintext[1] << 5) + plaintext[2]
                for char in plaintext[3:]:
                    quad_idx = ((quad_idx & 0x7FFF) << 5) + char
                    tmp_fitness += quadgrams[quad_idx]

                if tmp_fitness > max_fitness:
                    max_fitness = tmp_fitness
                    better_key = True
                    key[idx1] = ch2
                    key[idx2] = ch1
                else:
                    for idx in char_positions[ch1]:
                        plaintext[idx] = idx1
                    for idx in char_positions[ch2]:
                        plaintext[idx] = idx2

    return max_fitness, nbr_keys


def _decrypt_with_key(ciphertext, key, alphabet):
    camel_key = alphabet.upper() + alphabet.lower()
    key_upper = ''.join(alphabet[x].upper() for x in key)
    key_lower = ''.join(alphabet[x].lower() for x in key)
    camel_trans = key_upper + key_lower
    trans = str.maketrans(camel_trans, camel_key)
    return ciphertext.translate(trans)