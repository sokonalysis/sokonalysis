# gui/ai/navigation.py
"""
Chat navigation, dataset-driven.
"""

import json
import os

from gui.search_registry import get_all_options
from gui.category_pages import CATEGORY_DESCRIPTIONS
from gui.ai import matcher


_DATASET = None
_THRESHOLD = 0.60
_LINK_COLOR = '#2563eb'


def _load_dataset():
    global _DATASET
    if _DATASET is not None:
        return _DATASET
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'navigation_dataset.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {"intents": []}
    _DATASET = data.get('intents', [])
    return _DATASET


def route(question):
    if not question:
        return None
    q = question.strip()

    intents = _load_dataset()
    score, intent = matcher.best_intent(q, intents)
    if intent is not None and score >= _THRESHOLD:
        reply = _resolve_reply(intent.get('reply'))
        if reply is not None:
            return (intent.get('action'), intent.get('payload') or '', reply)

    return None


def _resolve_reply(reply):
    if reply is None:
        return None
    if reply == '__CATEGORIES__':
        return _format_category_list()
    if isinstance(reply, str) and reply.startswith('__CATEGORY_DETAIL:'):
        key = reply[len('__CATEGORY_DETAIL:'):]
        if key.endswith('__'):
            key = key[:-2]
        return _format_category_detail(key)
    return reply


def _option_link(name):
    encoded = name.replace(' ', '%20')
    return (
        f"<a href=\"http://sokonalysis/option/{encoded}/none\" "
        f"style=\"color: {_LINK_COLOR}; text-decoration: none;\">{name}</a>"
    )


def _format_category_list():
    try:
        opts = get_all_options()
    except Exception:
        opts = {}
    lines = ["<b>Available categories:</b><br><br>"]
    for i, (cat, tools) in enumerate(opts.items(), 1):
        lines.append(f"{i}. <b>{cat}</b> ({len(tools)} tools)<br>")
    return ''.join(lines)


def _format_category_detail(cat_key):
    try:
        opts = get_all_options()
    except Exception:
        return None
    match = None
    for cat in opts.keys():
        if cat.lower() == cat_key.lower():
            match = cat
            break
    if match is None:
        return None
    desc = CATEGORY_DESCRIPTIONS.get(match, "A collection of tools.")
    lines = [f"<b>{match}</b><br><br>{desc}<br><br><b>Tools:</b><br>"]
    for opt in opts[match][:10]:
        name = opt[0] if isinstance(opt, tuple) else opt
        lines.append(f"- {_option_link(name)}<br>")
    remaining = len(opts[match]) - 10
    if remaining > 0:
        lines.append(f"<i>...and {remaining} more</i><br>")
    return ''.join(lines)