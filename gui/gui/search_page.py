# gui/search_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QLineEdit, QToolButton, QMenu, QStackedWidget
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QPixmap
from gui.card_grid import CardGrid
import os
import sys


class SearchPage(QWidget):
    """Professional search page with card-style results and category filters."""

    option_selected = Signal(str)

    def __init__(self, theme_manager, all_options, on_back=None):
        super().__init__()
        self.theme = theme_manager
        self.all_options = all_options if all_options else {}
        self.on_back = on_back
        self.flat_options = []
        self.active_filter = None
        self.card_grid = None

        # Fixed, so the page's total content height (and therefore the
        # search bar's position, if a parent container centers this widget)
        # never depends on whether there happen to be zero or many results.
        self.RESULTS_AREA_MIN_HEIGHT = 420

        self._init_ui()
        self._flatten_options()

    def _flatten_options(self):
        self.flat_options = []
        for category, options in self.all_options.items():
            if not options:
                continue
            for option in options:
                name = ""
                desc = ""
                if isinstance(option, tuple):
                    name = str(option[0]) if option[0] else ""
                    desc = str(option[1]) if len(option) > 1 and option[1] else ""
                elif isinstance(option, str):
                    name = option
                else:
                    continue
                if name:
                    self.flat_options.append({
                        'name': name,
                        'category': str(category),
                        'description': desc
                    })

    def _init_ui(self):
        t = self.theme.current
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')

        # Let the parent give this page as much room as it wants rather
        # than sizing/centering it based on a shrinking sizeHint.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 20)
        self.main_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.on_back)
        back_btn.setMaximumWidth(100)
        header.addWidget(back_btn)
        header.addStretch()
        self.main_layout.addLayout(header)

        # Title - centered
        title = QLabel("Search")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title)

        # Search bar with filter
        search_wrapper = QHBoxLayout()
        search_wrapper.setSpacing(0)

        self.filter_btn = QToolButton()
        self.filter_btn.setText("Filter")
        filter_icon_path = os.path.join(icons_dir, "filter.png")
        if os.path.exists(filter_icon_path):
            self.filter_btn.setIcon(QIcon(filter_icon_path))
        self.filter_btn.setIconSize(QSize(32, 32))
        self.filter_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.filter_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.setStyleSheet(f"""
            QToolButton {{ color: {t['text_secondary']}; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 500; background: transparent; border: none; }}
            QToolButton:hover {{ color: {t['text']}; }}
        """)

        self.filter_menu = QMenu(self.filter_btn)
        self.filter_menu.setStyleSheet(f"""
            QMenu {{ background-color: {t['base']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 8px; }}
            QMenu::item {{ padding: 8px 36px 8px 16px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {t['hover']}; color: {t['text']}; }}
            QMenu::separator {{ height: 1px; background: {t['border']}; margin: 6px 8px; }}
        """)

        all_action = self.filter_menu.addAction("All Categories")
        all_action.triggered.connect(lambda: self._on_filter_selected(None))
        self.filter_menu.addSeparator()

        main_cats = ["Symmetric", "Asymmetric", "Hashing", "Advanced", "CTF"]
        for cat in main_cats:
            cat_action = self.filter_menu.addAction(f"  {cat}")
            cat_action.triggered.connect(lambda checked, c=cat: self._on_filter_selected(c))
            for item in self.flat_options:
                if item['category'] == cat:
                    sub_action = self.filter_menu.addAction(f"    {item['name']}")
                    sub_action.triggered.connect(lambda checked, n=item['name']: self._on_filter_selected(n))

        self.filter_btn.setMenu(self.filter_menu)
        search_wrapper.addWidget(self.filter_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tools, categories, or keywords...")
        self.search_input.setMinimumHeight(44)
        self._apply_search_input_style(t)

        # Use a native trailing action for the clear button instead of a
        # manually-positioned overlay widget. This removes the need for a
        # custom resizeEvent hack and any related layout jitter, and keeps
        # the control glued to the line edit at a fixed spot.
        self.clear_action = self.search_input.addAction(
            QIcon(), QLineEdit.ActionPosition.TrailingPosition
        )
        self.clear_action.setVisible(False)
        self.clear_action.triggered.connect(self.search_input.clear)

        search_wrapper.addWidget(self.search_input, 1)
        self.main_layout.addLayout(search_wrapper)

        self.search_input.textChanged.connect(self._on_search_text_changed)

        # Results count
        self.results_count = QLabel("")
        self.results_count.setStyleSheet(f"color: {t['text_tertiary']}; font-size: 11px; background: transparent;")
        self.results_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.results_count)

        # Separator
        self.separator = QFrame()
        self.separator.setObjectName("separator")
        self.main_layout.addWidget(self.separator)

        # Hint / "no results" state: a big, visible search icon with a short
        # message underneath. Same widget is reused for both the initial
        # "type to search" prompt and the "no results found" case - only
        # the message text changes, via _set_empty_state().
        self.empty_state_widget = QWidget()
        self.empty_state_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        empty_layout = QVBoxLayout(self.empty_state_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(18)

        self.empty_icon_label = QLabel()
        self.empty_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = os.path.join(icons_dir, "system-search-2.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    QSize(110, 110),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.empty_icon_label.setPixmap(scaled)
        empty_layout.addWidget(self.empty_icon_label)

        self.hint_label = QLabel("Type to search across all tools, or use the category filter")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet(f"color: {t['text_tertiary']}; font-size: 13px; background: transparent;")
        empty_layout.addWidget(self.hint_label)

        # Card grid - created once and reused. It stays in the same layout
        # slot for the lifetime of the page; we never remove/insert it again,
        # which is what was causing the whole page (including the search bar)
        # to visibly reflow/jump on every keystroke.
        self.card_grid = CardGrid()
        self.card_grid.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Both the empty state and the card grid live in a single stacked
        # container with a fixed minimum height. Switching between them is
        # a cheap setCurrentWidget() call, and - crucially - the container's
        # height no longer depends on which one is showing or how many
        # cards there are. That's what keeps the search bar pinned at a
        # fixed position instead of the page recentering itself
        # taller/shorter depending on result count.
        self.results_stack = QStackedWidget()
        self.results_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.results_stack.setMinimumHeight(self.RESULTS_AREA_MIN_HEIGHT)
        self.results_stack.addWidget(self.empty_state_widget)
        self.results_stack.addWidget(self.card_grid)
        self.results_stack.setCurrentWidget(self.empty_state_widget)
        self.main_layout.addWidget(self.results_stack, 1)

    def _apply_search_input_style(self, t):
        # No focus glow/border color change - keep the border identical in
        # both states and drop the platform focus outline.
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t['surface0']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 10px 40px 10px 16px;
                font-size: 14px;
                margin-left: 8px;
                outline: none;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['border']};
                outline: none;
            }}
        """)

    def _on_filter_selected(self, value):
        if value in ["Symmetric", "Asymmetric", "Hashing", "Advanced", "CTF"]:
            self.active_filter = value
        elif value is None:
            self.active_filter = None
        else:
            self.active_filter = value
        self._on_search(self.search_input.text())

    def _on_search_text_changed(self, text):
        self.clear_action.setVisible(bool(text))
        # Search immediately on every keystroke - no debounce delay. This is
        # safe to do in real time now because the card grid is reused rather
        # than rebuilt from scratch each call (see _clear_card_grid below).
        self._on_search(text)

    def _on_search(self, text):
        search_text = text.strip().lower()
        matches = []

        for item in self.flat_options:
            if self.active_filter:
                if self.active_filter in ["Symmetric", "Asymmetric", "Hashing", "Advanced", "CTF"]:
                    if item['category'] != self.active_filter:
                        continue
                else:
                    if item['name'] != self.active_filter:
                        continue

            if not search_text and not self.active_filter:
                continue
            if not search_text:
                matches.append(item)
                continue

            name_lower = item['name'].lower()
            category_lower = item['category'].lower()
            desc_lower = item['description'].lower() if item['description'] else ""
            if (search_text in name_lower or search_text in category_lower or search_text in desc_lower):
                matches.append(item)
            elif any(word.startswith(search_text) for word in name_lower.split()):
                matches.append(item)

        def sort_key(item):
            name = item['name'].lower()
            if name == search_text: return 0
            elif name.startswith(search_text): return 1
            return 2
        matches.sort(key=sort_key)

        seen = set()
        unique_matches = []
        for m in matches:
            if m['name'] not in seen:
                seen.add(m['name'])
                unique_matches.append(m)

        if unique_matches:
            count = len(unique_matches)
            parts = []
            if self.active_filter: parts.append(f"in {self.active_filter}")
            if search_text: parts.append(f"matching \"{search_text}\"")
            self.results_count.setText(f"{count} result{'s' if count != 1 else ''} {' · '.join(parts)}")

            cards = [(item['name'], item['description']) for item in unique_matches]

            # Reuse the existing CardGrid instance instead of tearing it down
            # and rebuilding it (and re-inserting it into main_layout) on
            # every search. This is both the main perf fix and part of the
            # fix for the search bar/page jumping around while typing.
            self._clear_card_grid()
            self.card_grid.add_cards(cards, self.theme, self.option_selected.emit)
            self.results_stack.setCurrentWidget(self.card_grid)
        else:
            self.results_count.setText("No results found" if (search_text or self.active_filter) else "")
            self._clear_card_grid()
            if search_text or self.active_filter:
                self._set_empty_state("No results found. Try a different keyword.")
            else:
                self._set_empty_state("Type to search across all tools, or use the category filter")
            self.results_stack.setCurrentWidget(self.empty_state_widget)

    def _set_empty_state(self, message):
        self.hint_label.setText(message)

    def _clear_card_grid(self):
        """Remove the current cards from the grid without destroying/
        recreating the CardGrid widget itself."""
        if not self.card_grid:
            return
        if hasattr(self.card_grid, 'clear_cards'):
            self.card_grid.clear_cards()
            return
        if hasattr(self.card_grid, 'clear'):
            self.card_grid.clear()
            return
        layout = self.card_grid.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

    def refresh_theme(self):
        t = self.theme.current
        self._apply_search_input_style(t)
        self.hint_label.setStyleSheet(f"color:{t['text_tertiary']};font-size:13px;background:transparent;")
        self.results_count.setStyleSheet(f"color:{t['text_tertiary']};font-size:11px;background:transparent;")
        self.filter_btn.setStyleSheet(f"QToolButton{{color:{t['text_secondary']};padding:4px 12px;border-radius:4px;font-size:12px;font-weight:500;background:transparent;border:none;}} QToolButton:hover{{color:{t['text']};}}")
        self.filter_menu.setStyleSheet(f"QMenu{{background-color:{t['base']};color:{t['text']};border:1px solid {t['border']};border-radius:8px;padding:8px;}} QMenu::item{{padding:8px 36px 8px 16px;border-radius:4px;}} QMenu::item:selected{{background-color:{t['hover']};color:{t['text']};}} QMenu::separator{{height:1px;background:{t['border']};margin:6px 8px;}}")
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)