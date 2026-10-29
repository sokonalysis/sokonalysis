# gui/tools_config_page.py
import os
import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QLineEdit, QFileDialog, QFrame, QDialog, QFormLayout
)

from gui.layout_manager import layout_manager
from gui.tool_manager import tool_manager
from gui.card_grid import CardGrid


ADD_TOOL_SENTINEL = "__ADD_NEW_TOOL__"


def _icons_dir():
    base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base, "assets", "icons")


def _fallback_x_icon(color):
    """Painted X, used only if assets/icons/no.png is missing."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(9, 9, 23, 23)
    p.drawLine(23, 9, 9, 23)
    p.end()
    return QIcon(pm)


# ----------------------------------------------------------------------
# Card grid: the normal option cards, plus a delete icon and a "+" card
# ----------------------------------------------------------------------
class ToolCardGrid(CardGrid):
    """CardGrid that adds no.png to each tool card and draws the add card as '+'.

    CardGrid rebuilds its cards on every resize/layout change, so the
    decorations are applied inside the build itself - never once from outside,
    where they would be lost on the next rebuild.
    """

    DELETE_SIZE = 24
    DELETE_MARGIN = 12

    def __init__(self, on_delete, parent=None):
        super().__init__(parent)
        self._on_delete = on_delete
        self._no_icon_path = os.path.join(_icons_dir(), "no.png")

    # Build the "+" card through the same code path as every other card,
    # so it keeps the exact same size, border, shadow and hover.
    def _create_card(self, name, description, theme, card_w, card_h,
                     title_font, desc_font, spacing, margins=None):
        if name != ADD_TOOL_SENTINEL:
            card = super()._create_card(name, description, theme, card_w, card_h,
                                        title_font, desc_font, spacing, margins)
            self._add_delete_button(card, name, card_w, theme)
            return card

        card = super()._create_card("", "", theme, card_w, card_h,
                                    title_font, desc_font, spacing, margins)
        # Own object name, so CardGrid's "QFrame#landingCard" rule (solid
        # border) never applies to it and the dotted border below wins.
        card.setObjectName("addCard")
        self._style_add_card(card, theme)
        for lbl in card.findChildren(QLabel):
            lbl.hide()

        plus = QLabel("+")
        plus.setObjectName("addPlus")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._style_plus(plus, theme)
        lay = card.layout()
        lay.addWidget(plus, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addStretch()
        return card

    def _add_delete_button(self, card, name, card_w, theme):
        # No tooltip: CardGrid paints everything "background: transparent",
        # which the tooltip inherits, and a transparent tooltip window shows
        # up as a solid black box.
        btn = QToolButton(card)
        btn.setObjectName("deleteButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(self.DELETE_SIZE, self.DELETE_SIZE)
        btn.setIconSize(QSize(18, 18))
        btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        self._set_delete_icon(btn, theme)
        btn.move(card_w - self.DELETE_SIZE - self.DELETE_MARGIN, self.DELETE_MARGIN)
        btn.clicked.connect(lambda checked=False, n=name: self._on_delete(n))
        btn.raise_()
        btn.hide()  # only shown while the cursor is on this card

        # Wrap CardGrid's own hover handlers (shadow lift) so they still run.
        grid_enter, grid_leave = card.enterEvent, card.leaveEvent

        def _enter(event, b=btn, orig=grid_enter):
            b.show()
            orig(event)

        def _leave(event, b=btn, orig=grid_leave):
            b.hide()
            orig(event)

        card.enterEvent = _enter
        card.leaveEvent = _leave

    def _style_add_card(self, card, theme):
        t = theme.current
        card.setStyleSheet(f"""
            QFrame#addCard {{
                background-color: {t['base']};
                border: 2px dotted {t['text_tertiary']};
                border-radius: 14px;
            }}
            QFrame#addCard:hover {{
                background-color: {t['hover']};
            }}
        """)

    def _set_delete_icon(self, btn, theme):
        if os.path.exists(self._no_icon_path):
            btn.setIcon(QIcon(self._no_icon_path))
        else:
            btn.setIcon(_fallback_x_icon(theme.current["error"]))

    def _style_plus(self, lbl, theme):
        t = theme.current
        size = max(36, int(48 * layout_manager.font_scale()))
        lbl.setStyleSheet(
            f"color: {t['text_tertiary']}; font-size: {size}px; "
            f"font-weight: 300; background: transparent;"
        )

    def refresh_theme(self, theme):
        super().refresh_theme(theme)
        for card in self._cards:
            # CardGrid.refresh_theme overwrites every card's stylesheet,
            # so put the dotted border back on the add card.
            if card.objectName() == "addCard":
                self._style_add_card(card, theme)
            for lbl in card.findChildren(QLabel, "addPlus"):
                self._style_plus(lbl, theme)
            for btn in card.findChildren(QToolButton, "deleteButton"):
                self._set_delete_icon(btn, theme)


# ----------------------------------------------------------------------
# Dialogs (plain buttons, no stock icons)
# ----------------------------------------------------------------------
def _dialog_qss(t):
    fs = max(12, int(13 * layout_manager.font_scale()))
    return f"""
    QDialog {{ background-color: {t['base']}; }}
    QLabel {{ color: {t['text']}; background: transparent; font-size: {fs}px; }}
    QLabel#errorLabel {{ color: {t['error']}; }}
    QLineEdit {{
        background-color: {t['crust']}; color: {t['text']};
        border: 1px solid {t['border']}; border-radius: 6px;
        padding: 8px 10px; font-size: {fs}px;
    }}
    QPushButton {{
        background-color: {t['crust']}; color: {t['text']};
        border: 1px solid {t['border']}; border-radius: 6px;
        padding: 7px 18px; font-size: {fs}px;
    }}
    QPushButton:hover {{ background-color: {t['surface0']}; }}
    QPushButton#dangerButton {{ color: {t['error']}; }}
    """


class ToolEditDialog(QDialog):
    def __init__(self, name, path, theme_manager, existing_names=(), parent=None):
        super().__init__(parent)
        self._original = name
        self._existing = set(existing_names)
        self.setWindowTitle("Edit Tool" if name else "Add Tool")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Tool name (e.g. john, zip2john)")
        form.addRow("Name:", self.name_input)

        path_row = QHBoxLayout()
        self.path_input = QLineEdit(path)
        self.path_input.setPlaceholderText("Path to executable (e.g. /usr/sbin/john)")
        browse = QPushButton("Browse")
        browse.setAutoDefault(False)
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.clicked.connect(self._browse)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(browse)
        form.addRow("Path:", path_row)
        layout.addLayout(form)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("errorLabel")
        self.error_lbl.hide()
        layout.addWidget(self.error_lbl)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setAutoDefault(False)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setDefault(True)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

        self.setStyleSheet(_dialog_qss(theme_manager.current))

    def _browse(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Executable")
        if fp:
            self.path_input.setText(fp)
            if not self.name_input.text().strip():
                self.name_input.setText(os.path.basename(fp))

    def _fail(self, msg):
        self.error_lbl.setText(msg)
        self.error_lbl.show()

    def _on_save(self):
        name, path = self.get_data()
        if not name:
            return self._fail("Enter a name for the tool.")
        if not path:
            return self._fail("Enter or browse to the tool's executable.")
        if os.path.isdir(path):
            return self._fail("That's a folder. Point to the program file itself, "
                              "or use Scan Folder to import a whole directory.")
        if not os.path.isfile(path):
            return self._fail(f"No file at: {path}")
        if name != self._original and name in self._existing:
            return self._fail(f"A tool named '{name}' already exists.")
        self.accept()

    def get_data(self):
        return self.name_input.text().strip(), self.path_input.text().strip()


class ConfirmRemoveDialog(QDialog):
    def __init__(self, name, theme_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Remove Tool")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        msg = QLabel(f"Remove '{name}' from Sokonalysis?")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setDefault(True)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        remove = QPushButton("Remove")
        remove.setObjectName("dangerButton")
        remove.setAutoDefault(False)
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(remove)
        layout.addLayout(row)

        self.setStyleSheet(_dialog_qss(theme_manager.current))


class InfoDialog(QDialog):
    """Simple themed message box (scan summary, save errors)."""

    def __init__(self, title, message, theme_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        msg = QLabel(message)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        row = QHBoxLayout()
        row.addStretch()
        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        layout.addLayout(row)

        self.setStyleSheet(_dialog_qss(theme_manager.current))


# ----------------------------------------------------------------------
# Page (same structure as CTFRSAPage)
# ----------------------------------------------------------------------
class ToolsConfigPage(QWidget):
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.card_grid = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setSpacing(20)

        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        back_icon_path = os.path.join(_icons_dir(), "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        header.addWidget(back_btn)
        header.addStretch()

        self.scan_btn = QPushButton("Scan Folder")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.setToolTip("Import john and every *2john tool from a folder")
        self.scan_btn.clicked.connect(self._scan_folder)
        self._style_scan_btn()
        header.addWidget(self.scan_btn)

        title = QLabel("Third-Party Tools")
        title.setObjectName("pageTitle")

        desc = QLabel("Configure custom tools. Click a card to edit its path. "
                      "Sokonalysis will automatically detect them.")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)

        separator = QFrame()
        separator.setObjectName("separator")

        self.card_grid = ToolCardGrid(on_delete=self._remove_tool)
        self._load_cards()

        layout.addLayout(header)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(self.card_grid)

    def _card_data(self):
        data = [(name, path) for name, path in tool_manager.tools.items()]
        data.append((ADD_TOOL_SENTINEL, ""))
        return data

    def _load_cards(self):
        # add_cards() clears and rebuilds the grid in place.
        self.card_grid.add_cards(self._card_data(), self.theme, self._on_card_clicked)

    def _on_card_clicked(self, name):
        self._edit_tool(None if name == ADD_TOOL_SENTINEL else name)

    def _edit_tool(self, name):
        current_path = tool_manager.tools.get(name, "") if name else ""
        dlg = ToolEditDialog(name or "", current_path, self.theme,
                             existing_names=tool_manager.tools.keys(), parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_name, new_path = dlg.get_data()
        if name and new_name != name:      # renamed: drop the old entry
            tool_manager.remove_tool(name)
        result = tool_manager.save_tool(new_name, new_path)
        # save_tool returns (ok, message); surface the reason on failure
        # instead of silently doing nothing.
        ok, msg = result if isinstance(result, tuple) else (bool(result), "")
        if not ok:
            InfoDialog("Couldn't add tool", msg or "Unknown error.", self.theme, self).exec()
        self._load_cards()

    def _scan_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select John the Ripper 'run' folder (e.g. /root/john/run)")
        if not folder:
            return
        added, skipped, msg = tool_manager.scan_folder(folder)
        lines = [msg]
        if added:
            lines.append("Added: " + ", ".join(added))
        if skipped:
            lines.append("Skipped: " + ", ".join(skipped))
        InfoDialog("Scan Folder", "\n".join(lines), self.theme, self).exec()
        self._load_cards()

    def _remove_tool(self, name):
        if ConfirmRemoveDialog(name, self.theme, self).exec() == QDialog.DialogCode.Accepted:
            tool_manager.remove_tool(name)
            self._load_cards()

    def _style_scan_btn(self):
        t = self.theme.current
        fs = max(12, int(13 * layout_manager.font_scale()))
        self.scan_btn.setStyleSheet(f"""
            QPushButton#scanButton {{
                background-color: {t['crust']}; color: {t['text']};
                border: 1px solid {t['border']}; border-radius: 8px;
                padding: 7px 16px; font-size: {fs}px; font-weight: 500;
            }}
            QPushButton#scanButton:hover {{ background-color: {t['surface0']}; }}
        """)

    def refresh_theme(self):
        self._style_scan_btn()
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)