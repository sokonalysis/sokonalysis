from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QScrollArea,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QPixmap, QColor
from gui.layout_manager import layout_manager
import os
import sys


class CardGrid(QWidget):
    
    def __init__(self, parent=None, force_single_row=False):
        super().__init__(parent)
        self._cards = []
        self._card_data = None
        self._theme = None
        self._on_click = None
        self._scroll = None
        self._cards_container = None
        self._scroll_indicator = None
        self._last_width = None
        self._last_height = None
        self._force_single_row = force_single_row
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)
        self._resize_timer.timeout.connect(self._on_resize_settled)
        self._setup_ui()
        layout_manager.layout_changed.connect(self._on_layout_changed)
        
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._float_indicator)
        self._float_direction = -1
        self._float_offset = 0

        # animation bookkeeping (does not affect layout logic, purely cosmetic)
        self._entrance_anims = []
        self._entrance_timers = []
        self._hover_anims = {}

    def _setup_ui(self):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._card_data:
            self._resize_timer.start()

    def _on_resize_settled(self):
        if not self._card_data:
            return
        w, h = self.width(), self.height()
        if (self._last_width is None or 
            abs(w - self._last_width) > 20 or 
            abs(h - self._last_height) > 20):
            self._build_cards()

    def _get_dynamic_values(self):
        width = self.width() if self.width() > 0 else 1280
        
        if layout_manager.current == "compact":
            base_scale = 0.65  # Changed from 0.55
        elif layout_manager.current == "wide":
            base_scale = 1.2
        else:
            base_scale = 1.0
        
        if width < 900:
            scale = 0.6
        elif width < 1100:
            scale = 0.8 * base_scale
        elif width < 1400:
            scale = 1.0 * base_scale
        else:
            scale = 1.2 * base_scale
        
        scale = max(0.5, min(1.4, scale))
        
        return {
            "card_font": max(11, int(16 * scale)),
            "desc_font": max(9, int(11 * scale)),
        }

    def _find_icon(self, icon_name):
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'assets', 'icons', icon_name)
            if os.path.exists(icon_path):
                return icon_path
        
        base_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'icons', icon_name),
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons', icon_name),
            os.path.join('assets', 'icons', icon_name),
        ]
        
        for path in base_paths:
            if os.path.exists(path):
                return path
        return ""

    def add_cards(self, card_data, theme, on_click):
        self._card_data = card_data
        self._theme = theme
        self._on_click = on_click
        self._build_cards()
        QTimer.singleShot(0, self._on_resize_settled)

    def _on_layout_changed(self, layout_type):
        if self._card_data:
            self._build_cards()

    def _float_indicator(self):
        if not self._scroll_indicator or not self._scroll_indicator.isVisible():
            return
            
        self._float_offset += self._float_direction * 1
        if self._float_offset > 8:
            self._float_direction = -1
        elif self._float_offset < -8:
            self._float_direction = 1
            
        self._scroll_indicator.move(
            self._scroll_indicator.x(),
            self._scroll_indicator.y() + self._float_direction
        )

    def _reposition_indicator(self):
        if not self._scroll_indicator or not self._scroll:
            return
            
        indicator_size = 48
        scroll_width = self._scroll.width()
        scroll_height = self._scroll.height()
        
        if scroll_width > 0 and scroll_height > 0:
            x = (scroll_width - indicator_size) // 2
            y = scroll_height - indicator_size - 20
            self._scroll_indicator.setGeometry(x, y, indicator_size, indicator_size)

    def _build_cards(self):
        self.clear()

        if not self._card_data:
            return

        if self._force_single_row:
            cards_per_row = len(self._card_data)
        else:
            cards_per_row = layout_manager.grid_cards_per_row()
            
        values = self._get_dynamic_values()
        title_font_size = values["card_font"]
        desc_font_size = values["desc_font"]
        
        # Only adjust spacing for compact mode on landing page
        if self._force_single_row and layout_manager.current == "compact":
            spacing = 15
            bottom_margin = 10
            card_spacing = 5
        else:
            spacing = 20
            bottom_margin = 20
            card_spacing = 8

        fallback_w, fallback_h = layout_manager.get_window_size()
        available_width = self.width() if self.width() > 0 else fallback_w
        available_height = self.height() if self.height() > 0 else fallback_h

        self._last_width = available_width
        self._last_height = available_height

        card_w = max(120, int((available_width - (cards_per_row - 1) * spacing) / cards_per_row))
        
        if self._force_single_row:
            if layout_manager.current == "compact":
                card_h = max(120, min(200, int((available_height - bottom_margin) * 0.95)))
            elif layout_manager.current == "wide":
                card_h = 250  # Fixed height for wide mode - adjust this value
            else:
                card_h = max(180, min(200, int((available_height - bottom_margin) * 0.95)))
        else:
            usable_height = available_height - bottom_margin - spacing - 50
            card_h = max(120, int(usable_height / 2))

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet("background: transparent;")
        cards_layout = QVBoxLayout(self._cards_container)
        cards_layout.setSpacing(spacing)
        cards_layout.setContentsMargins(0, 0, 0, bottom_margin)

        total_rows = (len(self._card_data) + cards_per_row - 1) // cards_per_row

        self._entrance_anims = []
        card_index = 0

        for row_start in range(0, len(self._card_data), cards_per_row):
            row_cards = self._card_data[row_start:row_start + cards_per_row]

            row_layout = QHBoxLayout()
            row_layout.setSpacing(spacing)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            for name, description in row_cards:
                card = self._create_card(
                    name, description, self._theme,
                    card_w, card_h,
                    title_font_size, desc_font_size,
                    card_spacing
                )
                self._cards.append(card)
                card._card_name = name
                card.mousePressEvent = lambda event, c=card: self._on_card_click(c)
                row_layout.addWidget(card)

                self._animate_card_entrance(card, card_index)
                card_index += 1

            cards_layout.addLayout(row_layout)

        cards_layout.addStretch()

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._cards_container)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        if self._force_single_row:
            self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        if self._scroll.verticalScrollBar():
            self._scroll.verticalScrollBar().valueChanged.connect(self._update_scroll_indicator)
        
        self._scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar {
                height: 0px;
                width: 0px;
                background: transparent;
            }
            QScrollBar::handle {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
        """)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_container = QWidget()
        main_container.setStyleSheet("background: transparent;")
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        main_container_layout.addWidget(self._scroll)
        
        if total_rows > 2 and not self._force_single_row:
            self._scroll_indicator = QLabel(self._scroll)
            self._scroll_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._scroll_indicator.setStyleSheet("background: transparent;")
            self._scroll_indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            
            down_icon = self._find_icon("scroll.png")
            up_icon = self._find_icon("up.png")
            self._down_icon_path = down_icon
            self._up_icon_path = up_icon
            
            self._update_indicator_icon(True)
            
            indicator_size = 48
            self._scroll_indicator.setFixedSize(indicator_size, indicator_size)
            self._reposition_indicator()
            
            self._scroll_indicator.show()
            self._float_timer.start(50)
            
            self._scroll.installEventFilter(self)
        
        self._main_layout.addWidget(main_container)

    def eventFilter(self, obj, event):
        if obj == self._scroll and event.type() == event.Type.Resize:
            self._reposition_indicator()
        return super().eventFilter(obj, event)

    def _update_indicator_icon(self, is_down):
        if not self._scroll_indicator:
            return
            
        icon_path = self._down_icon_path if is_down else self._up_icon_path
        
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
                self._scroll_indicator.setPixmap(scaled)
        else:
            self._scroll_indicator.setText("↓" if is_down else "↑")
            self._scroll_indicator.setStyleSheet("color: rgba(150, 150, 150, 150); font-size: 32px; background: transparent;")

    def _update_scroll_indicator(self, value):
        if not self._scroll_indicator or not self._scroll:
            return
            
        scroll_bar = self._scroll.verticalScrollBar()
        if not scroll_bar:
            return
            
        max_value = scroll_bar.maximum()
        
        if max_value > 0 and value >= max_value:
            self._update_indicator_icon(False)
        else:
            self._update_indicator_icon(True)

    def _on_card_click(self, card):
        if hasattr(card, '_card_name'):
            name = card._card_name
            if self._on_click:
                self._on_click(name)

    # ------------------------------------------------------------------
    # Animation helpers (purely cosmetic — do not alter grid/click logic)
    # ------------------------------------------------------------------

    def _animate_card_entrance(self, card, index):
        """Staggered fade + slight rise-in for each card as it's built.

        IMPORTANT: the animation and its scheduling QTimer are parented to
        `self` (the long-lived CardGrid), never to `card`. Cards get
        deleteLater'd on every rebuild (resize/layout change), and if a
        QPropertyAnimation were parented to the card, Qt would cascade-delete
        the still-pending animation along with it — then the scheduling timer
        would later call .start() on an already-deleted C++ object and raise
        "Internal C++ object already deleted". Parenting to `self` avoids
        that, and clear() proactively stops/drops everything pending anyway.
        """
        opacity_effect = QGraphicsOpacityEffect(card)
        opacity_effect.setOpacity(0.0)
        card.setGraphicsEffect(opacity_effect)
        card._opacity_effect = opacity_effect

        anim = QPropertyAnimation(opacity_effect, b"opacity", self)
        anim.setDuration(320)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _swap_to_shadow():
            # QWidget only supports one active graphics effect at a time, so
            # once the fade-in finishes hand off to the hover shadow effect.
            # Guard against the card having been rebuilt/deleted in the
            # meantime (belt-and-braces on top of clear()'s explicit stop()).
            try:
                shadow = getattr(card, "_shadow_effect", None)
                if shadow is not None:
                    card.setGraphicsEffect(shadow)
            except RuntimeError:
                pass

        anim.finished.connect(_swap_to_shadow)

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(anim.start)

        delay = min(index, 12) * 35  # cap stagger so long grids don't feel sluggish
        timer.start(delay)

        self._entrance_anims.append(anim)
        self._entrance_timers.append(timer)

    def _make_shadow_effect(self, blur, y_offset, alpha):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(0, 0, 0, alpha))
        return shadow

    def _animate_shadow(self, card, shadow, blur_to, y_to, alpha_to, duration=180):
        # Animations are parented to `self`, not to `shadow`/`card`, for the
        # same reason as the entrance animation above: shadow/card are torn
        # down on rebuild and must not take a running animation with them
        # while something else still holds a Python reference to it.
        blur_anim = QPropertyAnimation(shadow, b"blurRadius", self)
        blur_anim.setDuration(duration)
        blur_anim.setStartValue(shadow.blurRadius())
        blur_anim.setEndValue(blur_to)
        blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        offset_anim = QPropertyAnimation(shadow, b"yOffset", self)
        offset_anim.setDuration(duration)
        offset_anim.setStartValue(shadow.yOffset())
        offset_anim.setEndValue(y_to)
        offset_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        color = shadow.color()
        color_anim = QPropertyAnimation(shadow, b"color", self)
        color_anim.setDuration(duration)
        color_anim.setStartValue(color)
        color_anim.setEndValue(QColor(color.red(), color.green(), color.blue(), alpha_to))
        color_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Stop and drop any previous hover animation still running for this
        # card before starting a new one, so we never leak or double-drive
        # the same shadow effect.
        key = id(card)
        old = self._hover_anims.get(key)
        if old:
            for a in old:
                a.stop()

        blur_anim.start()
        offset_anim.start()
        color_anim.start()

        # keep references so Python-side GC doesn't cut animations short
        self._hover_anims[key] = (blur_anim, offset_anim, color_anim)

    def _create_card(self, name, description, theme, card_w, card_h,
                     title_font, desc_font, spacing):
        t = theme.current

        card = QFrame()
        card.setObjectName("landingCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedSize(card_w, card_h)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 24, 20, 20)
        card_layout.setSpacing(spacing)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        name_lbl = QLabel(name)
        name_lbl.setObjectName("cardTitle")
        name_lbl.setStyleSheet(f"color: {t['text']}; font-size: {title_font}px; font-weight: 600; background: transparent;")
        name_lbl.setWordWrap(True)

        desc_lbl = QLabel(description)
        desc_lbl.setObjectName("cardDesc")
        desc_lbl.setStyleSheet(f"color: {t['text_tertiary']}; font-size: {desc_font}px; background: transparent; line-height: 1.4;")
        desc_lbl.setWordWrap(True)

        card_layout.addWidget(name_lbl)
        card_layout.addWidget(desc_lbl)
        card_layout.addStretch()

        card.setStyleSheet(f"""
            QFrame#landingCard {{
                background-color: {t['base']};
                border: 1px solid {t['border']};
                border-radius: 14px;
            }}
            QFrame#landingCard:hover {{
                background-color: {t['hover']};
                border-color: {t['surface2']};
            }}
        """)

        # Modern resting shadow, "lifts" further on hover for a subtle elevation feel
        shadow = self._make_shadow_effect(blur=18, y_offset=4, alpha=40)
        # The opacity effect used for entrance animation is swapped out below
        # once the entrance completes, so give the card its shadow effect now
        # and let _animate_card_entrance layer opacity on top when needed.
        card._shadow_effect = shadow

        def _enter(event, c=card, s=shadow):
            self._animate_shadow(c, s, blur_to=28, y_to=10, alpha_to=70)
            QFrame.enterEvent(c, event)

        def _leave(event, c=card, s=shadow):
            self._animate_shadow(c, s, blur_to=18, y_to=4, alpha_to=40)
            QFrame.leaveEvent(c, event)

        card.enterEvent = _enter
        card.leaveEvent = _leave

        return card

    def clear(self):
        self._float_timer.stop()
        self._float_offset = 0
        self._float_direction = -1
        
        if self._scroll:
            self._scroll.removeEventFilter(self)

        # Stop and drop every pending entrance timer/animation and hover
        # animation BEFORE the old card widgets are torn down below. This is
        # what actually prevents the "Internal C++ object already deleted"
        # crash: once stopped here, none of these can fire later against a
        # card that no longer exists.
        for timer in self._entrance_timers:
            timer.stop()
            timer.deleteLater()
        self._entrance_timers = []

        for anim in self._entrance_anims:
            anim.stop()
        self._entrance_anims = []

        for anims in self._hover_anims.values():
            for a in anims:
                a.stop()
        self._hover_anims = {}
        
        while self._main_layout.count():
            item = self._main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._cards.clear()
        self._scroll = None
        self._cards_container = None
        self._scroll_indicator = None

    def refresh_theme(self, theme):
        t = theme.current
        values = self._get_dynamic_values()
        title_font = values["card_font"]
        desc_font = values["desc_font"]
        
        for card in self._cards:
            card.setStyleSheet(f"""
                QFrame#landingCard {{
                    background-color: {t['base']};
                    border: 1px solid {t['border']};
                    border-radius: 14px;
                }}
                QFrame#landingCard:hover {{
                    background-color: {t['hover']};
                    border-color: {t['surface2']};
                }}
            """)
            for child in card.findChildren(QLabel):
                if child.objectName() == "cardTitle":
                    child.setStyleSheet(f"color: {t['text']}; font-size: {title_font}px; font-weight: 600; background: transparent;")
                elif child.objectName() == "cardDesc":
                    child.setStyleSheet(f"color: {t['text_tertiary']}; font-size: {desc_font}px; background: transparent; line-height: 1.4;")