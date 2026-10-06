# gui/ai/matcher.py
"""
Phrase matcher shared by navigation and (future) operations.

Scoring order:
  1. exact (case-insensitive)        -> 1.00
  2. all tokens of phrase present    -> 0.90
  3. Jaccard token overlap           -> ratio (threshold ~0.60)
  4. difflib SequenceMatcher         -> ratio (threshold ~0.75)

score(user_text, phrases) -> (best_score, best_phrase_or_None)
best_intent(user_text, intents) -> (best_score, best_intent_or_None)

No external dependencies. Deterministic. Cheap.
"""
import re
from difflib import SequenceMatcher


_TOKEN_RE = re.compile(r'[a-z0-9]+')


def _tokens(text):
    return set(_TOKEN_RE.findall((text or '').lower()))


def _phrase_re(phrase):
    p = re.escape(phrase.lower())
    return re.compile(r'(?<![a-z0-9])' + p + r'(?![a-z0-9])')


def score(user_text, phrases):
    """
    phrases: list[str] - example phrasings for one intent.
    Returns (best_score, best_phrase). best_phrase is None if nothing
    crossed the "good enough" threshold.
    """
    if not user_text or not phrases:
        return 0.0, None

    u_lower = user_text.lower().strip()
    u_toks = _tokens(user_text)

    best = 0.0
    best_phrase = None

    for p in phrases:
        if not p:
            continue
        p_lower = p.lower().strip()
        p_toks = _tokens(p)
        if not p_toks:
            continue

        # 1) exact string match
        if u_lower == p_lower:
            return 1.0, p

        # 2) every token of the phrase is present in the input
        #    (order-independent containment)
        if p_toks.issubset(u_toks):
            s = 0.90
            if s > best:
                best, best_phrase = s, p
            continue

        # 3) Jaccard token overlap
        inter = p_toks & u_toks
        union = p_toks | u_toks
        if union:
            j = len(inter) / len(union)
            if j >= 0.60 and j > best:
                best, best_phrase = j, p

        # 4) Fuzzy string similarity (catches typos / reordering)
        r = SequenceMatcher(None, u_lower, p_lower).ratio()
        if r >= 0.75 and r > best:
            best, best_phrase = r, p

    return best, best_phrase


def best_intent(user_text, intents):
    """
    intents: list[dict] where each dict has a 'phrases' key (list[str]).
    Returns (best_score, best_intent_dict) or (0.0, None).
    Ties go to the earlier intent in the list (so put specific ones first).
    """
    top_score = 0.0
    top_intent = None
    for intent in intents:
        s, _ = score(user_text, intent.get('phrases', []))
        if s > top_score:
            top_score = s
            top_intent = intent
    return top_score, top_intent