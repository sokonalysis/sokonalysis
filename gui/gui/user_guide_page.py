# gui/user_guide_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QApplication, QMenu
)
from PySide6.QtCore import Qt, QSize, QUrl, QTimer, QRectF, QRect, Signal
from PySide6.QtGui import (
    QIcon, QPixmap, QImage, QDesktopServices, QPainter, QColor, QKeySequence,
    QPalette
)
import os, re, sys, fitz, subprocess, shutil, threading


class PdfPageWidget(QWidget):
    """One PDF page: a smoothly scaled bitmap plus a selectable text layer.

    Word boxes come from PyMuPDF (in PDF points, reading order). Selection is
    a range of word indexes, so it follows the natural flow of the text.
    """

    selection_started = Signal(object)   # emits self, so siblings can clear
    link_activated = Signal(object)      # emits an action dict (uri / goto / named)

    SELECTION_COLOR = QColor(51, 144, 255, 90)
    URL_RE = re.compile(r'^(?:https?://|www\.)\S+', re.IGNORECASE)

    def __init__(self, pt_width, pt_height, theme_manager, parent=None):
        super().__init__(parent)
        self._theme = theme_manager
        self._pt_w = pt_width or 1.0
        self._pt_h = pt_height or 1.0
        self._pixmap = None
        self._words = []          # (x0, y0, x1, y1, text, block, line, word_no)
        self._links = []          # (x0, y0, x1, y1, action_dict)
        self._press_link = None
        self._press_pos = None
        self._anchor = None
        self._cursor_idx = None
        self._dragging = False
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setMouseTracking(True)

    # --- content -------------------------------------------------------
    def set_content(self, pixmap, words, links=()):
        self._pixmap = pixmap
        self._words = words
        self._links = list(links)
        self.update()

    def clear_pixmap(self):
        """Free the bitmap (keeps words/selection)."""
        self._pixmap = None
        self.update()

    def clear_selection(self):
        self._anchor = self._cursor_idx = None
        self._dragging = False
        self.update()

    # --- geometry / hit testing ---------------------------------------
    def _scale(self):
        return self.width() / self._pt_w

    def _word_at(self, pos, nearest=False):
        s = self._scale()
        px, py = pos.x() / s, pos.y() / s
        best, best_d = None, None
        for i, w in enumerate(self._words):
            dx = max(w[0] - px, 0, px - w[2])
            dy = max(w[1] - py, 0, py - w[3])
            if dx == 0 and dy == 0:
                return i
            if nearest:
                d = dx * dx + 4 * dy * dy      # favour words on the same line
                if best_d is None or d < best_d:
                    best, best_d = i, d
        return best

    def _link_at(self, pos):
        """Return the link action under pos, or None."""
        s = self._scale()
        px, py = pos.x() / s, pos.y() / s
        for x0, y0, x1, y1, action in self._links:
            if x0 <= px <= x1 and y0 <= py <= y1:
                return action
        # Fallback: plain-text URLs that have no link annotation
        idx = self._word_at(pos)
        if idx is not None:
            text = self._words[idx][4].rstrip(".,;:!?)]}'\"")
            if self.URL_RE.match(text):
                if text.lower().startswith("www."):
                    text = "https://" + text
                return {"type": "uri", "uri": text}
        return None

    def _selection_range(self):
        if self._anchor is None or self._cursor_idx is None or not self._words:
            return None
        n = len(self._words) - 1
        lo = min(self._anchor, self._cursor_idx, n)
        hi = min(max(self._anchor, self._cursor_idx), n)
        return lo, hi

    def selected_text(self):
        rng = self._selection_range()
        if not rng:
            return ""
        lo, hi = rng
        out, prev = [], None
        for w in self._words[lo:hi + 1]:
            key = (w[5], w[6])
            if prev is not None:
                out.append(" " if key == prev else "\n")
            out.append(w[4])
            prev = key
        return "".join(out)

    def copy_selection(self):
        text = self.selected_text()
        if text:
            QApplication.clipboard().setText(text)

    def select_all(self):
        if self._words:
            self.selection_started.emit(self)
            self._anchor, self._cursor_idx = 0, len(self._words) - 1
            self.update()

    # --- painting ------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        bg = QColor(self._theme.current['base']) if self._theme.is_dark else QColor("white")
        p.fillRect(self.rect(), bg)
        if self._pixmap is not None:
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            p.drawPixmap(QRectF(self.rect()), self._pixmap, QRectF(self._pixmap.rect()))

        rng = self._selection_range()
        if rng:
            s = self._scale()
            lo, hi = rng
            words = self._words
            for i in range(lo, hi + 1):
                x0, y0, x1, y1 = words[i][:4]
                # bridge the gap to the next word on the same line
                if i < hi and words[i + 1][5:7] == words[i][5:7]:
                    x1 = max(x1, words[i + 1][0])
                p.fillRect(
                    QRectF(x0 * s, y0 * s, (x1 - x0) * s, (y1 - y0) * s),
                    self.SELECTION_COLOR
                )
        p.end()

    # --- mouse / keyboard ---------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self.setFocus()
        self.selection_started.emit(self)
        self._press_link = self._link_at(event.position())
        self._press_pos = event.position()
        idx = self._word_at(event.position())
        if idx is None:
            self.clear_selection()
        else:
            self._anchor = self._cursor_idx = idx
            self._dragging = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            idx = self._word_at(event.position(), nearest=True)
            if idx is not None and idx != self._cursor_idx:
                self._cursor_idx = idx
                self.update()
            return

        link = self._link_at(event.position())
        if link is not None:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip(link["uri"] if link["type"] == "uri" else "")
        else:
            self.setToolTip("")
            over_text = self._word_at(event.position()) is not None
            self.setCursor(
                Qt.CursorShape.IBeamCursor if over_text else Qt.CursorShape.ArrowCursor
            )

    def mouseReleaseEvent(self, event):
        self._dragging = False
        link, self._press_link = self._press_link, None
        if link is not None and event.button() == Qt.MouseButton.LeftButton:
            moved = (event.position() - self._press_pos).manhattanLength()
            # A click (not a drag) on the same link that was pressed
            if moved < 5 and self._link_at(event.position()) == link:
                self.clear_selection()
                self.link_activated.emit(link)

    def mouseDoubleClickEvent(self, event):
        idx = self._word_at(event.position())
        if idx is not None:
            self.selection_started.emit(self)
            self._anchor = self._cursor_idx = idx
            self.update()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection()
        elif event.matches(QKeySequence.StandardKey.SelectAll):
            self.select_all()
        else:
            super().keyPressEvent(event)

    def _style_menu(self, menu):
        """Make the popup follow the current light/dark theme."""
        t = self._theme.current
        pal = menu.palette()
        for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base):
            pal.setColor(role, QColor(t['base']))
        for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text):
            pal.setColor(role, QColor(t['text']))
        menu.setPalette(pal)
        menu.setAutoFillBackground(True)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {t['base']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 0px;
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {t['text']};
                padding: 6px 24px 6px 12px;
            }}
            QMenu::item:selected {{
                background-color: {t['hover']};
                color: {t['text']};
            }}
            QMenu::item:disabled {{
                color: {t['text_tertiary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {t['border']};
                margin: 4px 6px;
            }}
        """)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        self._style_menu(menu)

        link = self._link_at(event.pos())
        if link is not None and link["type"] == "uri":
            open_act = menu.addAction("Open Link")
            open_act.triggered.connect(lambda: self.link_activated.emit(link))
            copy_link_act = menu.addAction("Copy Link Address")
            copy_link_act.triggered.connect(
                lambda: QApplication.clipboard().setText(link["uri"])
            )
            menu.addSeparator()

        copy_act = menu.addAction("Copy")
        copy_act.setEnabled(bool(self.selected_text()))
        copy_act.triggered.connect(self.copy_selection)
        all_act = menu.addAction("Select All on Page")
        all_act.setEnabled(bool(self._words))
        all_act.triggered.connect(self.select_all)
        menu.exec(event.globalPos())


class UserGuidePage(QWidget):
    """User guide page with lazy, incremental embedded PDF viewer."""

    _uri_failed = Signal(str)    # emitted (from a worker thread) if no browser opened

    # How far (in viewport heights) around the viewport pages get rendered
    RENDER_BUFFER = 1.0
    # Pages further than this (in viewport heights) from the viewport are freed
    KEEP_BUFFER = 2.0
    # Render this many times larger than displayed, then smooth-scale down
    SUPERSAMPLE = 2.0
    # Safety cap on rendered bitmap width (pixels)
    MAX_RENDER_WIDTH = 3000

    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback

        self._guide_path = self._find_guide_path()
        self._doc = None
        self._page_sizes = []        # (width, height) in PDF points
        self._page_widgets = []
        self._num_labels = []
        self._rendered = set()       # indexes of pages currently holding a pixmap
        self._queue = []
        self._pump_scheduled = False
        self._page_width = 0
        self._dpr = 1.0
        self._render_dark = self.theme.is_dark   # theme the cached pages were drawn in

        self._uri_failed.connect(self._on_uri_failed)
        self.theme.theme_changed.connect(self._on_theme_changed)

        # Debounce timers
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(30)
        self._scroll_timer.timeout.connect(self._render_visible)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(120)
        self._resize_timer.timeout.connect(self._on_layout_settled)

        self._init_ui()

    # ------------------------------------------------------------------
    # Paths / external open
    # ------------------------------------------------------------------
    @staticmethod
    def _base_dir():
        return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..')

    def _find_guide_path(self):
        base = self._base_dir()
        for p in (
            os.path.join(base, 'assets', 'docs', 'guide.pdf'),
            os.path.join(base, 'assets', 'guide.pdf'),
        ):
            if os.path.exists(p):
                return p
        return None

    def _get_guide_path(self):
        return self._guide_path

    def _get_clean_env(self):
        """Environment to use when launching an external process.

        When frozen with PyInstaller, the bootloader points LD_LIBRARY_PATH
        (and sometimes PYTHONHOME/PYTHONPATH) at the bundled libs. Child
        processes inherit that, so external viewers try to load our bundled
        shared libraries. PyInstaller backs up the original values in *_ORIG
        variables so subprocesses can be restored to a normal environment.
        """
        env = dict(os.environ)
        if hasattr(sys, '_MEIPASS'):
            for var, orig_var in (
                ('LD_LIBRARY_PATH', 'LD_LIBRARY_PATH_ORIG'),
                ('PYTHONHOME', 'PYTHONHOME_ORIG'),
                ('PYTHONPATH', 'PYTHONPATH_ORIG'),
            ):
                orig_value = env.get(orig_var)
                if orig_value is not None:
                    env[var] = orig_value
                else:
                    env.pop(var, None)
        return env

    def _open_externally(self):
        """Open the PDF in the system's default PDF viewer."""
        guide_path = self._get_guide_path()
        if not guide_path:
            QMessageBox.warning(self, "Not Found", "User guide PDF not found.")
            return

        viewers = [
            ['atril', guide_path], ['evince', guide_path], ['okular', guide_path],
            ['qpdfview', guide_path], ['firefox', guide_path], ['chromium', guide_path],
            ['google-chrome', guide_path], ['gio', 'open', guide_path],
            ['gvfs-open', guide_path], ['gnome-open', guide_path], ['xdg-open', guide_path],
        ]

        clean_env = self._get_clean_env()

        for cmd in viewers:
            if shutil.which(cmd[0]):
                try:
                    with open(os.devnull, 'w') as devnull:
                        proc = subprocess.Popen(
                            cmd, stdout=devnull, stderr=devnull, env=clean_env
                        )
                    QApplication.processEvents()
                    if proc.poll() is not None and proc.returncode != 0:
                        continue
                    return
                except Exception:
                    continue

        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(guide_path))
        except Exception:
            QMessageBox.warning(
                self, "Error",
                "Could not find a PDF viewer.\n\n"
                f"Guide location:\n{guide_path}"
            )

    # ------------------------------------------------------------------
    # Document / geometry
    # ------------------------------------------------------------------
    def _get_page_width(self):
        w = self.width()
        if w > 100:
            return min(w - 60, 1200)
        return 900

    def _open_document(self):
        """Open the PDF and read page sizes only (fast, no rasterizing)."""
        # guide.pdf's tagged-accessibility structure tree is malformed, which
        # is harmless but spams stderr, so silence MuPDF while we work.
        fitz.TOOLS.mupdf_display_errors(False)
        try:
            self._doc = fitz.open(self._guide_path)
            self._page_sizes = []
            for i in range(len(self._doc)):
                r = self._doc.load_page(i).rect
                self._page_sizes.append((r.width, r.height))
        except Exception as e:
            self._doc = None
            self._show_error(f"Error loading guide: {e}")
        finally:
            fitz.TOOLS.mupdf_display_errors(True)
        return self._doc is not None

    def _show_error(self, text):
        t = self.theme.current
        error_label = QLabel(text)
        error_label.setStyleSheet(
            f"color:{t['error']};font-size:14px;background:transparent;padding:20px;"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        self.pages_layout.addWidget(error_label)

    def _page_height_for(self, index):
        w, h = self._page_sizes[index]
        return max(1, round(self._page_width * (h / w if w else 1.414)))

    def _build_placeholders(self):
        """Create correctly sized blank pages instantly; render nothing yet."""
        t = self.theme.current
        total = len(self._page_sizes)
        self._page_width = self._get_page_width()
        self._dpr = self.devicePixelRatioF()

        for i, (pw, ph) in enumerate(self._page_sizes):
            page_widget = PdfPageWidget(pw, ph, self.theme)
            page_widget.setFixedSize(self._page_width, self._page_height_for(i))
            page_widget.selection_started.connect(self._on_selection_started)
            page_widget.link_activated.connect(self._on_link_activated)
            self.pages_layout.addWidget(page_widget)
            self._page_widgets.append(page_widget)

            num_label = QLabel(f"{i + 1} / {total}")
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:10px;background:transparent;padding:2px;"
            )
            self.pages_layout.addWidget(num_label)
            self._num_labels.append(num_label)

    def _on_selection_started(self, sender):
        """Only one page holds a selection at a time."""
        for w in self._page_widgets:
            if w is not sender:
                w.clear_selection()

    # ------------------------------------------------------------------
    # Lazy rendering
    # ------------------------------------------------------------------
    def _render_visible(self):
        """Work out which pages are near the viewport and queue them."""
        if not self._doc or not self._page_widgets:
            return

        vbar = self.scroll.verticalScrollBar()
        view_h = max(1, self.scroll.viewport().height())
        top = vbar.value()
        center = top + view_h / 2

        lo = top - view_h * self.RENDER_BUFFER
        hi = top + view_h * (1 + self.RENDER_BUFFER)
        keep_lo = top - view_h * self.KEEP_BUFFER
        keep_hi = top + view_h * (1 + self.KEEP_BUFFER)

        wanted = []
        for i, w in enumerate(self._page_widgets):
            y, h = w.y(), w.height()
            if i in self._rendered and (y + h < keep_lo or y > keep_hi):
                w.clear_pixmap()                  # free memory for far-away pages
                self._rendered.discard(i)
            elif y + h >= lo and y <= hi and i not in self._rendered:
                wanted.append((abs(y + h / 2 - center), i))

        wanted.sort()                             # nearest to viewport center first
        self._queue = [i for _, i in wanted]
        self._schedule_pump()

    def _schedule_pump(self):
        if self._queue and not self._pump_scheduled:
            self._pump_scheduled = True
            QTimer.singleShot(0, self._pump)

    def _pump(self):
        """Render one page per event-loop tick so the UI never freezes."""
        self._pump_scheduled = False
        while self._queue:
            i = self._queue.pop(0)
            if i not in self._rendered:
                self._render_page(i)
                break
        self._schedule_pump()

    def _render_page(self, index):
        self._rendered.add(index)                 # mark first so failures don't loop
        fitz.TOOLS.mupdf_display_errors(False)
        try:
            page = self._doc.load_page(index)
            target_px = min(
                self._page_width * self._dpr * self.SUPERSAMPLE,
                self.MAX_RENDER_WIDTH
            )
            scale = target_px / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            img = QImage(
                pix.samples, pix.width, pix.height, pix.stride,
                QImage.Format.Format_RGB888
            ).convertToFormat(QImage.Format.Format_RGB32)   # copies, so pix can be freed
            if self.theme.is_dark:
                img = self._to_dark(img, page, scale)
            pixmap = QPixmap.fromImage(img)
            words = page.get_text("words")        # text layer for selection
            links = self._extract_links(page)     # clickable links / TOC entries
            self._page_widgets[index].set_content(pixmap, words, links)
        except Exception:
            pass
        finally:
            fitz.TOOLS.mupdf_display_errors(True)

    # ------------------------------------------------------------------
    # Links (external URLs and internal jumps such as the table of contents)
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_links(page):
        out = []
        for link in page.get_links():
            rect = link.get("from")
            if rect is None:
                continue
            kind = link.get("kind")
            action = None
            if kind == fitz.LINK_URI and link.get("uri"):
                action = {"type": "uri", "uri": link["uri"]}
            elif kind == fitz.LINK_GOTO and link.get("page", -1) >= 0:
                to = link.get("to")
                action = {"type": "goto", "page": link["page"],
                          "y": float(to.y) if to is not None else 0.0}
            elif kind == fitz.LINK_NAMED:
                name = link.get("nameddest") or link.get("name")
                if name:
                    action = {"type": "named", "name": name}
            if action:
                out.append((rect.x0, rect.y0, rect.x1, rect.y1, action))
        return out

    def _on_link_activated(self, action):
        kind = action.get("type")
        if kind == "uri":
            self._open_uri(action["uri"])
        elif kind == "goto":
            self._goto(action["page"], action.get("y", 0.0))
        elif kind == "named" and self._doc:
            try:
                res = self._doc.resolve_link("#" + action["name"])
                if res:
                    self._goto(res[0], res[2])
            except Exception:
                pass

    def _login_user_prefix(self):
        """Command prefix to launch a browser as the real desktop user.

        This app is often run as root (sudo) for the network tools, but
        browsers refuse to start as root, so xdg-open appears to do nothing.
        When running as root under sudo, launch the browser as SUDO_USER.
        """
        if not hasattr(os, 'geteuid') or os.geteuid() != 0:
            return []
        user = os.environ.get('SUDO_USER')
        if not user or user == 'root':
            return []
        try:
            import pwd
            pw = pwd.getpwnam(user)
        except Exception:
            return []

        if shutil.which('runuser'):
            wrapper = [shutil.which('runuser'), '-u', user, '--']
        elif shutil.which('sudo'):
            wrapper = [shutil.which('sudo'), '-u', user, '--']
        else:
            return []

        env_args = [f'HOME={pw.pw_dir}', f'XDG_RUNTIME_DIR=/run/user/{pw.pw_uid}']
        bus = f'/run/user/{pw.pw_uid}/bus'
        if os.path.exists(bus):
            env_args.append(f'DBUS_SESSION_BUS_ADDRESS=unix:path={bus}')
        for var in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION'):
            if os.environ.get(var):
                env_args.append(f'{var}={os.environ[var]}')
        xauth = os.environ.get('XAUTHORITY') or os.path.join(pw.pw_dir, '.Xauthority')
        if os.path.exists(xauth):
            env_args.append(f'XAUTHORITY={xauth}')
        return wrapper + ['env'] + env_args

    def _browser_commands(self, uri):
        candidates = [
            ['xdg-open', uri], ['gio', 'open', uri], ['x-www-browser', uri],
            ['sensible-browser', uri], ['firefox', uri], ['firefox-esr', uri],
            ['chromium', uri], ['google-chrome', uri],
        ]
        prefix = self._login_user_prefix()
        return [prefix + c for c in candidates if shutil.which(c[0])]

    def _open_uri(self, uri):
        """Open a web/mail link in the user's browser without blocking the UI."""
        uri = uri.strip()
        if uri.split(":", 1)[0].lower() not in ("http", "https", "mailto"):
            return                                # never launch file:, javascript:, etc.

        commands = self._browser_commands(uri)
        if not commands:                          # Windows / macOS / minimal Linux
            self._on_uri_failed(uri)
            return

        env = self._get_clean_env()

        def worker():
            for cmd in commands:
                try:
                    proc = subprocess.Popen(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        env=env, start_new_session=True
                    )
                except OSError:
                    continue
                try:
                    if proc.wait(timeout=3) == 0:
                        return
                except subprocess.TimeoutExpired:
                    return                        # still running: the browser took over
            self._uri_failed.emit(uri)

        threading.Thread(target=worker, daemon=True).start()

    def _on_uri_failed(self, uri):
        """Last resort: Qt's opener, then hand the link to the user."""
        if QDesktopServices.openUrl(QUrl(uri)):
            return
        QApplication.clipboard().setText(uri)
        QMessageBox.information(
            self, "Open Link",
            "Couldn't launch a web browser.\n\n"
            f"The link was copied to your clipboard:\n{uri}"
        )

    def _goto(self, page_index, y_pt):
        """Scroll so the destination (page + y offset in points) is at the top."""
        if not (0 <= page_index < len(self._page_widgets)):
            return
        widget = self._page_widgets[page_index]
        pw, ph = self._page_sizes[page_index]
        if not (0 <= y_pt <= ph):
            y_pt = 0.0
        target = widget.y() + int(y_pt * widget.width() / pw) - 16
        self.scroll.verticalScrollBar().setValue(max(0, target))

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def _scroll_style(self):
        t = self.theme.current
        return f"""
            QScrollArea {{
                border: none;
                background: {t['crust']};
            }}
            QScrollBar:vertical {{
                background: {t['crust']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {t['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t['text_tertiary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """

    def _to_dark(self, img, page, scale):
        """Recolor a rendered page for the dark theme.

        Inverts the page, then maps white -> theme base and black -> theme
        text color. Raster images (logos, screenshots) are re-drawn in their
        original colors on top so they don't look like photo negatives.
        """
        t = self.theme.current
        base, txt = QColor(t['base']), QColor(t['text'])
        lift = QColor(
            min(255, round(base.red() * 255 / max(1, txt.red()))),
            min(255, round(base.green() * 255 / max(1, txt.green()))),
            min(255, round(base.blue() * 255 / max(1, txt.blue()))),
        )

        img.invertPixels()
        p = QPainter(img)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        p.fillRect(img.rect(), lift)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
        p.fillRect(img.rect(), txt)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        try:
            infos = page.get_image_info()
        except Exception:
            infos = []
        page_area = page.rect.width * page.rect.height
        for info in infos:
            r = fitz.Rect(info["bbox"]) & page.rect
            if r.is_empty or r.width * r.height > 0.85 * page_area:
                continue                          # full-page scans: just invert
            x0, y0 = max(0, int(r.x0 * scale)), max(0, int(r.y0 * scale))
            x1 = min(img.width(), int(r.x1 * scale) + 1)
            y1 = min(img.height(), int(r.y1 * scale) + 1)
            clip = fitz.Rect(x0 / scale, y0 / scale, x1 / scale, y1 / scale)
            try:
                # alpha=True keeps transparent logos transparent
                cp = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                                     clip=clip, alpha=True)
                qi = QImage(cp.samples, cp.width, cp.height, cp.stride,
                            QImage.Format.Format_RGBA8888)
                p.drawImage(cp.x, cp.y, qi)
            except Exception:
                continue
        p.end()
        return img

    def _on_theme_changed(self, *_):
        """Restyle and, if light/dark flipped, re-render the cached pages."""
        t = self.theme.current
        self.scroll.setStyleSheet(self._scroll_style())
        for lbl in self._num_labels:
            lbl.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:10px;background:transparent;padding:2px;"
            )

        if self.theme.is_dark != self._render_dark:
            self._render_dark = self.theme.is_dark
            self._queue.clear()
            self._rendered.clear()
            for w in self._page_widgets:
                w.clear_pixmap()
            self._render_visible()
        else:
            for w in self._page_widgets:
                w.update()

    # ------------------------------------------------------------------
    # Layout changes
    # ------------------------------------------------------------------
    def _on_layout_settled(self):
        """After show / resize: adjust page sizes if needed, then render visible."""
        if not self._doc:
            return

        new_width = self._get_page_width()
        new_dpr = self.devicePixelRatioF()

        if abs(new_width - self._page_width) >= 20 or new_dpr != self._dpr:
            vbar = self.scroll.verticalScrollBar()
            ratio = vbar.value() / max(1, vbar.maximum())

            self._page_width = new_width
            self._dpr = new_dpr
            self._queue.clear()
            self._rendered.clear()
            for i, w in enumerate(self._page_widgets):
                w.clear_pixmap()
                w.setFixedSize(self._page_width, self._page_height_for(i))

            self.pages_layout.activate()
            vbar.setValue(round(ratio * vbar.maximum()))

        self._render_visible()

    def showEvent(self, event):
        super().showEvent(event)
        if self._doc:
            # Wait one tick so the layout has real geometry
            QTimer.singleShot(0, self._on_layout_settled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._doc:
            self._resize_timer.start()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 12, 20, 8)

        back_btn = QPushButton("  Back")
        back_icon_path = os.path.join(self._base_dir(), 'assets', 'icons', "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)

        title = QLabel("User Guide")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setObjectName("actionButton")
        open_btn.setMaximumWidth(80)
        open_btn.clicked.connect(self._open_externally)

        header.addWidget(back_btn)
        header.addStretch()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(open_btn)
        layout.addLayout(header)

        t = self.theme.current

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(self._scroll_style())

        self.pages_widget = QWidget()
        self.pages_widget.setStyleSheet("background: transparent;")
        self.pages_layout = QVBoxLayout(self.pages_widget)
        self.pages_layout.setSpacing(8)
        self.pages_layout.setContentsMargins(20, 16, 20, 30)
        self.pages_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.scroll.setWidget(self.pages_widget)
        layout.addWidget(self.scroll)

        self.scroll.verticalScrollBar().valueChanged.connect(
            lambda _v: self._scroll_timer.start()
        )

        if self._guide_path:
            if self._open_document():
                self._build_placeholders()
        else:
            info = QLabel("User guide not found")
            info.setStyleSheet(
                f"color:{t['error']};font-size:14px;font-weight:600;background:transparent;padding:10px;"
            )
            self.pages_layout.addWidget(info)

            hint = QLabel("Place guide.pdf in assets/docs/ directory")
            hint.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:12px;background:transparent;padding:10px;"
            )
            self.pages_layout.addWidget(hint)
            self.pages_layout.addStretch()

        self._apply_theme()

    def cleanup(self):
        """Optional: call when the page is destroyed to release the PDF handle."""
        if self._doc:
            self._doc.close()
            self._doc = None

    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"background-color:{t['base']};")

    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()
        self._on_theme_changed()