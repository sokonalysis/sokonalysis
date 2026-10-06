# gui/navigation_bar.py
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QFrame
)
from PySide6.QtCore import Qt, Signal
from gui.layout_manager import layout_manager


class NavigationBar(QWidget):
    """
    A bar that displays the current breadcrumb path and allows pinning
    pages. Pinning a page makes it the new breadcrumb "root": navigating
    anywhere else afterwards builds the trail starting from that pinned
    page instead of from Home, until it is unpinned.
    """
    pin_clicked = Signal(str, str)        # Emits (page_key, display_name) - toggles pin
    breadcrumb_clicked = Signal(str)      # Emits page_key to navigate back

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.current_path = []   # List of tuples: (page_key, display_name)
        self.pinned_pages = []   # List of tuples: (page_key, display_name)

        self._setup_ui()

    def _setup_ui(self):
        # Use layout_manager for spacing and margins
        m = layout_manager.get_scaled_margins((8, 4, 8, 4))
        spacing = layout_manager.get_scaled_spacing(6)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*m)
        layout.setSpacing(spacing)

        # --- Breadcrumb Container ---
        self.breadcrumb_container = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(spacing)
        self.breadcrumb_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.breadcrumb_container, 1)
        layout.addStretch(1)

        # Bottom border line to separate from content
        self.setStyleSheet("NavigationBar { border-bottom: 1px solid palette(mid); }")

    def set_path(self, path_list):
        """
        Update the breadcrumb path.
        :param path_list: List of tuples (page_key, display_name)
        """
        self.current_path = path_list
        self._rebuild_breadcrumbs()

    def _is_pinned(self, page_key):
        return any(k == page_key for k, _ in self.pinned_pages)

    def _rebuild_breadcrumbs(self):
        # Clear existing
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.current_path:
            return

        # Build new
        for i, (key, name) in enumerate(self.current_path):
            # Add separator if not first
            if i > 0:
                sep = QLabel(">")
                sep.setObjectName("breadcrumbSeparator")
                self.breadcrumb_layout.addWidget(sep)

            # Wrap each segment so we can show a pin toggle next to it
            segment = QWidget()
            seg_layout = QHBoxLayout(segment)
            seg_layout.setContentsMargins(0, 0, 0, 0)
            seg_layout.setSpacing(2)

            # Create button for the path segment
            btn = QPushButton(name)
            btn.setObjectName("breadcrumbButton")
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)

            is_last = i == len(self.current_path) - 1
            is_home = key == "__home__"

            if is_last:
                btn.setObjectName("breadcrumbCurrent")
                btn.setEnabled(False)  # Current page
            else:
                btn.clicked.connect(lambda checked=False, k=key: self.breadcrumb_clicked.emit(k))

            seg_layout.addWidget(btn)

            # Pin/unpin toggle for every segment, skipping Home since
            # there's nothing meaningful to pin there.
            if not is_home:
                pinned = self._is_pinned(key)
                
                pin_btn = QToolButton()
                pin_btn.setCursor(Qt.PointingHandCursor)
                pin_btn.setText("\u2605" if pinned else "\u2606")  # filled/outline star
                pin_btn.setToolTip("Unpin this page" if pinned else "Pin this page")
                pin_btn.setObjectName("breadcrumbPin")
                
                # Make the star gold-ish
                pin_btn.setStyleSheet("QToolButton#breadcrumbPin { color: #d4a017; border: none; background: transparent; font-size: 14px; }")
                pin_btn.clicked.connect(lambda checked=False, k=key, n=name: self.pin_clicked.emit(k, n))
                seg_layout.addWidget(pin_btn)

            self.breadcrumb_layout.addWidget(segment)

    def update_pins(self, pinned_list):
        """Update the pinned tabs display."""
        self.pinned_pages = pinned_list
        # No separate pin box anymore, just refresh the breadcrumbs
        self._rebuild_breadcrumbs()