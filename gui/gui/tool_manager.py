# gui/tool_manager.py
import os
import json
import sys
import stat
from PySide6.QtCore import QObject, Signal


class ToolManager(QObject):
    tools_updated = Signal()

    # Scripts we can wrap by calling their interpreter directly, so they work
    # even without an exec bit or a usable shebang.
    _INTERPRETERS = {".pl": "perl", ".py": "python3", ".rb": "ruby"}

    def __init__(self):
        super().__init__()
        self.config_dir = os.path.join(os.path.expanduser("~"), ".sokonalysis")
        self.config_file = os.path.join(self.config_dir, "custom_tools.json")
        self.tools = {}  # name -> path
        self._load()

    def _load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.tools = json.load(f)
            except Exception:
                self.tools = {}
        self._apply_to_environment()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _write_config(self):
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.tools, f, indent=4)

    def save_tool(self, name, path):
        if not name or not path:
            return False, "Name and path are required."
        if not os.path.isfile(path):
            return False, f"File does not exist: {path}"
        self.tools[name] = path
        self._write_config()

        # Cross-platform visibility
        if sys.platform != "win32":
            self._create_linux_wrapper(name, path)
        self._apply_to_environment()
        self.tools_updated.emit()
        return True, "Tool saved successfully."

    def remove_tool(self, name):
        if name in self.tools:
            del self.tools[name]
            self._write_config()
            if sys.platform != "win32":
                wrapper = os.path.join(os.path.expanduser("~"), ".local", "bin", name)
                if os.path.exists(wrapper):
                    try:
                        os.remove(wrapper)
                    except Exception:
                        pass
            self._apply_to_environment()
            self.tools_updated.emit()
            return True
        return False

    # ------------------------------------------------------------------
    # Folder scan: import john + every *2john tool from one directory
    # (e.g. a jumbo build's run/ folder) in a single action.
    # ------------------------------------------------------------------
    def scan_folder(self, folder):
        """Find john / *2john tools in `folder` and register them.

        Returns (added, skipped, message).

        Handles the two things that break detection of a jumbo build:
          - the scripts carry .pl/.py extensions (pdf2john.pl, not pdf2john),
            so each is registered under its BARE base name and a bare-named
            wrapper is created, which is what the Requirements check looks up.
          - when the same base exists as a binary and a script
            (bitlocker2john + bitlocker2john.py), the fastest is preferred:
            no-extension binary > .pl > .py > anything else.
        """
        if not folder or not os.path.isdir(folder):
            return [], [], f"Not a folder: {folder}"

        ext_priority = {"": 0, ".pl": 1, ".py": 2, ".rb": 3}
        skip_ext = {".js", ".lua", ".md", ".txt", ".conf", ".cfg", ".chr", ".bak"}

        best = {}  # base_name -> (priority, full_path)
        try:
            entries = sorted(os.listdir(folder))
        except OSError as e:
            return [], [], f"Can't read folder: {e}"

        for fn in entries:
            full = os.path.join(folder, fn)
            if not os.path.isfile(full):
                continue
            base, ext = os.path.splitext(fn)
            ext = ext.lower()
            # keep the main binary 'john' and anything that is a *2john tool
            if not (base == "john" or "2john" in base):
                continue
            if ext in skip_ext:
                continue
            prio = ext_priority.get(ext, 9)
            if base not in best or prio < best[base][0]:
                best[base] = (prio, full)

        if not best:
            return [], [], "No John tools (john / *2john) found in that folder."

        added, skipped = [], []
        for base, (_prio, full) in sorted(best.items()):
            try:
                self.tools[base] = full
                if sys.platform != "win32":
                    self._create_linux_wrapper(base, full)
                added.append(base)
            except Exception as e:
                self.tools.pop(base, None)
                skipped.append(f"{base} ({e})")

        # One write + one signal for the whole batch.
        self._write_config()
        self._apply_to_environment()
        self.tools_updated.emit()

        return added, skipped, f"Added {len(added)} tool(s) from {folder}."

    # ------------------------------------------------------------------
    # Wrappers / PATH
    # ------------------------------------------------------------------
    def _create_linux_wrapper(self, name, target_path):
        """Create a bare-named wrapper in ~/.local/bin so the app finds the
        tool on PATH under `name` regardless of the target's extension.

        For known script types the interpreter is invoked explicitly
        (perl/python3/ruby), so a .pl/.py with no exec bit or a missing
        shebang still runs.
        """
        bin_dir = os.path.join(os.path.expanduser("~"), ".local", "bin")
        os.makedirs(bin_dir, exist_ok=True)
        wrapper_path = os.path.join(bin_dir, name)

        ext = os.path.splitext(target_path)[1].lower()
        interp = self._INTERPRETERS.get(ext)
        if interp:
            exec_line = f'exec {interp} "{target_path}" "$@"'
        else:
            exec_line = f'exec "{target_path}" "$@"'

        script = f"#!/bin/sh\n{exec_line}\n"
        with open(wrapper_path, "w") as f:
            f.write(script)
        st = os.stat(wrapper_path)
        os.chmod(wrapper_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _apply_to_environment(self):
        """On Windows, add tool directories to PATH. On Linux, ensure
        ~/.local/bin is in PATH so the wrappers are found."""
        if sys.platform == "win32":
            paths = [os.path.dirname(p) for p in self.tools.values()]
            current_path = os.environ.get("PATH", "")
            new_paths = [p for p in paths if p and p not in current_path]
            if new_paths:
                os.environ["PATH"] = os.pathsep.join(new_paths + [current_path])
        else:
            bin_dir = os.path.join(os.path.expanduser("~"), ".local", "bin")
            current_path = os.environ.get("PATH", "")
            if bin_dir not in current_path.split(os.pathsep):
                os.environ["PATH"] = f"{bin_dir}{os.pathsep}{current_path}"


# Global instance
tool_manager = ToolManager()