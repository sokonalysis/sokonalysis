# gui/ai/links.py
"""
Tool link lookup for the chat.

Passes (in order):
  1. Exact leaf name match        (e.g. "base64" -> Base64)
  2. Fuzzy leaf name match        (e.g. "base 64" -> Base64)
  3. Keyword match against parent
     tools that have children     (e.g. "sha" -> SHA Hash + its children)
  4. Keyword match against
     a category name              (e.g. "ctf" -> all CTF tools as links)
"""

from gui.ai import matcher
from gui.search_registry import get_all_options
from gui.category_pages import CATEGORY_DESCRIPTIONS


_LINK_COLOR = '#2563eb'


def lookup(query, options_index):
    if not query or not options_index:
        return None
    q = query.strip().lower()
    if not q:
        return None

    # --- 1) Exact leaf name
    if q in options_index:
        return _format_single(options_index[q])

    # --- 2) Fuzzy leaf name
    best = None
    best_score = 0.0
    for name_lower, info in options_index.items():
        s, _ = matcher.score(q, [name_lower])
        if s > best_score:
            best_score = s
            best = info
    if best is not None and best_score >= 0.80:
        # If another candidate is within 0.05, show a multi-match list
        close = [info for nl, info in options_index.items()
                 if matcher.score(q, [nl])[0] >= best_score - 0.05]
        if len(close) > 1:
            return _format_multi(close)
        return _format_single(best)

    # --- 3) Parent tool that has children (e.g. "sha")
    parent = _match_parent(q, options_index)
    if parent:
        return _format_parent(parent)

    # --- 4) Category name (e.g. "ctf", "hashing")
    cat = _match_category(q)
    if cat:
        return _format_category(cat)

    return None


# --------------------------------------------------------------------- #
# Matching helpers
# --------------------------------------------------------------------- #
def _match_parent(q, options_index):
    """
    Find a parent tool whose name word or full name matches q.
    A parent is an option with children.
    """
    # Build word -> parent mapping once
    word_hits = []
    for name_lower, info in options_index.items():
        children = info.get('children') or []
        if not children:
            continue

        name_words = name_lower.replace('-', ' ').split()

        # Whole-name match
        if q == name_lower:
            return info
        # Single word match
        if q in name_words:
            word_hits.append((len(info['name']), info))

    if word_hits:
        # Prefer the shortest parent name so "sha" picks "SHA Hash" over
        # some longer unrelated name
        word_hits.sort()
        return word_hits[0][1]

    return None


def _match_category(q):
    """Return the real-case category name if q matches one, else None."""
    try:
        opts = get_all_options()
    except Exception:
        return None
    # Single-word queries only, to avoid "hash this md5" matching "Hashing"
    if len(q.split()) > 2:
        return None
    for cat in opts.keys():
        cat_lower = cat.lower()
        if q == cat_lower or q in cat_lower.split():
            return cat
    return None


# --------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------- #
def _link(name):
    encoded = name.replace(' ', '%20')
    return (
        f"<a href=\"http://sokonalysis/option/{encoded}/none\" "
        f"style=\"color: {_LINK_COLOR}; text-decoration: none;\">{name}</a>"
    )


def _link_bold(name):
    encoded = name.replace(' ', '%20')
    return (
        f"<a href=\"http://sokonalysis/option/{encoded}/none\" "
        f"style=\"color: {_LINK_COLOR}; font-size:14px; font-weight:600; "
        f"text-decoration: none;\">{name}</a>"
    )


def _format_single(info):
    response = (
        f"{_link_bold(info['name'])}<br><br>"
        f"<b>Category:</b> {info['category']}<br>"
        f"<b>Description:</b> {info['description']}"
    )
    children = info.get('children') or []
    if children:
        response += "<br><br><b>Available options:</b><br>"
        for child in children:
            response += f"- {_link(child['name'])}: {child['description']}<br>"
    return response


def _format_parent(info):
    response = (
        f"{_link_bold(info['name'])}<br><br>"
        f"<b>Category:</b> {info['category']}<br>"
        f"<b>Description:</b> {info['description']}<br><br>"
        f"<b>Available options:</b><br>"
    )
    for child in info.get('children', []):
        response += f"- {_link(child['name'])}: {child['description']}<br>"
    return response


def _format_category(cat_name):
    try:
        opts = get_all_options()
    except Exception:
        return None

    real = None
    for cat in opts.keys():
        if cat.lower() == cat_name.lower():
            real = cat
            break
    if real is None:
        return None

    desc = CATEGORY_DESCRIPTIONS.get(real, "A collection of tools.")
    response = f"<b>{real}</b><br><br>{desc}<br><br><b>Tools:</b><br>"
    for opt in opts[real]:
        name = opt[0] if isinstance(opt, tuple) else opt
        o_desc = opt[1] if isinstance(opt, tuple) and len(opt) > 1 else ""
        if o_desc:
            response += f"- {_link(name)}: {o_desc}<br>"
        else:
            response += f"- {_link(name)}<br>"
    return response


def _format_multi(matches):
    response = f"Found <b>{len(matches)} matches</b>:<br><br>"
    for i, info in enumerate(matches[:5], 1):
        response += f"{i}. {_link(info['name'])} ({info['category']})<br>"
    return response