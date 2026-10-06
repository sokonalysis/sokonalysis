# gui/algorithms/__init__.py
"""
Pure-Python algorithm implementations.

No Qt, no signals, no main_window. Callable from:
  - gui/ai_assistant.py       (chat-driven cracking)
  - gui/crack_*_page.py       (UI-driven cracking, if/when refactored)
  - tests, CLI, anywhere

Each module exposes plain functions with a consistent signature:
    progress_cb:     callable(str) -> None, optional
    cancelled_check: callable() -> bool, optional (return True to abort)
"""