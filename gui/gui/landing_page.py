from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QLineEdit, QTextBrowser
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QMovie
from urllib.parse import unquote
import os
import sys
from datetime import datetime
from gui.ai_assistant import AIAssistantWorker
from gui.layout_manager import layout_manager
from gui.font_controller import font_controller
from gui.card_grid import CardGrid


class ClickableTextBrowser(QTextBrowser):
    """QTextBrowser that emits a signal when a link is clicked."""
    link_clicked = Signal(str)
    
    def mousePressEvent(self, event):
        anchor = self.anchorAt(event.pos())
        if anchor:
            self.link_clicked.emit(anchor)
            return
        super().mousePressEvent(event)
    
    def setSource(self, url):
        if url.toString().startswith('http://sokonalysis/'):
            return
        super().setSource(url)
    
    def loadResource(self, type, name):
        if name.toString().startswith('http://sokonalysis/'):
            return None
        return super().loadResource(type, name)


class LandingPage(QWidget):
    """Professional landing page with logo, categorized tool sections, and search.

    Layout note: the page never scrolls. Instead it adapts to the window
    height in "density" steps (0 = roomy ... 3 = tightest): logo, title,
    spacing and the AI box get slightly smaller as the window gets shorter,
    and the category cards size and shrink their text to fit what is left
    (see CardGrid). The cards and the AI box therefore never collide.
    """
    
    search_requested = Signal(str)
    
    total_operations = 0
    last_activity = None
    app_start_time = None
    operation_log = []
    
    def __init__(self, theme_manager, on_category_clicked):
        super().__init__()
        self.theme = theme_manager
        self.on_category_clicked = on_category_clicked
        self.card_grid = None
        self._saved_ai_response = ""
        self._thinking_movie = None
        self._thinking_container = None
        self._ai_icon_movie = None
        self._ai_icon_idle = True
        self._density = 0
        self._min_density = 0          # raised by _verify_fit if the estimate was too optimistic
        self._min_density_height = 0   # page height at which it was raised
        self._params = None
        
        if LandingPage.app_start_time is None:
            LandingPage.app_start_time = datetime.now()
        
        self.setAcceptDrops(True)
        self._init_ui()
        
        self.runtime_timer = QTimer(self)
        self.runtime_timer.timeout.connect(self._update_runtime)
        self.runtime_timer.start(1000)
        
        layout_manager.layout_changed.connect(self._on_layout_changed)
    
    @classmethod
    def record_activity(cls, activity_name):
        cls.total_operations += 1
        cls.last_activity = activity_name
        cls.operation_log.append({'name': activity_name, 'time': datetime.now()})
        if len(cls.operation_log) > 100:
            cls.operation_log = cls.operation_log[-100:]
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self._handle_dropped_file(file_path)
    
    def _get_logo_gif_path(self):
        """Get the logo.gif path."""
        if hasattr(sys, '_MEIPASS'):
            for p in [os.path.join(sys._MEIPASS, 'assets', 'logo.gif'), os.path.join(sys._MEIPASS, 'logo.gif')]:
                if os.path.exists(p):
                    return p
        for p in [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.gif'),
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.gif'),
            os.path.join('assets', 'logo.gif'),
        ]:
            if p and os.path.exists(p):
                return p
        return ""
    
    def _stop_thinking_animation(self):
        """Stop and clean up thinking animation."""
        if hasattr(self, '_thinking_movie') and self._thinking_movie:
            self._thinking_movie.stop()
            self._thinking_movie.deleteLater()
            self._thinking_movie = None
    
    def _hide_thinking_container(self):
        """Hide and clean up thinking container."""
        if hasattr(self, '_thinking_container') and self._thinking_container:
            try:
                self._thinking_container.hide()
                self._thinking_container.deleteLater()
            except RuntimeError:
                pass
            self._thinking_container = None
    
    def _show_thinking_animation(self, message="Thinking..."):
        """Show animated GIF with thinking message in the response area (top)."""
        self._stop_thinking_animation()
        self._hide_thinking_container()
        
        logo_gif_path = self._get_logo_gif_path()
        
        # Get the parent of ai_response (the AI container)
        parent_widget = self.ai_response.parent()
        if not parent_widget:
            self.ai_response.setText(message)
            return
        
        # Create thinking container as child of parent
        self._thinking_container = QWidget(parent_widget)
        self._thinking_container.setStyleSheet("background: transparent;")
        
        thinking_layout = QHBoxLayout(self._thinking_container)
        thinking_layout.setContentsMargins(14, 0, 14, 0)
        thinking_layout.setSpacing(6)
        thinking_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        if logo_gif_path and os.path.exists(logo_gif_path):
            # Create QMovie for animation
            self._thinking_movie = QMovie(logo_gif_path)
            self._thinking_movie.setScaledSize(QSize(20, 20))
            self._thinking_movie.setCacheMode(QMovie.CacheMode.CacheAll)
            
            # Create QLabel to hold the animation
            thinking_gif_label = QLabel()
            thinking_gif_label.setMovie(self._thinking_movie)
            thinking_gif_label.setFixedSize(20, 20)
            thinking_gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thinking_gif_label.setStyleSheet("background: transparent; border: none;")
            
            # Start the animation
            self._thinking_movie.start()
            
            thinking_layout.addWidget(thinking_gif_label)
        
        # Add thinking text
        thinking_text = QLabel(message)
        thinking_text.setStyleSheet("color: #888; font-size: 12px; background: transparent; border: none;")
        thinking_layout.addWidget(thinking_text)
        thinking_layout.addStretch()
        
        # Position the container exactly where ai_response is (top area)
        response_geo = self.ai_response.geometry()
        self._thinking_container.setGeometry(response_geo.x(), response_geo.y(), response_geo.width(), 30)
        self._thinking_container.show()
        self._thinking_container.raise_()
    
    def _handle_dropped_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
        
        self.ai_response.show()
        self._show_thinking_animation("Analyzing...")
        
        self.ai_worker = AIAssistantWorker(f"analyze file", dropped_file=file_path)
        self.ai_worker.response_ready.connect(self._on_ai_response)
        self.ai_worker.action_requested.connect(self._on_ai_action)
        self.ai_worker.progress_update.connect(self._on_ai_progress)
        self.ai_worker.start()
    
    def _find_logo(self):
        if hasattr(sys, '_MEIPASS'):
            for p in [os.path.join(sys._MEIPASS, 'assets', 'logo.png'), os.path.join(sys._MEIPASS, 'logo.png')]:
                if os.path.exists(p): return p
        for p in [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'logo.png'),
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png'),
            os.path.join('assets', 'logo.png'),
            os.path.join(os.path.expanduser('~'), '.sokonalysis', 'logo.png'),
            '/usr/local/share/icons/sokonalysis.png',
        ]:
            if p and os.path.exists(p): return p
        return ""
    
    def _get_dynamic_values(self):
        """Get dynamic values based on layout and window width."""
        width = self.width() if self.width() > 0 else 1280
        
        if layout_manager.current == "compact":
            base_scale = 0.7
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
            "search_margin": int(200 * scale),
            "ai_margin": int(40 * scale),
            "stats_margin": int(80 * scale),
            "stats_font": max(9, int(12 * scale)),
            "logo_size": int(80 * scale) if layout_manager.current == "wide" else 64,
            "title_font": int(42 * scale) if layout_manager.current == "wide" else 38,
            "motto_font": int(12 * scale) if layout_manager.current == "wide" else 11,
        }
    
    # ------------------------------------------------------------------
    # Height adaptation (replaces scrolling)
    # ------------------------------------------------------------------

    def _ai_height(self, level):
        """Fixed height of the AI assistant box at a given density level."""
        if layout_manager.current == "compact":
            base = 150
        else:
            response_max_h = 100
            input_row_h = 34
            vertical_chrome = 10 + 10 + 4
            content_height = response_max_h + input_row_h + vertical_chrome
            base = min(200, max(150, int(content_height * (1 + (layout_manager.font_scale() - 1) * 0.4))))
        caps = {0: base, 1: 140, 2: 122, 3: 104}
        return min(base, caps.get(level, 104))

    def _density_params(self, level):
        """Sizes/margins for the header, AI box and stats at a density level."""
        v = self._get_dynamic_values()
        compact = layout_manager.current == "compact"
        stats_font = max(8, v["stats_font"] - 1) if compact else v["stats_font"]

        d = {
            "logo": v["logo_size"], "title": v["title_font"], "motto": v["motto_font"],
            "show_motto": True,
            "top": 20, "bottom": 30,
            "search_top": 16, "sep_top": 16, "sep_bottom": 18,
            "ai_m_top": 6 if compact else 12, "ai_m_bottom": 8 if compact else 12,
            "stats_m": 4 if compact else 8, "stats_font": stats_font,
        }
        if level >= 1:
            d.update(logo=min(d["logo"], 52), title=min(d["title"], 32), motto=min(d["motto"], 10),
                     top=14, bottom=20, search_top=10, sep_top=10, sep_bottom=12)
        if level >= 2:
            d.update(logo=min(d["logo"], 40), title=min(d["title"], 26),
                     top=10, bottom=12, search_top=8, sep_top=6, sep_bottom=8,
                     ai_m_top=min(d["ai_m_top"], 4), ai_m_bottom=min(d["ai_m_bottom"], 4),
                     stats_m=min(d["stats_m"], 3))
        if level >= 3:
            d.update(logo=min(d["logo"], 32), title=min(d["title"], 22), show_motto=False,
                     top=6, bottom=8, search_top=6, sep_top=4, sep_bottom=4,
                     ai_m_top=2, ai_m_bottom=2, stats_m=2)
        return d

    def _estimate_fixed_height(self, level):
        """Height used by everything except the category cards (slightly generous)."""
        p = self._density_params(level)
        title_h = int(p["title"] * 1.5)
        motto_h = int(p["motto"] * 1.6) if p["show_motto"] else 0
        stats_h = int(p["stats_font"] * 1.7)
        search_h = 46
        return (p["top"] + p["bottom"] + p["logo"] + title_h + motto_h
                + p["search_top"] + search_h
                + 1 + p["sep_top"] + p["sep_bottom"]
                + p["ai_m_top"] + p["ai_m_bottom"] + self._ai_height(level)
                + 2 * p["stats_m"] + stats_h)

    def _pick_density(self):
        """Lowest density level that still leaves the cards a comfortable height."""
        page_h = self.height()
        if not self.isVisible() or page_h < 200:
            # Not shown yet: estimate from the layout's planned window size
            page_h = layout_manager.get_window_size()[1] - 70
        wanted_cards_h = self._wanted_cards_height()
        for level in range(4):
            if page_h - self._estimate_fixed_height(level) >= wanted_cards_h:
                return max(level, self._min_density)
        return 3

    def _wanted_cards_height(self):
        return 150 if layout_manager.current == "compact" else 170

    def _verify_fit(self):
        """Self-check after a build: use the REAL space the cards got.

        The density level is chosen from height estimates. If the real fonts
        and widgets turned out taller than estimated, the cards got less room
        than intended - step the page one level tighter and rebuild.
        """
        if not self.isVisible() or self.card_grid is None:
            return
        try:
            cards_h = self.card_grid.height()
        except RuntimeError:
            return
        if cards_h < self._wanted_cards_height() and self._density < 3:
            self._min_density = self._density + 1
            self._min_density_height = self.height()
            self._on_layout_changed(layout_manager.current)

    def _on_layout_changed(self, layout_type):
        """Rebuild UI when layout changes."""
        saved_response = getattr(self, '_saved_ai_response', "")

        self.setUpdatesEnabled(False)
        try:
            self._init_ui()
        finally:
            self.setUpdatesEnabled(True)

        if saved_response:
            self._saved_ai_response = saved_response
            if hasattr(self, 'ai_response'):
                self.ai_response.setHtml(saved_response)
                self.ai_response.show()
    
    def _clear_layout(self, layout):
        """Recursively remove and schedule deletion of all widgets in a layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def _init_ui(self):
        if self.layout():
            self._clear_layout(self.layout())
            old_layout = self.layout()
            QWidget().setLayout(old_layout)

        # Drop anything that points into the widgets that were just removed
        self._stop_thinking_animation()
        self._thinking_container = None
        self._ai_icon_movie = None
        self._ai_icon_idle = True

        # Pick how compact the page must be to fit the current window height
        self._density = self._pick_density()
        p = self._density_params(self._density)
        self._params = p
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, p["top"], 0, p["bottom"])
        
        values = self._get_dynamic_values()
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_wrapper = QWidget()
        logo_wrapper.setStyleSheet("background: transparent;")
        logo_wrapper_layout = QHBoxLayout(logo_wrapper)
        logo_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        logo_wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_label = QLabel()
        logo_path = self._find_logo()
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_size = p["logo"]
            scaled = pixmap.scaled(logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled)
            logo_label.setFixedSize(logo_size, logo_size)
        else:
            logo_label.setFixedSize(p["logo"], p["logo"])
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        logo_wrapper_layout.addWidget(logo_label)
        
        title = QLabel("sokonalysis")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = p["title"]
        title.setStyleSheet(f"font-size: {title_font}px; font-weight: 800; letter-spacing: 2px; background: transparent;")
        
        motto = QLabel("The Cipher Toolkit Built For All Skill Levels")
        motto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        motto_font = p["motto"]
        motto.setStyleSheet(f"font-size: {motto_font}px; font-weight: 500; background: transparent; letter-spacing: 0.5px; color: {self.theme.current['text_tertiary']};")
        
        header_layout.addWidget(logo_wrapper)
        header_layout.addWidget(title)
        if p["show_motto"]:
            header_layout.addWidget(motto)
        
        t = self.theme.current
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        search_icon_path = os.path.join(icons_dir, "search.png")
        
        # SEARCH
        search_wrapper = QHBoxLayout()
        search_wrapper.setContentsMargins(values["search_margin"], p["search_top"], values["search_margin"], 0)
        
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet(f"QFrame#searchContainer{{background-color:{t['surface0']};border:2px solid {t['border']};border-radius:20px;}}")
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 2, 8, 2)
        search_layout.setSpacing(10)
        
        search_icon_label = QLabel()
        if os.path.exists(search_icon_path):
            search_icon_label.setPixmap(QPixmap(search_icon_path).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        search_icon_label.setFixedSize(18, 18)
        search_icon_label.setStyleSheet("background: transparent;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("")
        self.search_input.setObjectName("searchInput")
        self.search_input.setMinimumHeight(36)
        self.search_input.returnPressed.connect(self._on_search_enter)
        self.search_input.setStyleSheet(f"QLineEdit#searchInput{{background:transparent;border:none;color:{t['text']};font-size:14px;}}")
        
        self.search_status = QLabel("")
        self.search_status.setFixedWidth(28)
        self.search_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_status.setStyleSheet("font-size:14px;font-weight:bold;background:transparent;border-radius:14px;")
        
        search_layout.addWidget(search_icon_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_status)
        search_wrapper.addWidget(search_container)
        
        sep_wrapper = QHBoxLayout()
        sep_wrapper.setContentsMargins(80, 0, 80, 0)
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color:{t['border']};margin:{p['sep_top']}px 0px {p['sep_bottom']}px 0px;")
        sep_wrapper.addWidget(sep)
        
        # CATEGORIES
        categories = [
            ("Symmetric", "Classical and modern cipher algorithms for encryption and decryption"),
            ("Asymmetric", "Public-key cryptography for secure key exchange and signatures"),
            ("Hashing", "Generate and reverse cryptographic hash values of any type"),
            ("Advanced", "Password cracking and file recovery for security audits"),
            ("CTF", "Capture the Flag tools for cybersecurity competitions"),
        ]
        
        self.card_grid = CardGrid(force_single_row=True)
        self.card_grid.add_cards(categories, self.theme, self.on_category_clicked)
        
        # === AI ASSISTANT ===
        ai_wrapper = QHBoxLayout()
        
        if layout_manager.current == "compact":
            ai_wrapper.setContentsMargins(20, p["ai_m_top"], 20, p["ai_m_bottom"])
        else:
            ai_wrapper.setContentsMargins(values["ai_margin"], p["ai_m_top"], values["ai_margin"], p["ai_m_bottom"])
        ai_height = self._ai_height(self._density)
        
        ai_container = QFrame()
        ai_container.setFixedHeight(ai_height)
        ai_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ai_container.setStyleSheet(f"QFrame{{background:transparent;border:1px solid {t['border']};border-radius:12px;}}")
        ai_container.setAcceptDrops(True)
        ai_container.dragEnterEvent = self.dragEnterEvent
        ai_container.dropEvent = self.dropEvent
        
        ai_layout = QVBoxLayout(ai_container)
        ai_layout.setContentsMargins(14, 10, 14, 10)
        ai_layout.setSpacing(4)
        
        ai_input_row = QHBoxLayout()
        ai_input_row.setSpacing(8)
        
        fonts = font_controller.get_font_sizes()
        input_font = fonts["input"]
        response_font = fonts["body"]
        
        # AI Response (top area)
        self.ai_response = ClickableTextBrowser()
        self.ai_response.setReadOnly(True)
        self.ai_response.setOpenExternalLinks(False)
        self.ai_response.link_clicked.connect(self._on_ai_link_clicked)
        self.ai_response.setStyleSheet(f"""
            QTextBrowser{{
                background:transparent;
                border:none;
                color:{t['text_secondary']};
                font-size:{response_font}px;
                padding:2px 0;
            }}
        """)
        self.ai_response.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # The response area is short, so tighten the default block margins of
        # the rendered HTML; otherwise headings waste most of the visible space.
        self.ai_response.document().setDefaultStyleSheet(
            "h1,h2,h3,h4,h5,h6{margin-top:2px;margin-bottom:3px;}"
            "p{margin-top:0px;margin-bottom:3px;}"
            "ul,ol{margin-top:2px;margin-bottom:2px;}"
        )
        
        base_response_h = 70 if layout_manager.current == "compact" else 100
        self.ai_response.setMaximumHeight(max(36, min(base_response_h, ai_height - 58)))
        
        if self._saved_ai_response:
            self.ai_response.setHtml(self._saved_ai_response)
            self.ai_response.show()
        else:
            self.ai_response.hide()
        
        # AI Input (bottom area)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask Assistant about any tool... (or drop files here)")
        self.ai_input.setMinimumHeight(30)
        self.ai_input.setStyleSheet(f"""
            QLineEdit{{
                background:transparent;
                border:none;
                color:{t['text_secondary']};
                font-size:{input_font}px;
                padding:4px 0;
            }}
            QLineEdit:focus{{
                color:{t['text']};
            }}
        """)
        self.ai_input.returnPressed.connect(self._ask_ai)
        
        # AI Icon (animated logo.gif — plays once on click, then returns to idle)
        self.ai_icon_label = QLabel()
        self.ai_icon_label.setFixedSize(24, 24)
        self.ai_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ai_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_icon_label.setStyleSheet("background: transparent; border: none;")
        self.ai_icon_label.mousePressEvent = self._on_ai_icon_clicked
        
        logo_gif_path = self._get_logo_gif_path()
        if logo_gif_path and os.path.exists(logo_gif_path):
            self._ai_icon_movie = QMovie(logo_gif_path)
            self._ai_icon_movie.setScaledSize(QSize(24, 24))
            self._ai_icon_movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self.ai_icon_label.setMovie(self._ai_icon_movie)
            # Show first frame idle (no looping)
            self._ai_icon_movie.jumpToFrame(0)
            self._ai_icon_movie.setPaused(True)
            self._ai_icon_movie.frameChanged.connect(self._on_ai_icon_frame_changed)
            self._ai_icon_idle = True
        else:
            self.ai_icon_label.setText("AI")
            self.ai_icon_label.setStyleSheet(f"color: {t['accent']}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        
        ai_input_row.addWidget(self.ai_input)
        ai_input_row.addWidget(self.ai_icon_label)
        
        # Add response first (top), then input row (bottom)
        ai_layout.addWidget(self.ai_response)
        ai_layout.addLayout(ai_input_row)
        ai_wrapper.addWidget(ai_container)
        
        # === STATS ===
        stats_wrapper = QHBoxLayout()
        
        if layout_manager.current == "compact":
            stats_wrapper.setContentsMargins(20, p["stats_m"], 20, p["stats_m"])
        else:
            stats_wrapper.setContentsMargins(values["stats_margin"], p["stats_m"], values["stats_margin"], p["stats_m"])
        stats_font_size = p["stats_font"]
        
        stats_bar = QWidget()
        stats_bar.setStyleSheet("background:transparent;")
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(0)
        
        self.left_stat = QLabel("Runtime: 00:00:00")
        self.left_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        self.left_stat.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.center_stat = QLabel("Operations: 0")
        self.center_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        self.center_stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.right_stat = QLabel("Last: None")
        self.right_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        self.right_stat.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        stats_layout.addWidget(self.left_stat)
        stats_layout.addWidget(self.center_stat)
        stats_layout.addWidget(self.right_stat)
        stats_wrapper.addWidget(stats_bar)
        
        layout.addLayout(header_layout)
        layout.addLayout(search_wrapper)
        layout.addLayout(sep_wrapper)
        
        card_grid_wrapper = QHBoxLayout()
        if layout_manager.current == "compact":
            card_grid_wrapper.setContentsMargins(20, 0, 20, 0)
        else:
            card_grid_wrapper.setContentsMargins(values["ai_margin"], 0, values["ai_margin"], 0)
        card_grid_wrapper.addWidget(self.card_grid)
        # Stretch = 1: the cards take all spare vertical space; the header and
        # the AI box keep their own (density-adjusted) size, so they never overlap.
        layout.addLayout(card_grid_wrapper, 1)
        
        layout.addLayout(ai_wrapper)
        layout.addLayout(stats_wrapper)

        QTimer.singleShot(250, self._verify_fit)
    
    def _on_ai_icon_clicked(self, event=None):
        """Clear the AI response AND play the GIF once from the start."""
        # 1) Clear text (same behavior as the old _clear_ai)
        self._stop_thinking_animation()
        self._hide_thinking_container()
        self.ai_response.clear()
        self.ai_response.hide()
        self._saved_ai_response = ""
        self.ai_input.clear()
        self.ai_input.setPlaceholderText("Ask Assistant about any tool... (or drop files here)")

        # 2) Play the GIF once from the start
        if getattr(self, '_ai_icon_movie', None):
            self._ai_icon_idle = False
            self._ai_icon_movie.stop()
            self._ai_icon_movie.jumpToFrame(0)
            self._ai_icon_movie.setPaused(False)
            self._ai_icon_movie.start()

    def _on_ai_icon_frame_changed(self, frame):
        """Let the GIF play to its true end, then snap back to idle (frame 0)."""
        movie = getattr(self, '_ai_icon_movie', None)
        if movie is None or self._ai_icon_idle:
            return

        last = movie.frameCount() - 1
        if last <= 0:
            return

        # Leave a small buffer before the final frame so the last visible
        # frame actually renders before we reset.
        if frame >= last - 1:
            delay = max(120, movie.nextFrameDelay() + 60)
            QTimer.singleShot(delay, self._reset_ai_icon_to_idle)

    def _reset_ai_icon_to_idle(self):
        """Stop the movie, snap back to frame 0, and pause (idle state)."""
        movie = getattr(self, '_ai_icon_movie', None)
        if movie is None:
            return
        movie.stop()
        movie.jumpToFrame(0)
        movie.setPaused(True)
        self._ai_icon_idle = True
    
    def _clear_ai(self, event=None):
        self._stop_thinking_animation()
        self._hide_thinking_container()
        self.ai_response.clear()
        self.ai_response.hide()
        self._saved_ai_response = ""
        self.ai_input.clear()
        self.ai_input.setPlaceholderText("Ask Assistant about any tool... (or drop files here)")
    
    def _ask_ai(self):
        question = self.ai_input.text().strip()
        if not question:
            return
        self.ai_input.setEnabled(False)
        self._show_thinking_animation("Thinking...")
        self.ai_worker = AIAssistantWorker(question)
        self.ai_worker.response_ready.connect(self._on_ai_response)
        self.ai_worker.action_requested.connect(self._on_ai_action)
        self.ai_worker.progress_update.connect(self._on_ai_progress)
        self.ai_worker.start()
    
    def _ask_ai_with_text(self, text):
        self.ai_input.setText(text)
        self._ask_ai()
    
    def _on_ai_action(self, action_type, value):
        main_window = self.window()
        if not main_window:
            return
    
        if action_type == 'toggle_theme':
            if hasattr(main_window, '_toggle_theme'):
                main_window._toggle_theme()
        elif action_type == 'layout':
            if hasattr(main_window, '_apply_layout'):
                main_window._apply_layout(value)
        elif action_type == 'show_user_guide':
            if hasattr(main_window, '_show_user_guide'):
                main_window._show_user_guide()
        elif action_type == 'show_license':
            if hasattr(main_window, '_show_license'):
                main_window._show_license()
        elif action_type == 'show_about':
            if hasattr(main_window, '_show_about'):
                main_window._show_about()
        elif action_type == 'check_updates':
            from gui.updater import check_for_updates
            check_for_updates(main_window)
        elif action_type == 'show_landing':
            if hasattr(main_window, '_show_landing'):
                main_window._show_landing()
        elif action_type == 'show_config':
            if value == 'wordlist':
                main_window._show_configurations()
            elif value == 'json':
                main_window._show_json_config()
            elif value == 'john':
                main_window._show_john_config()
        elif action_type == 'quit_app':
            main_window.close()
        elif action_type == 'navigate_option':
            if hasattr(main_window, '_on_category_option_clicked'):
                main_window._on_category_option_clicked(value)
    
    def _on_ai_progress(self, message):
        """Handle progress updates - update text in container."""
        if hasattr(self, '_thinking_container') and self._thinking_container:
            for child in self._thinking_container.findChildren(QLabel):
                if not child.movie() and child.text():
                    child.setText(message)
                    return
        self._show_thinking_animation(message)
    
    def _on_ai_response(self, response):
        self._stop_thinking_animation()
        self._hide_thinking_container()
        self.ai_response.show()
        self.ai_response.setHtml(response)
        self._saved_ai_response = response
        self.ai_input.setEnabled(True)
        self.ai_input.clear()
        self.ai_input.setPlaceholderText("Ask Assistant about any tool... (or drop files here)")
    
    def _on_ai_link_clicked(self, url_str):
        main_window = self.window()
        if not main_window:
            return
    
        if '/search/' in url_str:
            tool_name = unquote(url_str.split('/search/')[1])
            if hasattr(main_window, '_handle_search'):
                main_window._handle_search(tool_name)
    
        elif '/config/' in url_str:
            config_type = url_str.split('/config/')[1]
            if config_type == 'wordlist':
                main_window._show_configurations()
            elif config_type == 'json':
                main_window._show_json_config()
            elif config_type == 'john':
                main_window._show_john_config()
    
        elif '/cipher/' in url_str:
            cipher = url_str.split('/cipher/')[1]
            self._ask_ai_with_text(f"crack {cipher}")
    
        elif '/option/' in url_str:
            parts = url_str.split('/option/')[1].split('/', 1)
            option_name = unquote(parts[0])
            extra_data = unquote(parts[1]) if len(parts) > 1 and parts[1] != 'none' else ""
            
            if hasattr(main_window, '_on_category_option_clicked'):
                main_window._on_category_option_clicked(option_name)
            
            if extra_data and os.path.exists(extra_data):
                QTimer.singleShot(500, lambda: self._set_file_in_current_page(main_window, extra_data))
            elif extra_data:
                QTimer.singleShot(500, lambda: self._set_text_in_current_page(main_window, extra_data))
    
    def _set_text_in_current_page(self, main_window, text):
        current_page = main_window.stack.currentWidget()
        if current_page:
            for attr_name in ['ciphertext_input', 'input_text', 'text_input',
                              'cipher_input', 'message_input', 'plaintext_input',
                              'ct_input', 'input_field', 'text_edit', 'hash_input',
                              'ciphertext', 'input_box', 'text_area']:
                if hasattr(current_page, attr_name):
                    widget = getattr(current_page, attr_name)
                    if hasattr(widget, 'setText'):
                        widget.setText(text)
                        return
                    elif hasattr(widget, 'setPlainText'):
                        widget.setPlainText(text)
                        return
    
    def _set_file_in_current_page(self, main_window, file_path):
        current_page = main_window.stack.currentWidget()
        if current_page:
            for attr_name in ['file_path', 'file_input', 'target_file', 
                              'archive_path', 'document_path', 'input_file']:
                if hasattr(current_page, attr_name):
                    widget = getattr(current_page, attr_name)
                    if hasattr(widget, 'setText'):
                        widget.setText(file_path)
                        return
                    elif hasattr(widget, 'setPlainText'):
                        widget.setPlainText(file_path)
                        return
    
    def _on_search_enter(self):
        text = self.search_input.text().strip()
        if text:
            self.search_requested.emit(text)
            self.search_input.clear()
            self.search_status.setText("")
    
    def _update_runtime(self):
        if LandingPage.app_start_time:
            delta = datetime.now() - LandingPage.app_start_time
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            self.left_stat.setText(f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        self.center_stat.setText(f"Operations: {LandingPage.total_operations}")
        self.right_stat.setText(f"Last: {LandingPage.last_activity[:25] if LandingPage.last_activity else 'None'}")
    
    def resizeEvent(self, event):
        """Debounced resize handling."""
        super().resizeEvent(event)
        if self._min_density and self.height() > self._min_density_height + 30:
            self._min_density = 0
        first = not hasattr(self, '_last_width')
        width_changed = (not first) and abs(self.width() - self._last_width) > 50
        # Rebuild when the window height crosses into a different density level
        density_changed = self.isVisible() and self._pick_density() != self._density

        if first or width_changed:
            self._last_width = self.width()

        if width_changed or density_changed:
            if not hasattr(self, '_resize_debounce_timer'):
                self._resize_debounce_timer = QTimer(self)
                self._resize_debounce_timer.setSingleShot(True)
                self._resize_debounce_timer.timeout.connect(
                    lambda: self._on_layout_changed(layout_manager.current)
                )
            self._resize_debounce_timer.start(150)
    
    def refresh_theme(self):
        t = self.theme.current
        fonts = font_controller.get_font_sizes()
        input_font = fonts["input"]
        response_font = fonts["body"]
        
        # Use the sizes the page was actually built with (density-adjusted),
        # otherwise toggling the theme would bring back the full-size header.
        p = self._params or self._density_params(self._density)
        stats_font_size = p["stats_font"]
        logo_size = p["logo"]
        title_font = p["title"]
        motto_font = p["motto"]
        
        for child in self.findChildren(QLabel):
            if child.pixmap() is not None:
                logo_path = self._find_logo()
                if logo_path:
                    pixmap = QPixmap(logo_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(logo_size, logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        child.setPixmap(scaled)
                        child.setFixedSize(logo_size, logo_size)
                break
        
        for child in self.findChildren(QLabel):
            if child.text() == "sokonalysis":
                child.setStyleSheet(f"font-size: {title_font}px; font-weight: 800; letter-spacing: 2px; background: transparent;")
            elif child.text() == "The Cipher Toolkit Built For All Skill Levels":
                child.setStyleSheet(f"font-size: {motto_font}px; font-weight: 500; background: transparent; letter-spacing: 0.5px; color: {t['text_tertiary']};")
        
        for child in self.findChildren(QFrame, "searchContainer"):
            child.setStyleSheet(f"QFrame#searchContainer{{background-color:{t['surface0']};border:2px solid {t['border']};border-radius:20px;}}")
        self.search_input.setStyleSheet(f"QLineEdit#searchInput{{background:transparent;border:none;color:{t['text']};font-size:14px;}}")
        
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)
        
        self.left_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        self.center_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        self.right_stat.setStyleSheet(f"color:{t['text_tertiary']};font-size:{stats_font_size}px;background:transparent;font-family:'JetBrains Mono',monospace;")
        
        if hasattr(self, 'ai_input'):
            self.ai_input.setStyleSheet(f"""
                QLineEdit{{
                    background:transparent;
                    border:none;
                    color:{t['text_secondary']};
                    font-size:{input_font}px;
                    padding:4px 0;
                }}
                QLineEdit:focus{{
                    color:{t['text']};
                }}
            """)
        if hasattr(self, 'ai_response'):
            self.ai_response.setStyleSheet(f"""
                QTextBrowser{{
                    background:transparent;
                    border:none;
                    color:{t['text_secondary']};
                    font-size:{response_font}px;
                    padding:2px 0;
                }}
            """)
        if hasattr(self, 'ai_icon_label'):
            current_text = self.ai_icon_label.text()
            if current_text == "AI":
                self.ai_icon_label.setStyleSheet(f"color: {t['accent']}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
