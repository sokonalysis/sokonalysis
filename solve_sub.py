import random
import math
import string

# Quadgram frequencies from an English corpus, normalized and log-scored
# (You can get a file quadgrams.txt online; for brevity, I'll include a small snippet)
QUADGRAMS = {
    'TION': 0.00084,
    'THER': 0.00076,
    'WITH': 0.00072,
    'HERE': 0.00068,
    'OULD': 0.00065,
    # ... (you'll want a big list in practice)
}

TOTAL_QUADGRAMS = sum(QUADGRAMS.values())
LOG_TOTAL = math.log10(TOTAL_QUADGRAMS)

# Precompute log probabilities for scoring
LOG_PROBS = {k: math.log10(v) - LOG_TOTAL for k, v in QUADGRAMS.items()}
MIN_LOG_PROB = math.log10(0.01 / TOTAL_QUADGRAMS)  # for unseen quadgrams

def score_text(text):
    score = 0
    text = text.upper()
    for i in range(len(text) - 3):
        quad = text[i:i+4]
        if quad in LOG_PROBS:
            score += LOG_PROBS[quad]
        else:
            score += MIN_LOG_PROB
    return score

def decrypt(text, key_map):
    decrypted = []
    for c in text:
        if c.lower() in key_map:
            new_char = key_map[c.lower()]
            decrypted.append(new_char.upper() if c.isupper() else new_char)
        else:
            decrypted.append(c)
    return ''.join(decrypted)

def random_key():
    letters = list(string.ascii_lowercase)
    random.shuffle(letters)
    return letters

def key_map_from_list(key_list):
    return {chr(ord('a') + i): key_list[i] for i in range(26)}

def hill_climb(ciphertext, max_iters=10000):
    best_key = random_key()
    best_map = key_map_from_list(best_key)
    best_score = score_text(decrypt(ciphertext, best_map))

    for _ in range(max_iters):
        # swap two letters in key
        new_key = best_key[:]
        i1, i2 = random.sample(range(26), 2)
        new_key[i1], new_key[i2] = new_key[i2], new_key[i1]
        new_map = key_map_from_list(new_key)
        new_score = score_text(decrypt(ciphertext, new_map))

        if new_score > best_score:
            best_key = new_key
            best_map = new_map
            best_score = new_score

    return decrypt(ciphertext, best_map), best_map

if __name__ == "__main__":
    ciphertext = input("Enter ciphertext: ")
    plaintext, key = hill_climb(ciphertext)
    print("Best decryption:\n", plaintext)
    print("Key mapping (a->letter):")
    for k, v in sorted(key.items()):
        print(f"{k} -> {v}")
