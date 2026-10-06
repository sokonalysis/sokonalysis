# gui/thinking_indicator.py
"""
A small animated "thinking" indicator, similar to the animated status text
Claude shows while composing a response. Drop this into whatever widget
hosts your AI assistant chat, next to where you create AIAssistantWorker.

USAGE
-----
    from gui.thinking_indicator import ThinkingIndicator

    # once, when building your chat panel:
    self.thinking = ThinkingIndicator(self.theme)
    layout.addWidget(self.thinking)
    self.thinking.hide()

    # when the user asks something:
    def _ask_ai(self, question, dropped_file=None):
        self.thinking.start("Thinking")
        self.worker = AIAssistantWorker(question, dropped_file, main_window=self.main_window)

        # progress_update already emits messages like "Cracking ZIP file...",
        # "Using wordlist: rockyou.txt", "Brute forcing..." - feed those
        # straight into the indicator so it reads like Claude's live status:
        self.worker.progress_update.connect(self.thinking.set_status)

        self.worker.response_ready.connect(self._on_ai_response)
        self.worker.action_requested.connect(self._on_ai_action)
        self.worker.start()

    def _on_ai_response(self, response):
        self.thinking.stop()
        self._append_message(response)   # your existing chat-append logic

Nothing here talks to the worker thread directly except via signals, so it's
safe to use from the GUI thread as-is.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, Qt


class ThinkingIndicator(QLabel):
    """Animated 'Thinking...' label with cycling dots, theme-aware color."""

    def __init__(self, theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._base_text = "Thinking"
        self._dot_count = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._apply_style()

    def _apply_style(self):
        color = "#888888"
        if self.theme is not None:
            try:
                color = self.theme.current.get('text_secondary', color)
            except Exception:
                pass
        self.setStyleSheet(
            f"color:{color};font-size:12px;font-style:italic;background:transparent;"
        )

    def start(self, base_text="Thinking"):
        """Begin the animation with an optional starting status message."""
        self._base_text = base_text
        self._dot_count = 0
        self._apply_style()
        self.setText(self._base_text)
        self.show()
        self._timer.start(400)

    def set_status(self, text):
        """
        Update the status text shown mid-animation. Wire this directly to
        AIAssistantWorker.progress_update so the indicator narrates what's
        actually happening ("Cracking ZIP file...", "Using wordlist...",
        "Brute forcing...") instead of just sitting on generic dots.
        """
        self._base_text = text
        self.setText(self._base_text + "." * self._dot_count)

    def stop(self):
        """Stop and hide the indicator."""
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._dot_count = (self._dot_count + 1) % 4
        self.setText(self._base_text + "." * self._dot_count)

    def refresh_theme(self):
        """Call from your page's refresh_theme() so colors stay in sync."""
        self._apply_style()