import sys
from PySide6.QtWidgets import QApplication
from gui.tools_config_page import ToolsConfigPage

# Mock theme manager
class MockTheme:
    current = {
        'base': '#ffffff', 'text': '#000000', 'crust': '#f0f0f0', 
        'border': '#cccccc', 'surface0': '#e0e0e0'
    }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolsConfigPage(MockTheme(), back_callback=lambda: print("Back clicked"))
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())