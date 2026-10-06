# gui/layout_manager.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class LayoutManager(QObject):
    """Central layout manager - single source of truth for layout state."""
    
    layout_changed = Signal(str)
    
    LAYOUTS = {
        "compact": {
            "width_pct": 0.60,
            "height_pct": 0.65,
            "cards_per_row": 3,
            "grid_cards_per_row": 3,
            "card_width": 295,
            "card_height": 140,
            "font_scale": 0.80,
            "margin_scale": 0.70,
            "spacing_scale": 0.70,
            "button_scale": 0.80,
            "input_scale": 0.80,
            "icon_scale": 0.80,
            "title_scale": 0.80,
        },
        "default": {
            "width_pct": 0.80,
            "height_pct": 0.80,
            "cards_per_row": 3,
            "grid_cards_per_row": 3,
            "card_width": 380,
            "card_height": 180,
            "font_scale": 1.0,
            "margin_scale": 1.0,
            "spacing_scale": 1.0,
            "button_scale": 1.0,
            "input_scale": 1.0,
            "icon_scale": 1.0,
            "title_scale": 1.0,
        },
        "wide": {
            "width_pct": 1.0,
            "height_pct": 1.0,
            "cards_per_row": 4,
            "grid_cards_per_row": 4,
            "card_width": 400,
            "card_height": 190,
            "font_scale": 1.4,        # Changed from 1.15
            "margin_scale": 1.30,
            "spacing_scale": 1.30,
            "button_scale": 1.4,      # Changed from 1.20
            "input_scale": 1.4,       # Changed from 1.20
            "icon_scale": 1.20,
            "title_scale": 1.4,       # Changed from 1.20
        },
    }
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current = "default"
        return cls._instance
    
    @property
    def current(self):
        return self._current
    
    @property
    def current_config(self):
        return self.LAYOUTS[self._current]
    
    def set_layout(self, layout_type):
        if layout_type in self.LAYOUTS:
            self._current = layout_type
            self.layout_changed.emit(layout_type)
    
    def _get_screen_size(self):
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                return geo.width(), geo.height()
        return 1920, 1080
    
    def _get_dpi_scale(self):
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                dpi = screen.logicalDotsPerInch()
                scale = dpi / 96.0
                return max(0.8, min(2.0, scale))
        return 1.0
    
    def get_window_size(self):
        screen_w, screen_h = self._get_screen_size()
        config = self.LAYOUTS[self._current]
        
        if self._current == "wide":
            return screen_w, screen_h
        
        width = int(screen_w * config["width_pct"])
        height = int(screen_h * config["height_pct"])
        
        min_w = 960 if self._current == "default" else 800
        min_h = 640 if self._current == "default" else 550
        
        return max(width, min_w), max(height, min_h)
    
    def get_window_position(self):
        screen_w, screen_h = self._get_screen_size()
        width, height = self.get_window_size()
        
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        
        return x, y
    
    def get_minimum_size(self):
        if self._current == "compact":
            return 800, 550
        return 960, 640
    
    def cards_per_row(self):
        return self.current_config["cards_per_row"]
    
    def grid_cards_per_row(self):
        return self.current_config["grid_cards_per_row"]
    
    def card_size(self):
        config = self.LAYOUTS[self._current]
        dpi_scale = self._get_dpi_scale()
        
        width = int(config["card_width"] * dpi_scale)
        height = int(config["card_height"] * dpi_scale)
        
        width = max(200, width)
        height = max(120, height)
        
        return width, height
    
    # ===== SCALING METHODS =====
    
    def font_scale(self):
        return self.current_config["font_scale"]
    
    def margin_scale(self):
        return self.current_config["margin_scale"]
    
    def spacing_scale(self):
        return self.current_config["spacing_scale"]
    
    def button_scale(self):
        return self.current_config["button_scale"]
    
    def input_scale(self):
        return self.current_config["input_scale"]
    
    def icon_scale(self):
        return self.current_config["icon_scale"]
    
    def title_scale(self):
        return self.current_config["title_scale"]
    
    def get_scaled_value(self, base_value, scale_type="font_scale"):
        scale = self.current_config.get(scale_type, 1.0)
        dpi_scale = self._get_dpi_scale()
        return int(base_value * scale * dpi_scale)
    
    def get_scaled_margins(self, base_margins):
        scale = self.margin_scale()
        dpi_scale = self._get_dpi_scale()
        return tuple(int(m * scale * dpi_scale) for m in base_margins)
    
    def get_scaled_font_size(self, base_size):
        scale = self.font_scale()
        dpi_scale = self._get_dpi_scale()
        return int(base_size * scale * dpi_scale)
    
    def get_scaled_spacing(self, base_spacing):
        scale = self.spacing_scale()
        dpi_scale = self._get_dpi_scale()
        return int(base_spacing * scale * dpi_scale)


# Global singleton
layout_manager = LayoutManager()