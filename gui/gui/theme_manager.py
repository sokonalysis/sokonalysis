# gui/theme_manager.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from gui.layout_manager import layout_manager


class ThemeManager(QObject):
    """Professional theme management."""
    
    theme_changed = Signal(str)
    
    LIGHT = {
        "name": "Light",
        "base": "#ffffff",
        "base_alt": "#f8f9fa",
        "crust": "#f1f3f5",
        "surface0": "#e9ecef",
        "surface1": "#dee2e6",
        "surface2": "#adb5bd",
        "text": "#000000",
        "text_secondary": "#495057",
        "text_tertiary": "#6c757d",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_light": "#dbeafe",
        "accent_text": "#ffffff",
        "border": "#ced4da",
        "border_focus": "#2563eb",
        "hover": "#f1f3f5",
        "hover_accent": "#dbeafe",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
        "shadow": "rgba(0, 0, 0, 0.08)",
        "overlay": "rgba(0, 0, 0, 0.03)",
        # Matplotlib specific
        "mpl_bar_color": "#2563eb",
        "mpl_bar_alpha": 0.85,
        "mpl_grid_alpha": 0.3,
    }
    
    DARK = {
        "name": "Dark",
        "base": "#121212",
        "base_alt": "#1a1a1a",
        "crust": "#1e1e1e",
        "surface0": "#252525",
        "surface1": "#2d2d2d",
        "surface2": "#3d3d3d",
        "text": "#e4e4e4",
        "text_secondary": "#a0a0a0",
        "text_tertiary": "#6b6b6b",
        "accent": "#8ab4f8",
        "accent_hover": "#a8c7fa",
        "accent_light": "#1a3a5c",
        "accent_text": "#121212",
        "border": "#2d2d2d",
        "border_focus": "#8ab4f8",
        "hover": "#2a2a2a",
        "hover_accent": "#252525",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "shadow": "rgba(0, 0, 0, 0.5)",
        "overlay": "rgba(255, 255, 255, 0.02)",
        # Matplotlib specific
        "mpl_bar_color": "#4ade80",
        "mpl_bar_alpha": 0.85,
        "mpl_grid_alpha": 0.3,
    }
    
    def __init__(self):
        super().__init__()
        self._is_dark = False
        self._current = self.LIGHT
        self._apply_matplotlib_theme()
        
        # Connect layout changes to update matplotlib fonts
        layout_manager.layout_changed.connect(self._on_layout_changed)
    
    @property
    def is_dark(self):
        return self._is_dark
    
    @property
    def current(self):
        return self._current
    
    def toggle(self):
        self._is_dark = not self._is_dark
        self._current = self.DARK if self._is_dark else self.LIGHT
        self._apply_matplotlib_theme()
        self.theme_changed.emit(self._current["name"])
    
    def _on_layout_changed(self, layout_type):
        """Update matplotlib fonts when layout changes."""
        self._apply_matplotlib_theme()
    
    def _get_matplotlib_font_size(self):
        """Get scaled font size for matplotlib charts."""
        scale = layout_manager.font_scale()
        dpi_scale = layout_manager._get_dpi_scale() if hasattr(layout_manager, '_get_dpi_scale') else 1.0
        
        base_sizes = {
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.titlesize': 12,
        }
        
        scaled_sizes = {}
        for key, base_size in base_sizes.items():
            scaled_size = int(base_size * scale * dpi_scale)
            scaled_sizes[key] = max(8, scaled_size)
        
        return scaled_sizes
    
    def _apply_matplotlib_theme(self):
        """Force all matplotlib charts to use theme colors and fonts."""
        t = self._current
        font_sizes = self._get_matplotlib_font_size()
        
        # Update all matplotlib params
        matplotlib.rcParams.update({
            # Background colors
            'figure.facecolor': t['base'],
            'axes.facecolor': t['base'],
            'axes.edgecolor': t['border'],
            # Text colors
            'axes.labelcolor': t['text'],
            'text.color': t['text'],
            'xtick.color': t['text'],
            'ytick.color': t['text'],
            # Grid colors
            'grid.color': t['border'],
            'grid.alpha': t.get('mpl_grid_alpha', 0.3),
            # Legend colors
            'legend.facecolor': t['crust'],
            'legend.edgecolor': t['border'],
            'legend.labelcolor': t['text'],
            # Font sizes
            'font.size': font_sizes['font.size'],
            'axes.labelsize': font_sizes['axes.labelsize'],
            'axes.titlesize': font_sizes['axes.titlesize'],
            'xtick.labelsize': font_sizes['xtick.labelsize'],
            'ytick.labelsize': font_sizes['ytick.labelsize'],
            'legend.fontsize': font_sizes['legend.fontsize'],
            'figure.titlesize': font_sizes['figure.titlesize'],
            # Color cycle for ALL plots - bars, lines, etc.
            'axes.prop_cycle': matplotlib.cycler(color=[
                t['accent'],
                t['success'],
                t['warning'],
                t['error'],
                t['accent_hover'],
                t['text_secondary']
            ]),
        })
        plt.rcParams.update(matplotlib.rcParams)

        # rcParams only act as a template for NEW figures/axes created after
        # this point - they do NOT retroactively repaint figures that
        # already exist (e.g. a chart canvas built before a theme toggle,
        # or one that hasn't been re-rendered by its own page yet). Without
        # this step, those charts silently keep stale colors (often white
        # backgrounds) after switching to dark mode.
        self._refresh_existing_figures()

    def _repaint_figure(self, fig, t):
        """Apply theme colors to a single Figure/Axes set."""
        fig.set_facecolor(t['base'])
        for ax in fig.axes:
            ax.set_facecolor(t['base'])
            ax.tick_params(colors=t['text'])
            ax.xaxis.label.set_color(t['text'])
            ax.yaxis.label.set_color(t['text'])
            if ax.title:
                ax.title.set_color(t['text'])
            for spine in ax.spines.values():
                spine.set_color(t['border'])
            if ax.get_lines() or ax.patches or ax.collections:
                ax.grid(color=t['border'], alpha=t.get('mpl_grid_alpha', 0.3))
            legend = ax.get_legend()
            if legend is not None:
                frame = legend.get_frame()
                frame.set_facecolor(t['crust'])
                frame.set_edgecolor(t['border'])
                for text in legend.get_texts():
                    text.set_color(t['text'])

    def _refresh_existing_figures(self):
        """Force-repaint colors on all matplotlib figures that already
        exist, so every chart in the app stays in sync with the current
        theme even if its own page doesn't explicitly listen for
        theme_changed or hasn't redrawn itself yet.

        Note: rcParams and plt.get_fignums() only cover figures created
        through pyplot's own state machine (plt.figure()). Charts built
        directly as `Figure(...)` and wrapped in a FigureCanvasQTAgg -
        which is how most embedded charts in this app are built - never
        register with pyplot at all, so that route misses them entirely.
        Instead, walk every live Qt widget and grab `.figure` off any
        widget that has one (every FigureCanvas subclass exposes this
        attribute regardless of how its Figure was constructed). This
        reaches every chart in the app with no per-page registration."""
        t = self._current
        seen = set()

        # Figures still tracked by pyplot's global state machine.
        for num in plt.get_fignums():
            fig = plt.figure(num)
            if id(fig) in seen:
                continue
            seen.add(id(fig))
            try:
                self._repaint_figure(fig, t)
                if fig.canvas is not None:
                    fig.canvas.draw_idle()
            except Exception:
                continue

        # Any matplotlib figure embedded in a Qt canvas anywhere in the
        # app, even if it was created directly via Figure() and never
        # touched pyplot.
        app = QApplication.instance()
        if app is not None:
            for widget in app.allWidgets():
                fig = getattr(widget, 'figure', None)
                if fig is None or id(fig) in seen:
                    continue
                seen.add(id(fig))
                try:
                    self._repaint_figure(fig, t)
                    draw_idle = getattr(widget, 'draw_idle', None)
                    if callable(draw_idle):
                        draw_idle()
                    else:
                        widget.draw()
                except Exception:
                    continue
    
    def get_mpl_colors(self):
        """Get matplotlib colors for charts."""
        t = self._current
        return {
            'bar_color': t.get('mpl_bar_color', t['accent']),
            'bar_alpha': t.get('mpl_bar_alpha', 0.85),
            'text_color': t['text'],
            'bg_color': t['base'],
            'grid_color': t['border'],
            'success': t['success'],
            'warning': t['warning'],
            'error': t['error'],
            'accent': t['accent'],
        }
    
    def stylesheet(self):
        t = self._current
        return f"""
        QMainWindow {{
            background-color: {t['base']};
            color: {t['text']};
        }}
        
        QMenuBar {{
            background-color: {t['crust']};
            color: {t['text_secondary']};
            border-bottom: 1px solid {t['border']};
            padding: 2px 0px;
        }}
        QMenuBar::item {{
            padding: 6px 14px;
            border-radius: 4px;
            margin: 2px 2px;
        }}
        QMenuBar::item:selected {{
            background-color: {t['hover']};
            color: {t['text']};
        }}
        
        QMenu {{
            background-color: {t['base']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 8px;
            margin-top: 4px;
        }}
        QMenu::item {{
            padding: 8px 36px 8px 16px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {t['hover']};
            color: {t['text']};
        }}
        QMenu::separator {{
            height: 1px;
            background: {t['border']};
            margin: 6px 8px;
        }}
        
        QComboBox {{
            background-color: {t['crust']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 8px 28px 8px 14px;
        }}
        QComboBox:hover {{
            border-color: {t['border_focus']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {t['base']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 8px;
            selection-background-color: {t['hover']};
            selection-color: {t['text']};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {t['hover']};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {t['hover']};
            color: {t['text']};
        }}
        
        QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px 20px;
        }}
        QPushButton:hover {{
            background-color: {t['hover']};
        }}
        QPushButton:pressed {{
            background-color: {t['surface1']};
        }}
        
        QPushButton#actionButton {{
            background-color: {t['crust']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
        }}
        QPushButton#actionButton:hover {{
            background-color: {t['surface0']};
        }}
        
        QPushButton#optionButton {{
            background-color: transparent;
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 14px 20px;
            text-align: left;
        }}
        QPushButton#optionButton:hover {{
            background-color: {t['hover']};
        }}
        
        QPushButton#backButton {{
            background-color: transparent;
            border: none;
            color: {t['text_secondary']};
            padding: 6px 0px;
        }}
        QPushButton#backButton:hover {{
            color: {t['text']};
        }}
        
        QLabel {{
            color: {t['text']};
            background: transparent;
        }}
        QLabel#pageTitle {{
            font-weight: 700;
        }}
        QLabel#pageSubtitle {{
            color: {t['text_secondary']};
        }}
        QLabel#sectionLabel {{
            font-weight: 700;
            color: {t['text_tertiary']};
            letter-spacing: 3px;
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px 14px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {t['border_focus']};
        }}
        
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['surface2']};
            min-height: 36px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t['text_tertiary']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QStatusBar {{
            background-color: {t['crust']};
            color: {t['text_tertiary']};
            border-top: 1px solid {t['border']};
            padding: 3px 14px;
        }}
        
        QFrame#separator {{
            background-color: {t['border']};
            max-height: 1px;
            min-height: 1px;
        }}
        
        QMessageBox {{
            background-color: {t['base']};
        }}
        QMessageBox QLabel {{
            color: {t['text']};
        }}
        """


# Global singleton
theme_manager = ThemeManager()