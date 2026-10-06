# gui/auto_font.py
"""
Automatic font scaling for all widgets.
Just import once in main.py and it handles everything.
"""
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, 
    QTextEdit, QGroupBox, QTabWidget, QTabBar, QMenu, QMenuBar,
    QStatusBar, QToolButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QDateTimeEdit, QListWidget, QTreeWidget,
    QTableWidget, QPlainTextEdit, QCheckBox, QRadioButton,
    QScrollArea, QFrame, QToolBox, QStackedWidget, QSplitter,
    QDockWidget, QMdiArea, QCalendarWidget, QDial, QSlider,
    QProgressBar, QLCDNumber
)
from PySide6.QtCore import QEvent, QObject, QTimer, QSize
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QStyle
from gui.layout_manager import layout_manager


class AutoFont(QObject):
    """Automatically applies fonts to all widgets."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_started'):
            return
        super().__init__()
        self._started = True
        
        # Get font sizes
        self.fonts = self._get_fonts()
        
        # Timer for debouncing updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_to_all_widgets)
        
        # Install event filter
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
        
        # Update on layout change with debounce
        layout_manager.layout_changed.connect(self._on_layout_change)
    
    def _get_fonts(self):
        """Get scaled font sizes."""
        scale = layout_manager.font_scale()
        dpi = layout_manager._get_dpi_scale()
        
        def s(size):
            return max(8, int(size * scale * dpi))
        
        return {
            'title': s(16),
            'body': s(14),
            'heading': s(24),
            'small': s(11),
            'button': s(14),
            'tab': s(13),
            'menu': s(13),
            'status': s(11),
            'input': s(14),
            'groupbox': s(13),
            'tooltip': s(11),
            'checkbox': s(13),
            'radio': s(13),
            'table': s(13),
            'list': s(13),
            'tree': s(13),
            'calendar': s(13),
            'lcd': s(20),
        }
    
    def _on_layout_change(self, layout_type):
        """Handle layout change with debounce to prevent glitching."""
        self.fonts = self._get_fonts()
        self._update_timer.stop()
        self._update_timer.start(50)
    
    def _apply_to_all_widgets(self):
        """Apply fonts to all widgets after layout has settled."""
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                self._apply(widget)
            QTimer.singleShot(10, self._process_new_widgets)
    
    def _process_new_widgets(self):
        """Process widgets that might have been created during the first pass."""
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if self._is_valid(widget) and widget.isVisible():
                    self._apply(widget)
                    for child in widget.findChildren(QWidget):
                        if self._is_valid(child) and child.isVisible():
                            self._apply(child)
    
    def _is_valid(self, widget):
        """Check if a widget is still valid (not deleted)."""
        try:
            if widget is None:
                return False
            if isinstance(widget, QWidget):
                widget.objectName()
                return True
            return False
        except (RuntimeError, AttributeError):
            return False
    
    def _apply_font_to_widget(self, widget, font_size):
        """Helper to apply font size to a widget."""
        if not self._is_valid(widget):
            return
        try:
            current = widget.styleSheet()
            if 'font-size' not in current:
                widget.setStyleSheet(current + f"font-size: {font_size}px;")
        except RuntimeError:
            pass
    
    def _ensure_button_text_fits(self, widget, font_size):
        """Ensure button text is never cut off by adjusting width, height, and padding."""
        if not self._is_valid(widget):
            return
        
        try:
            text = widget.text()
            if not text:
                return
            
            # Create font with the new size
            font = QFont()
            font.setPointSize(font_size)
            metrics = QFontMetrics(font)
            
            # Calculate text width
            text_width = metrics.horizontalAdvance(text)
            
            # Calculate padding based on font size (reduced padding)
            padding_horizontal = font_size * 0.6  # Reduced from 1.0
            padding_vertical = font_size * 0.2    # Reduced from 0.4
            
            # Calculate minimum width needed
            min_width = text_width + padding_horizontal * 2
            
            # Calculate minimum height needed
            min_height = font_size + padding_vertical * 2 + 4  # +4 for border
            
            # Check if button has an icon
            if widget.icon():
                icon_size = widget.iconSize()
                if icon_size.width() > 0:
                    min_width += icon_size.width() + padding_horizontal * 0.3
            
            # Get current size
            current_width = widget.width() if widget.width() > 0 else widget.minimumWidth()
            current_height = widget.height() if widget.height() > 0 else widget.minimumHeight()
            
            # Set minimum width if needed
            if current_width < min_width:
                widget.setMinimumWidth(int(min_width))
            
            # Set minimum height if needed
            if current_height < min_height:
                widget.setMinimumHeight(int(min_height))
            
            # Only add padding if absolutely necessary
            current_style = widget.styleSheet()
            if 'padding' not in current_style:
                widget.setStyleSheet(current_style + 
                    f"padding: {int(padding_vertical)}px {int(padding_horizontal)}px;")
                
        except RuntimeError:
            pass
    
    def _adjust_height(self, widget, font_size):
        """Adjust widget height based on font size to prevent text cutoff."""
        if not self._is_valid(widget):
            return
        
        try:
            min_height = font_size + 10  # Reduced from 16
            
            if isinstance(widget, QLineEdit):
                current_min = widget.minimumHeight()
                if current_min < min_height:
                    widget.setMinimumHeight(min_height)
                current_style = widget.styleSheet()
                if 'padding' not in current_style:
                    widget.setStyleSheet(current_style + f"padding: {int(font_size * 0.2)}px {int(font_size * 0.4)}px;")
            
            elif isinstance(widget, (QTextEdit, QPlainTextEdit)):
                current_min = widget.minimumHeight()
                if current_min < min_height * 1.5:
                    widget.setMinimumHeight(int(min_height * 1.5))
                current_style = widget.styleSheet()
                if 'padding' not in current_style:
                    widget.setStyleSheet(current_style + f"padding: {int(font_size * 0.3)}px;")
            
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                current_min = widget.minimumHeight()
                if current_min < min_height:
                    widget.setMinimumHeight(min_height)
            
            elif isinstance(widget, QComboBox):
                current_min = widget.minimumHeight()
                if current_min < min_height:
                    widget.setMinimumHeight(min_height)
            
            elif isinstance(widget, QPushButton):
                self._ensure_button_text_fits(widget, font_size)
        except RuntimeError:
            pass
    
    def _adjust_tab_width(self, tab_widget, font_size):
        """Adjust tab widths based on text length to prevent cutoff."""
        if not self._is_valid(tab_widget):
            return
        
        try:
            tab_bar = tab_widget.tabBar()
            if not self._is_valid(tab_bar):
                return
            
            font = QFont()
            font.setPointSize(font_size)
            metrics = QFontMetrics(font)
            
            total_width = 0
            for i in range(tab_widget.count()):
                text = tab_widget.tabText(i)
                if text:
                    text_width = metrics.horizontalAdvance(text)
                    padding = font_size * 0.8  # Reduced from 1.5
                    total_width += text_width + padding
                else:
                    total_width += 60  # Reduced from 80
            
            total_width += font_size * 1.5  # Reduced from 2
            
            current_min = tab_bar.minimumWidth()
            if current_min < total_width:
                tab_bar.setMinimumWidth(int(total_width))
                
        except RuntimeError:
            pass
    
    def _apply(self, widget):
        """Apply fonts to a widget."""
        if not self._is_valid(widget):
            return
        
        try:
            fonts = self.fonts
            
            # QLabel
            if isinstance(widget, QLabel):
                name = widget.objectName()
                if name in ['pageTitle', 'title']:
                    widget.setStyleSheet(f"font-size: {fonts['heading']}px; font-weight: bold;")
                elif name in ['cardTitle']:
                    widget.setStyleSheet(f"font-size: {fonts['title']}px; font-weight: 600;")
                elif name in ['pageSubtitle', 'cardDesc', 'subtitle']:
                    widget.setStyleSheet(f"font-size: {fonts['body']}px;")
                else:
                    self._apply_font_to_widget(widget, fonts['body'])
            
            # QPushButton
            elif isinstance(widget, QPushButton):
                self._apply_font_to_widget(widget, fonts['button'])
                self._ensure_button_text_fits(widget, fonts['button'])
            
            # QToolButton
            elif isinstance(widget, QToolButton):
                self._apply_font_to_widget(widget, fonts['button'])
                if widget.text():
                    font = QFont()
                    font.setPointSize(fonts['button'])
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(widget.text())
                    padding = fonts['button'] * 0.6
                    min_width = text_width + padding * 2
                    if widget.icon():
                        icon_size = widget.iconSize()
                        if icon_size.width() > 0:
                            min_width += icon_size.width() + padding * 0.3
                    current_min = widget.minimumWidth()
                    if current_min < min_width:
                        widget.setMinimumWidth(int(min_width))
            
            # QLineEdit
            elif isinstance(widget, QLineEdit):
                self._apply_font_to_widget(widget, fonts['input'])
                self._adjust_height(widget, fonts['input'])
            
            # QTextEdit
            elif isinstance(widget, QTextEdit):
                self._apply_font_to_widget(widget, fonts['body'])
                self._adjust_height(widget, fonts['body'])
            
            # QPlainTextEdit
            elif isinstance(widget, QPlainTextEdit):
                self._apply_font_to_widget(widget, fonts['body'])
                self._adjust_height(widget, fonts['body'])
            
            # QGroupBox
            elif isinstance(widget, QGroupBox):
                current = widget.styleSheet()
                if 'font-size' not in current:
                    widget.setStyleSheet(current + f"font-size: {fonts['groupbox']}px; font-weight: 600;")
                if 'padding' not in current:
                    widget.setStyleSheet(current + f"padding-top: {int(fonts['groupbox'] * 0.3)}px;")
            
            # QCheckBox
            elif isinstance(widget, QCheckBox):
                self._apply_font_to_widget(widget, fonts['checkbox'])
                current = widget.styleSheet()
                if 'spacing' not in current:
                    widget.setStyleSheet(current + f"spacing: {int(fonts['checkbox'] * 0.2)}px;")
                if widget.text():
                    font = QFont()
                    font.setPointSize(fonts['checkbox'])
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(widget.text())
                    padding = fonts['checkbox'] * 0.6
                    min_width = text_width + padding + 24
                    current_min = widget.minimumWidth()
                    if current_min < min_width:
                        widget.setMinimumWidth(int(min_width))
            
            # QRadioButton
            elif isinstance(widget, QRadioButton):
                self._apply_font_to_widget(widget, fonts['radio'])
                current = widget.styleSheet()
                if 'spacing' not in current:
                    widget.setStyleSheet(current + f"spacing: {int(fonts['radio'] * 0.2)}px;")
                if widget.text():
                    font = QFont()
                    font.setPointSize(fonts['radio'])
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(widget.text())
                    padding = fonts['radio'] * 0.6
                    min_width = text_width + padding + 24
                    current_min = widget.minimumWidth()
                    if current_min < min_width:
                        widget.setMinimumWidth(int(min_width))
            
            # QTabWidget
            elif isinstance(widget, QTabWidget):
                tab_bar = widget.tabBar()
                if self._is_valid(tab_bar):
                    self._apply_font_to_widget(tab_bar, fonts['tab'])
                    current_min = tab_bar.minimumHeight()
                    min_height = fonts['tab'] + 8  # Reduced from 12
                    if current_min < min_height:
                        tab_bar.setMinimumHeight(min_height)
                    self._adjust_tab_width(widget, fonts['tab'])
                
                for i in range(widget.count()):
                    tab_widget = widget.widget(i)
                    if self._is_valid(tab_widget):
                        self._apply(tab_widget)
                        for child in tab_widget.findChildren(QWidget):
                            if self._is_valid(child):
                                self._apply(child)
            
            # QComboBox
            elif isinstance(widget, QComboBox):
                self._apply_font_to_widget(widget, fonts['input'])
                self._adjust_height(widget, fonts['input'])
                if widget.currentText():
                    font = QFont()
                    font.setPointSize(fonts['input'])
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(widget.currentText())
                    padding = fonts['input'] * 1.0
                    min_width = text_width + padding + 16
                    current_min = widget.minimumWidth()
                    if current_min < min_width:
                        widget.setMinimumWidth(int(min_width))
                if widget.isEditable():
                    line_edit = widget.lineEdit()
                    if self._is_valid(line_edit):
                        self._apply_font_to_widget(line_edit, fonts['input'])
                        self._adjust_height(line_edit, fonts['input'])
            
            # QSpinBox, QDoubleSpinBox
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                self._apply_font_to_widget(widget, fonts['input'])
                self._adjust_height(widget, fonts['input'])
                font = QFont()
                font.setPointSize(fonts['input'])
                metrics = QFontMetrics(font)
                max_text = "-999999"
                text_width = metrics.horizontalAdvance(max_text)
                padding = fonts['input'] * 1.0
                min_width = text_width + padding + 16
                current_min = widget.minimumWidth()
                if current_min < min_width:
                    widget.setMinimumWidth(int(min_width))
            
            # QDateEdit, QTimeEdit, QDateTimeEdit
            elif isinstance(widget, (QDateEdit, QTimeEdit, QDateTimeEdit)):
                self._apply_font_to_widget(widget, fonts['input'])
                self._adjust_height(widget, fonts['input'])
            
            # QListWidget
            elif isinstance(widget, QListWidget):
                self._apply_font_to_widget(widget, fonts['list'])
                current = widget.styleSheet()
                if 'padding' not in current:
                    widget.setStyleSheet(current + f"padding: {int(fonts['list'] * 0.2)}px;")
            
            # QTreeWidget
            elif isinstance(widget, QTreeWidget):
                self._apply_font_to_widget(widget, fonts['tree'])
                current = widget.styleSheet()
                if 'padding' not in current:
                    widget.setStyleSheet(current + f"padding: {int(fonts['tree'] * 0.2)}px;")
            
            # QTableWidget
            elif isinstance(widget, QTableWidget):
                self._apply_font_to_widget(widget, fonts['table'])
                current = widget.styleSheet()
                if 'padding' not in current:
                    widget.setStyleSheet(current + f"padding: {int(fonts['table'] * 0.2)}px;")
            
            # QMenuBar
            elif isinstance(widget, QMenuBar):
                self._apply_font_to_widget(widget, fonts['menu'])
                current_min = widget.minimumHeight()
                min_height = fonts['menu'] + 8  # Reduced from 12
                if current_min < min_height:
                    widget.setMinimumHeight(min_height)
            
            # QStatusBar
            elif isinstance(widget, QStatusBar):
                self._apply_font_to_widget(widget, fonts['status'])
            
            # QCalendarWidget
            elif isinstance(widget, QCalendarWidget):
                self._apply_font_to_widget(widget, fonts['calendar'])
            
            # QLCDNumber
            elif isinstance(widget, QLCDNumber):
                self._apply_font_to_widget(widget, fonts['lcd'])
                current_min = widget.minimumHeight()
                min_height = fonts['lcd'] + 6
                if current_min < min_height:
                    widget.setMinimumHeight(min_height)
            
            # QSlider, QDial, QProgressBar
            elif isinstance(widget, (QSlider, QDial, QProgressBar)):
                self._apply_font_to_widget(widget, fonts['body'])
            
            # QMenu
            elif isinstance(widget, QMenu):
                self._apply_font_to_widget(widget, fonts['menu'])
                current = widget.styleSheet()
                if 'padding' not in current:
                    widget.setStyleSheet(current + f"padding: {int(fonts['menu'] * 0.2)}px {int(fonts['menu'] * 0.4)}px;")
            
            # QFrame, QScrollArea - skip containers
            elif isinstance(widget, (QFrame, QScrollArea, QStackedWidget, QSplitter, QDockWidget, QToolBox)):
                pass
            
            # CATCH-ALL
            else:
                if hasattr(widget, 'styleSheet') and hasattr(widget, 'setStyleSheet'):
                    if not widget.children() or isinstance(widget, (QWidget, QFrame)):
                        self._apply_font_to_widget(widget, fonts['body'])
                        self._adjust_height(widget, fonts['body'])
        except RuntimeError:
            pass
    
    def eventFilter(self, obj, event):
        """Apply fonts when widgets are shown or added."""
        if not self._is_valid(obj):
            return False
        
        if event.type() == QEvent.Type.Show and isinstance(obj, QWidget):
            QTimer.singleShot(5, lambda: self._apply(obj) if self._is_valid(obj) else None)
            for child in obj.findChildren(QWidget):
                if self._is_valid(child):
                    QTimer.singleShot(5, lambda c=child: self._apply(c) if self._is_valid(c) else None)
        elif event.type() == QEvent.Type.Polish and isinstance(obj, QWidget):
            if self._is_valid(obj):
                self._apply(obj)
        return False


_auto_font = None

def init_auto_font():
    """Initialize auto font (call once in main.py)."""
    global _auto_font
    if _auto_font is None:
        _auto_font = AutoFont()
    return _auto_font