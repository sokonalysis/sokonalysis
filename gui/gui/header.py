# gui/header.py
"""
Professional header toolbar for the main window.
"""
from PySide6.QtWidgets import QToolBar, QToolButton, QMenu
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QFont, QFontMetrics
import os
import sys

from gui.layout_manager import layout_manager
from gui.user_preferences import user_prefs


class HeaderToolbar:
    """Header toolbar with navigation, tools, and actions."""

    BASE_ICON_SIZE = 32
    BASE_FONT_SIZE = 13

    def __init__(self, main_window, theme_manager):
        self.main_window = main_window
        self.theme = theme_manager
        self.header_toolbar = None
        self.theme_action = None
        self.icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        self._icon_refs = []
        self._menu_buttons = []
        self._expandable_data = {}
        self._expanded_button = None
        self._sub_widgets = []
        self._menus = []
        self._current_area = Qt.ToolBarArea.TopToolBarArea
        self._is_vertical = False
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._delayed_update)

        self._create_header()

        layout_manager.layout_changed.connect(self._on_layout_change)
        self.header_toolbar.orientationChanged.connect(self._on_orientation_changed)

    def _current_icon_size(self):
        """Current icon pixel size, scaled from the layout's icon_scale + DPI."""
        scale = layout_manager.icon_scale()
        dpi = layout_manager._get_dpi_scale()
        return max(16, int(self.BASE_ICON_SIZE * scale * dpi))

    def _current_font_size(self):
        """Current header button font pixel size, scaled with the layout's font_scale + DPI."""
        scale = layout_manager.font_scale()
        dpi = layout_manager._get_dpi_scale()
        return max(8, int(self.BASE_FONT_SIZE * scale * dpi))

    def _get_icon(self, name, size=None):
        """Get icon from assets, rendered at the given (or current) size."""
        path = os.path.join(self.icons_dir, name)
        if os.path.exists(path):
            sz = size if size is not None else self._current_icon_size()
            pixmap = QPixmap(path).scaled(
                sz, sz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            return QIcon(pixmap)
        return QIcon()

    def _track_icon(self, target, icon_name):
        """Remember which widget/action needs its icon rebuilt on layout change."""
        self._icon_refs.append((target, icon_name))

    def _add_menu_action(self, menu, icon_name, text, callback=None):
        """Helper: add a menu action and track its icon for rescaling."""
        action = menu.addAction(self._get_icon(icon_name), text)
        if callback is not None:
            action.triggered.connect(callback)
        self._track_icon(action, icon_name)
        return action

    def _create_header(self):
        """Create the header toolbar."""
        self.header_toolbar = QToolBar()
        icon_size = self._current_icon_size()
        self.header_toolbar.setIconSize(QSize(icon_size, icon_size))
        self.header_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        self.header_toolbar.setMovable(True)
        self.header_toolbar.setFloatable(False)
        self.header_toolbar.setAllowedAreas(
            Qt.ToolBarArea.LeftToolBarArea | 
            Qt.ToolBarArea.RightToolBarArea
        )

        self.header_toolbar.setStyleSheet(self._get_style())

        # === FILE ===
        file_btn = self._create_menu_button("File", "file.png")
        file_menu = QMenu(file_btn)
        self._menus.append(file_menu)
        exit_action = self._add_menu_action(file_menu, "exit.png", "Exit", self.main_window.close)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        file_btn.setMenu(file_menu)
        self.header_toolbar.addWidget(file_btn)
        self._expandable_data[file_btn] = [
            ("Exit", "exit.png", self.main_window.close)
        ]

        # === VIEW ===
        view_btn = self._create_menu_button("View", "view.png")
        view_menu = QMenu(view_btn)
        self._menus.append(view_menu)
        self.theme_action = self._add_menu_action(view_menu, "theme.png", "Switch Theme", self.main_window._toggle_theme)
        self.theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        home_action = self._add_menu_action(view_menu, "home.png", "Home", self.main_window._show_landing)
        home_action.setShortcut(QKeySequence("Ctrl+H"))
        view_btn.setMenu(view_menu)
        self.header_toolbar.addWidget(view_btn)
        self._expandable_data[view_btn] = [
            ("Theme", "theme.png", self.main_window._toggle_theme),
            ("Home", "home.png", self.main_window._show_landing)
        ]

        # === LAYOUT ===
        layout_btn = self._create_menu_button("Layout", "layout.png")
        layout_menu = QMenu(layout_btn)
        self._menus.append(layout_menu)
        self._add_menu_action(layout_menu, "view-default.png", "Default", lambda: self.main_window._apply_layout("default"))
        self._add_menu_action(layout_menu, "view-compact.png", "Compact", lambda: self.main_window._apply_layout("compact"))
        self._add_menu_action(layout_menu, "view-wide.png", "Wide", lambda: self.main_window._apply_layout("wide"))
        layout_btn.setMenu(layout_menu)
        self.header_toolbar.addWidget(layout_btn)
        self._expandable_data[layout_btn] = [
            ("Default", "view-default.png", lambda: self.main_window._apply_layout("default")),
            ("Compact", "view-compact.png", lambda: self.main_window._apply_layout("compact")),
            ("Wide", "view-wide.png", lambda: self.main_window._apply_layout("wide"))
        ]

        # === TOOLS ===
        tools_btn = self._create_menu_button("Tools", "tools.png")
        tools_menu = QMenu(tools_btn)
        self._menus.append(tools_menu)
        self._add_menu_action(tools_menu, "symmetric.png", "Symmetric Ciphers", lambda: self.main_window._show_category("Symmetric"))
        self._add_menu_action(tools_menu, "asymmetric.png", "Asymmetric Ciphers", lambda: self.main_window._show_category("Asymmetric"))
        self._add_menu_action(tools_menu, "hashing.png", "Hashing", lambda: self.main_window._show_category("Hashing"))
        self._add_menu_action(tools_menu, "ctf.png", "CTF Tools", lambda: self.main_window._show_category("CTF"))
        self._add_menu_action(tools_menu, "advanced.png", "Advanced", lambda: self.main_window._show_category("Advanced"))
        tools_btn.setMenu(tools_menu)
        self.header_toolbar.addWidget(tools_btn)
        self._expandable_data[tools_btn] = [
            ("Symmetric", "symmetric.png", lambda: self.main_window._show_category("Symmetric")),
            ("Asymmetric", "asymmetric.png", lambda: self.main_window._show_category("Asymmetric")),
            ("Hashing", "hashing.png", lambda: self.main_window._show_category("Hashing")),
            ("CTF", "ctf.png", lambda: self.main_window._show_category("CTF")),
            ("Advanced", "advanced.png", lambda: self.main_window._show_category("Advanced"))
        ]

        # === CONFIGURATIONS ===
        config_btn = self._create_menu_button("Config", "configurations.png")
        config_menu = QMenu(config_btn)
        self._menus.append(config_menu)
        self._add_menu_action(config_menu, "wordlist.png", "Wordlist Settings", self.main_window._show_configurations)
        self._add_menu_action(config_menu, "jonny.png", "John Settings", self.main_window._show_john_config)
        self._add_menu_action(config_menu, "wordlist.png", "Quadgram Settings", self.main_window._show_json_config)
        config_btn.setMenu(config_menu)
        self.header_toolbar.addWidget(config_btn)
        self._expandable_data[config_btn] = [
            ("Wordlist", "wordlist.png", self.main_window._show_configurations),
            ("John", "jonny.png", self.main_window._show_john_config),
            ("Quadgram", "wordlist.png", self.main_window._show_json_config)
        ]

        # === HELP ===
        help_btn = self._create_menu_button("Help", "help.png")
        help_menu = QMenu(help_btn)
        self._menus.append(help_menu)
        self._add_menu_action(help_menu, "guide.png", "User Guide", self.main_window._show_user_guide)
        self._add_menu_action(help_menu, "license.png", "License", self.main_window._show_license)
        update_action = self._add_menu_action(help_menu, "update.png", "Check for Updates", lambda: self._check_updates())
        self._add_menu_action(help_menu, "about.png", "About", self.main_window._show_about)
        help_btn.setMenu(help_menu)
        self.header_toolbar.addWidget(help_btn)
        self._expandable_data[help_btn] = [
            ("User Guide", "guide.png", self.main_window._show_user_guide),
            ("License", "license.png", self.main_window._show_license),
            ("Updates", "update.png", lambda: self._check_updates()),
            ("About", "about.png", self.main_window._show_about)
        ]

        self._update_menu_styles()
        self._apply_uniform_button_size()
        
        if self._is_vertical:
            self._set_vertical_width()
        
        QTimer.singleShot(200, self._update_footer_visibility)

    def _create_menu_button(self, text, icon_name):
        """Create a tool button with menu."""
        icon_size = self._current_icon_size()
        font_size = self._current_font_size()

        btn = QToolButton()
        btn._stored_text = text
        btn._stored_icon = icon_name
        btn.setText(text)
        btn.setIcon(self._get_icon(icon_name, icon_size))
        btn.setIconSize(QSize(icon_size, icon_size))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.clicked.connect(lambda checked=False, b=btn: self._on_btn_click(b))

        font = btn.font()
        font.setPixelSize(font_size)
        btn.setFont(font)

        self._track_icon(btn, icon_name)
        self._menu_buttons.append(btn)
        return btn

    def _on_btn_click(self, btn):
        """Handle button click in vertical mode - toggle collapse/expand."""
        if self._is_vertical and btn in self._expandable_data:
            self._toggle_collapse(btn)

    def _toggle_collapse(self, btn):
        """Toggle collapse/expand for a button."""
        if self._expanded_button == btn:
            self._collapse_sub()
        else:
            if self._expanded_button:
                self._collapse_sub()
            self._expand_sub(btn)

    def _expand_sub(self, btn):
        """Expand to show sub-items inline below the clicked button."""
        if not self._is_vertical or btn not in self._expandable_data:
            return
        
        self._expanded_button = btn
        
        actions = self.header_toolbar.actions()
        insert_idx = -1
        for i, a in enumerate(actions):
            if a.defaultWidget() == btn:
                insert_idx = i + 1
                break
        
        if insert_idx < 0:
            return
        
        icon_size = self._current_icon_size()
        font_size = self._current_font_size()
        items = self._expandable_data[btn]
        
        sub_icon_size = max(12, icon_size - 6)
        t = self.theme.current
        
        for text, icon_name, callback in items:
            sub = QToolButton()
            sub.setText(text)
            sub.setIcon(self._get_icon(icon_name, sub_icon_size))
            sub.setIconSize(QSize(sub_icon_size, sub_icon_size))
            sub.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            sub.clicked.connect(callback)
            sub.setCursor(Qt.CursorShape.PointingHandCursor)
            
            font = QFont()
            font.setPixelSize(font_size)
            sub.setFont(font)
            
            sub.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    text-align: left;
                    font-size: {font_size}px;
                }}
                QToolButton:hover {{
                    background: {t['hover']};
                    color: {t['text']};
                }}
                QToolButton:pressed {{
                    background: {t['surface1']};
                }}
            """)
            
            current_actions = self.header_toolbar.actions()
            if insert_idx < len(current_actions):
                self.header_toolbar.insertWidget(current_actions[insert_idx], sub)
            else:
                self.header_toolbar.addWidget(sub)

            self._sub_widgets.append(sub)
            insert_idx += 1

    def _collapse_sub(self):
        """Collapse expanded sub-items."""
        all_actions = self.header_toolbar.actions()
        to_remove = []
        for w in self._sub_widgets:
            for a in all_actions:
                if a.defaultWidget() == w:
                    to_remove.append(a)
                    break
        for a in to_remove:
            self.header_toolbar.removeAction(a)
        for w in self._sub_widgets:
            w.deleteLater()
        self._sub_widgets.clear()
        self._expanded_button = None

    def _set_vertical_width(self):
        """Set the fixed width for vertical mode based on content."""
        icon_size = self._current_icon_size()
        font_size = self._current_font_size()
        
        font = QFont()
        font.setPixelSize(font_size)
        fm = QFontMetrics(font)
        
        max_text_width = 0
        
        for btn in self._expandable_data:
            for text, _, _ in self._expandable_data[btn]:
                text_width = fm.horizontalAdvance(text)
                max_text_width = max(max_text_width, text_width)
        
        padding = int(font_size * 2.5)
        width = icon_size + max_text_width + padding
        width = max(width, icon_size + 24)
        
        self.header_toolbar.setFixedWidth(width)
        self.header_toolbar.setMaximumWidth(width)

    def _get_vertical_btn_size(self):
        """Get button size for vertical mode based on layout manager icon_scale."""
        icon_size = self._current_icon_size()
        scale = layout_manager.icon_scale()
        padding = int(icon_size * 0.75 * scale)
        return icon_size + padding

    def _apply_uniform_button_size(self):
        """Force every top-level button to share one width/height."""
        if not self._menu_buttons or not self.header_toolbar:
            return
        try:
            is_vertical = self.header_toolbar.orientation() == Qt.Orientation.Vertical
        except RuntimeError:
            return

        if is_vertical:
            icon_size = self._current_icon_size()
            btn_size = self._get_vertical_btn_size()
            layout = self.header_toolbar.layout()
            for btn in self._menu_buttons:
                try:
                    btn.setFixedSize(btn_size, btn_size)
                    btn.setIconSize(QSize(icon_size, icon_size))
                    if layout is not None:
                        layout.setAlignment(btn, Qt.AlignmentFlag.AlignHCenter)
                except RuntimeError:
                    pass
        else:
            for btn in self._menu_buttons:
                btn.setMinimumWidth(0)
                btn.setMaximumWidth(16777215)
                btn.setMinimumHeight(0)
                btn.setMaximumHeight(16777215)

            try:
                hints = [btn.sizeHint() for btn in self._menu_buttons]
            except RuntimeError:
                return
            if not hints:
                return

            max_w = max(h.width() for h in hints)
            max_h = max(h.height() for h in hints)

            for btn in self._menu_buttons:
                try:
                    btn.setFixedHeight(max_h)
                    btn.setMinimumWidth(max_w)
                except RuntimeError:
                    pass

    def _check_updates(self):
        """Check for updates."""
        from gui.updater import check_for_updates
        check_for_updates(self.main_window)

    def _get_style(self):
        """Get the current style for the header."""
        t = self.theme.current
        font_size = self._current_font_size()
        padding_v = max(2, int(font_size * 0.3))
        padding_h = max(6, int(font_size * 0.9))

        is_vertical = self._current_area in (Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea)

        if is_vertical:
            icon_size = self._current_icon_size()
            btn_size = self._get_vertical_btn_size()
            icon_padding = max(0, (btn_size - icon_size) // 2)
            
            return f"""
                QToolBar {{
                    background-color: {t['crust']};
                    border-right: 1px solid {t['border']};
                    padding: 6px 4px;
                    spacing: 6px;
                }}
                QToolButton {{
                    color: {t['text_secondary']};
                    padding: {icon_padding}px;
                    border-radius: 6px;
                    font-size: {font_size}px;
                    border: none;
                }}
                QToolButton::menu-indicator {{
                    image: none;
                    width: 0px;
                }}
                QToolButton::menu-button {{
                    width: 0px;
                    padding: 0px;
                }}
                QToolButton:hover {{
                    background-color: {t['hover']};
                    color: {t['text']};
                }}
                QToolButton:pressed {{
                    background-color: {t['surface1']};
                }}
            """
        else:
            return f"""
                QToolBar {{
                    background-color: {t['crust']};
                    border-bottom: 1px solid {t['border']};
                    padding: 4px;
                    spacing: 4px;
                }}
                QToolButton {{
                    color: {t['text_secondary']};
                    padding: {padding_v}px {padding_h}px;
                    border-radius: 4px;
                    font-size: {font_size}px;
                    border: none;
                }}
                QToolButton::menu-indicator {{
                    image: none;
                    width: 0px;
                }}
                QToolButton::menu-button {{
                    width: 0px;
                    padding: 0px;
                }}
                QToolButton:hover {{
                    background-color: {t['hover']};
                    color: {t['text']};
                }}
                QToolButton:pressed {{
                    background-color: {t['surface1']};
                }}
            """

    def get_toolbar(self):
        """Get the header toolbar widget."""
        return self.header_toolbar

    def update_style(self):
        """Update the header style when theme changes."""
        if self.header_toolbar:
            self.header_toolbar.setStyleSheet(self._get_style())
        font_size = self._current_font_size()
        for btn in self._menu_buttons:
            try:
                font = btn.font()
                font.setPixelSize(font_size)
                btn.setFont(font)
            except RuntimeError:
                pass
        self._update_menu_styles()
        self._update_sub_styles()

    def update_theme_action_text(self, is_dark):
        """Update the theme action text."""
        if self.theme_action:
            self.theme_action.setText(
                "Switch to &Dark Mode" if not is_dark else "Switch to &Light Mode"
            )

    def _update_menu_styles(self):
        """Apply dynamic font size to all tracked QMenu objects."""
        font_size = self._current_font_size()
        t = self.theme.current
        for menu in self._menus:
            try:
                menu.setStyleSheet(f"""
                    QMenu {{
                        background-color: {t['base']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 4px;
                        margin-top: 2px;
                    }}
                    QMenu::item {{
                        padding: 6px 28px 6px 12px;
                        border-radius: 4px;
                        font-size: {font_size}px;
                    }}
                    QMenu::item:selected {{
                        background-color: {t['hover']};
                        color: {t['text']};
                    }}
                    QMenu::separator {{
                        height: 1px;
                        background: {t['border']};
                        margin: 4px 8px;
                    }}
                """)
            except RuntimeError:
                pass

    def _update_sub_styles(self):
        """Update styles of expanded sub-buttons when theme changes."""
        if not self._sub_widgets:
            return
        font_size = self._current_font_size()
        t = self.theme.current
        for sub in self._sub_widgets:
            try:
                sub.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        color: {t['text_secondary']};
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                        text-align: left;
                        font-size: {font_size}px;
                    }}
                    QToolButton:hover {{
                        background: {t['hover']};
                        color: {t['text']};
                    }}
                    QToolButton:pressed {{
                        background: {t['surface1']};
                    }}
                """)
            except RuntimeError:
                pass

    def _delayed_update(self):
        """Delayed update to prevent glitching during rapid layout changes."""
        icon_size = self._current_icon_size()
        font_size = self._current_font_size()

        if self.header_toolbar:
            self.header_toolbar.setIconSize(QSize(icon_size, icon_size))

        for target, icon_name in self._icon_refs:
            try:
                target.setIcon(self._get_icon(icon_name, icon_size))
                if isinstance(target, QToolButton):
                    target.setIconSize(QSize(icon_size, icon_size))
            except RuntimeError:
                pass

        self.update_style()

        for btn in self._menu_buttons:
            try:
                font = QFont()
                font.setPixelSize(font_size)
                btn.setFont(font)
            except RuntimeError:
                pass

        self._apply_uniform_button_size()
        
        if self._is_vertical:
            self._set_vertical_width()
        
        if self._expanded_button:
            current = self._expanded_button
            self._collapse_sub()
            self._expand_sub(current)
        
        for btn in self._menu_buttons:
            try:
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.updateGeometry()
            except RuntimeError:
                pass
        
        self._update_footer_visibility()

    def _on_orientation_changed(self, orientation):
        """Fires whenever Qt flips the toolbar between horizontal/vertical."""
        self._is_vertical = (orientation == Qt.Orientation.Vertical)
        
        if not self._is_vertical:
            self._collapse_sub()
            self.header_toolbar.setFixedWidth(16777215)
            self.header_toolbar.setMaximumWidth(16777215)
        else:
            self._set_vertical_width()
        
        for btn in self._expandable_data:
            if self._is_vertical:
                btn.setPopupMode(QToolButton.ToolButtonPopupMode.DelayedPopup)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            else:
                btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        self._apply_uniform_button_size()
        
        QTimer.singleShot(50, self._update_area_and_footer)
        QTimer.singleShot(200, self._update_footer_visibility)
        QTimer.singleShot(500, self._update_footer_visibility)

    def _update_area_and_footer(self):
        """Update the current area and footer visibility after docking settles."""
        if not self.header_toolbar:
            return
            
        toolbar_area = self.main_window.toolBarArea(self.header_toolbar)
        
        if toolbar_area != Qt.ToolBarArea.NoToolBarArea:
            self._current_area = toolbar_area
            area_str = {
                Qt.ToolBarArea.TopToolBarArea: "top",
                Qt.ToolBarArea.LeftToolBarArea: "left",
                Qt.ToolBarArea.RightToolBarArea: "right"
            }.get(toolbar_area, "top")
            user_prefs.set_toolbar_area(area_str)
        
        self.update_style()
        self._apply_uniform_button_size()
        self._update_footer_visibility()

    def _update_footer_visibility(self):
        """Hide footer when header is not at the top."""
        if not self.header_toolbar:
            return
            
        if hasattr(self.main_window, 'footer'):
            current_area = self.main_window.toolBarArea(self.header_toolbar)
            
            if current_area == Qt.ToolBarArea.TopToolBarArea:
                self.main_window.footer.show()
            else:
                self.main_window.footer.hide()

    def _on_layout_change(self, layout_type):
        """Re-render header icons and refresh the stylesheet for the new layout."""
        self._update_timer.stop()
        self._update_timer.start(100)

    def set_toolbar_area(self, area):
        """External hook for toolbar area updates."""
        self._current_area = area
        self._is_vertical = area in (Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea)
        
        if not self._is_vertical:
            self._collapse_sub()
            self.header_toolbar.setFixedWidth(16777215)
            self.header_toolbar.setMaximumWidth(16777215)
        else:
            self._set_vertical_width()
        
        self.update_style()
        self._apply_uniform_button_size()
        self._update_footer_visibility()
        QTimer.singleShot(200, self._update_footer_visibility)