# gui/user_preferences.py
"""
Persistent user preferences - remembers ALL settings across sessions.
"""
import json
import os
import sys


class UserPreferences:
    """Manages user preferences with persistent storage."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._prefs = {
            # Wordlist & cracking
            "wordlist_path": "",
            "split_parts": 4,
            
            # Quadgram/JSON
            "json_path": "",
            
            # Theme
            "theme": "dark",
            "theme_name": "Catppuccin Mocha",
            
            # Layout
            "layout": "default",
            "last_toolbar_area": "top",
            
            # Window
            "window_geometry": None,
            "window_maximized": False,
            
            # AI Assistant
            "ai_assistant_open": False,
            "ai_assistant_visible": False,
            
            # Favorites
            "favorite_tools": [],
            "recent_tools": [],
            "last_category": "",
            "last_tool": "",
            
            # Search
            "search_history": [],
            "last_search_query": "",
            
            # John the Ripper
            "john_path": "",
            "john_wordlist_path": "",
            "john_rules": "",
            
            # Customization
            "header_position": "top",
            "footer_visible": True,
            
            # Advanced
            "auto_start_cracking": False,
            "save_results": True,
            "results_path": "",
        }
        self._config_dir = self._get_config_dir()
        self._config_file = os.path.join(self._config_dir, "preferences.json")
        self._load()
    
    def _get_config_dir(self):
        """Get the config directory path."""
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
        elif sys.platform == 'darwin':
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:
            base = os.environ.get('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
        
        config_dir = os.path.join(base, 'sokonalysis')
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    def _load(self):
        """Load preferences from disk."""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self._prefs.update(saved)
        except:
            pass
    
    def _save(self):
        """Save preferences to disk."""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._prefs, f, indent=2, default=str)
        except:
            pass
    
    def get(self, key, default=None):
        return self._prefs.get(key, default)
    
    def set(self, key, value):
        self._prefs[key] = value
        self._save()
    
    # ===== WORDLIST =====
    @property
    def wordlist_path(self):
        return self._prefs.get("wordlist_path", "")
    
    @property
    def split_parts(self):
        return self._prefs.get("split_parts", 4)
    
    def set_wordlist(self, path, split_parts=4):
        self._prefs["wordlist_path"] = path
        self._prefs["split_parts"] = split_parts
        self._save()
    
    # ===== QUADGRAM/JSON =====
    @property
    def json_path(self):
        return self._prefs.get("json_path", "")
    
    def set_json_path(self, path):
        self._prefs["json_path"] = path
        self._save()
    
    # ===== THEME =====
    @property
    def theme(self):
        return self._prefs.get("theme", "dark")
    
    @property
    def theme_name(self):
        return self._prefs.get("theme_name", "Catppuccin Mocha")
    
    def set_theme(self, theme, name="Catppuccin Mocha"):
        self._prefs["theme"] = theme
        self._prefs["theme_name"] = name
        self._save()
    
    # ===== LAYOUT =====
    @property
    def layout(self):
        return self._prefs.get("layout", "default")
    
    def set_layout(self, layout):
        self._prefs["layout"] = layout
        self._save()
    
    # ===== TOOLBAR =====
    @property
    def last_toolbar_area(self):
        return self._prefs.get("last_toolbar_area", "top")
    
    @property
    def header_position(self):
        return self._prefs.get("header_position", "top")
    
    def set_toolbar_area(self, area):
        self._prefs["last_toolbar_area"] = area
        self._prefs["header_position"] = area
        self._save()
    
    # ===== WINDOW =====
    @property
    def window_geometry(self):
        return self._prefs.get("window_geometry", None)
    
    @property
    def window_maximized(self):
        return self._prefs.get("window_maximized", False)
    
    def set_window_geometry(self, geometry):
        self._prefs["window_geometry"] = geometry
        self._save()
    
    def set_window_maximized(self, maximized):
        self._prefs["window_maximized"] = maximized
        self._save()
    
    # ===== FOOTER =====
    @property
    def footer_visible(self):
        return self._prefs.get("footer_visible", True)
    
    def set_footer_visible(self, visible):
        self._prefs["footer_visible"] = visible
        self._save()
    
    # ===== AI ASSISTANT =====
    @property
    def ai_assistant_open(self):
        return self._prefs.get("ai_assistant_open", False)
    
    @property
    def ai_assistant_visible(self):
        return self._prefs.get("ai_assistant_visible", False)
    
    def set_ai_assistant_state(self, open_state, visible):
        self._prefs["ai_assistant_open"] = open_state
        self._prefs["ai_assistant_visible"] = visible
        self._save()
    
    # ===== FAVORITES =====
    @property
    def favorite_tools(self):
        return self._prefs.get("favorite_tools", [])
    
    def add_favorite_tool(self, tool_name):
        tools = self._prefs.get("favorite_tools", [])
        if tool_name not in tools:
            tools.append(tool_name)
            self._prefs["favorite_tools"] = tools[:20]
            self._save()
    
    def remove_favorite_tool(self, tool_name):
        tools = self._prefs.get("favorite_tools", [])
        if tool_name in tools:
            tools.remove(tool_name)
            self._prefs["favorite_tools"] = tools
            self._save()
    
    # ===== RECENT =====
    @property
    def recent_tools(self):
        return self._prefs.get("recent_tools", [])
    
    @property
    def last_category(self):
        return self._prefs.get("last_category", "")
    
    @property
    def last_tool(self):
        return self._prefs.get("last_tool", "")
    
    def add_recent_tool(self, tool_name):
        tools = self._prefs.get("recent_tools", [])
        if tool_name in tools:
            tools.remove(tool_name)
        tools.insert(0, tool_name)
        self._prefs["recent_tools"] = tools[:10]
        self._save()
    
    def set_last_category(self, category):
        self._prefs["last_category"] = category
        self._save()
    
    def set_last_tool(self, tool):
        self._prefs["last_tool"] = tool
        self._save()
    
    # ===== SEARCH =====
    @property
    def search_history(self):
        return self._prefs.get("search_history", [])
    
    @property
    def last_search_query(self):
        return self._prefs.get("last_search_query", "")
    
    def add_search_history(self, query):
        history = self._prefs.get("search_history", [])
        if query in history:
            history.remove(query)
        history.insert(0, query)
        self._prefs["search_history"] = history[:20]
        self._prefs["last_search_query"] = query
        self._save()
    
    # ===== JOHN THE RIPPER =====
    @property
    def john_path(self):
        return self._prefs.get("john_path", "")
    
    @property
    def john_wordlist_path(self):
        return self._prefs.get("john_wordlist_path", "")
    
    @property
    def john_rules(self):
        return self._prefs.get("john_rules", "")
    
    def set_john_config(self, path="", wordlist="", rules=""):
        if path:
            self._prefs["john_path"] = path
        if wordlist:
            self._prefs["john_wordlist_path"] = wordlist
        if rules:
            self._prefs["john_rules"] = rules
        self._save()
    
    # ===== ADVANCED =====
    @property
    def auto_start_cracking(self):
        return self._prefs.get("auto_start_cracking", False)
    
    @property
    def save_results(self):
        return self._prefs.get("save_results", True)
    
    @property
    def results_path(self):
        return self._prefs.get("results_path", "")
    
    def set_results_path(self, path):
        self._prefs["results_path"] = path
        self._save()


# Global singleton
user_prefs = UserPreferences()