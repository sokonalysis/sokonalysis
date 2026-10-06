# gui/footer.py
"""
Professional footer for the main window.
"""
from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import Qt

from gui.utils import get_version, get_os_info


class Footer:
    """Footer status bar with version and OS info."""
    
    def __init__(self, main_window, theme_manager):
        self.main_window = main_window
        self.theme = theme_manager
        self.status_bar = None
        self.version_label = None
        self.os_display = get_os_info()
        
        self._create_footer()
    
    def _create_footer(self):
        """Create the footer status bar."""
        self.status_bar = QStatusBar()
        version = get_version()
        
        self.version_label = QLabel(f"sokonalysis v{version} — {self.os_display}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_bar.addWidget(self.version_label, 1)
        
        self.update_style()
    
    def get_status_bar(self):
        """Get the status bar widget."""
        return self.status_bar
    
    def update_style(self):
        """Update footer style when theme changes."""
        if self.status_bar:
            self.status_bar.setStyleSheet(self._get_style())
    
    def update_version_text(self):
        """Update the version text."""
        if self.version_label:
            version = get_version()
            self.version_label.setText(f"sokonalysis v{version} — {self.os_display}")
    
    def show(self):
        """Show the footer."""
        if self.status_bar:
            self.status_bar.setVisible(True)
    
    def hide(self):
        """Hide the footer."""
        if self.status_bar:
            self.status_bar.setVisible(False)
    
    def _get_style(self):
        """Get the footer stylesheet."""
        t = self.theme.current
        
        return f"""
            QStatusBar {{
                background-color: {t['crust']};
                color: {t['text_secondary']};
                border-top: 1px solid {t['border']};
                padding: 4px 8px;
            }}
            QStatusBar QLabel {{
                color: {t['text_secondary']};
                padding: 0px 8px;
            }}
        """