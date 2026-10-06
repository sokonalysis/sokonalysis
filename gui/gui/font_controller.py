# gui/font_controller.py
"""
Centralized font size controller for all pages.
"""
from gui.layout_manager import layout_manager


class FontController:
    """Centralized font size control."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_font_sizes(self):
        """Get font sizes based on current layout."""
        return {
            "title": max(12, layout_manager.get_scaled_font_size(16)),
            "subtitle": max(9, layout_manager.get_scaled_font_size(11)),
            "heading": max(18, layout_manager.get_scaled_font_size(24)),
            "body": max(11, layout_manager.get_scaled_font_size(14)),
            "small": max(9, layout_manager.get_scaled_font_size(11)),
            "large": max(16, layout_manager.get_scaled_font_size(22)),
            "mono": max(11, layout_manager.get_scaled_font_size(14)),
            "button": max(11, layout_manager.get_scaled_font_size(14)),
            "input": max(11, layout_manager.get_scaled_font_size(14)),
        }


font_controller = FontController()