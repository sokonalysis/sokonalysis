# gui/search_registry.py
_search_index = {}

def register_options(category, options):
    if category not in _search_index:
        _search_index[category] = []
    for opt in options:
        name = opt[0] if isinstance(opt, tuple) else opt
        desc = opt[1] if isinstance(opt, tuple) and len(opt) > 1 else ""
        _search_index[category].append((name, desc))

def get_all_options():
    return dict(_search_index)