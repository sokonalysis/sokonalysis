# gui/ctf_rsa_factordb.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar,
    QApplication, QMessageBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon
import os
import sys
import json
import urllib.request
import urllib.error
from gui.layout_manager import layout_manager


class FactorDBWorker(QThread):
    """Worker for FactorDB API queries."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, dict)
    
    def __init__(self, modulus):
        super().__init__()
        self.modulus = modulus
    
    def run(self):
        try:
            self.progress.emit(f"[*] Querying FactorDB for modulus: {self.modulus}")
            self.progress_value.emit(10)
            
            url = f"http://factordb.com/api?query={self.modulus}"
            self.progress.emit("[*] Connecting to FactorDB API...")
            self.progress_value.emit(30)
            
            req = urllib.request.Request(url, headers={'User-Agent': 'sokonalysis/3.5'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
            
            self.progress_value.emit(60)
            self.progress.emit("[*] Parsing response...")
            
            result = json.loads(data)
            status = result.get('status', 'unknown')
            factors = result.get('factors', [])
            
            self.progress.emit(f"[*] Status: {status}")
            self.progress_value.emit(80)
            
            factor_list = []
            for i, factor in enumerate(factors):
                factor_id = factor[0]
                exponent = factor[1]
                resolved = self._resolve_factor(factor_id)
                factor_list.append({
                    'id': factor_id,
                    'exponent': exponent,
                    'resolved': resolved
                })
            
            self.progress_value.emit(100)
            self.progress.emit(f"[✓] Found {len(factor_list)} factors")
            
            self.finished.emit(True, {
                'modulus': self.modulus,
                'status': status,
                'factors': factor_list
            })
            
        except urllib.error.URLError as e:
            self.progress_value.emit(100)
            self.progress.emit(f"[!] Connection error: {str(e)}")
            self.finished.emit(False, {'error': f'Connection failed: {str(e)}'})
        except json.JSONDecodeError:
            self.progress_value.emit(100)
            self.progress.emit("[!] Failed to parse API response")
            self.finished.emit(False, {'error': 'Invalid API response'})
        except Exception as e:
            self.progress_value.emit(100)
            self.progress.emit(f"[!] Error: {str(e)}")
            self.finished.emit(False, {'error': str(e)})
    
    def _resolve_factor(self, factor_id):
        """Resolve factor ID to actual number if needed."""
        if factor_id.isdigit():
            return factor_id
        
        try:
            url = f"http://factordb.com/api?query={factor_id}"
            req = urllib.request.Request(url, headers={'User-Agent': 'sokonalysis/3.5'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                return result.get('number', factor_id)
        except:
            return factor_id


class CTF_RSA_FactorDBPage(QWidget):
    """CTF > RSA > FactorDB - Query FactorDB for RSA modulus factorization."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.result_data = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("CTF - RSA - FactorDB")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.setMinimumHeight(400)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'in_grp') and self.in_grp is not None:
            try:
                self.in_grp.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        input_style = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        if hasattr(self, 'modulus_input') and self.modulus_input is not None:
            try:
                self.modulus_input.setStyleSheet(input_style)
                self.modulus_input.setMinimumHeight(max(34, int(38 * scale)))
            except RuntimeError:
                pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        # Scale the primary "Query FactorDB" button
        if hasattr(self, 'run_btn') and self.run_btn is not None:
            self.run_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(ts)
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(
                    f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
                )
                self.status_progress.setMinimumHeight(max(22, int(28 * scale)))
            except RuntimeError:
                pass
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.in_grp = QGroupBox("Modulus")
        il = QVBoxLayout()
        il.setSpacing(10)
        
        il.addWidget(QLabel("Modulus (n):"))
        
        # Row: [input] [Paste] [Clear]
        row = QHBoxLayout()
        row.setSpacing(8)
        
        self.modulus_input = QLineEdit()
        self.modulus_input.setPlaceholderText("Enter RSA modulus (n)...")
        self.modulus_input.setMinimumHeight(38)
        self.modulus_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        row.addWidget(self.modulus_input, 1)
        
        paste_n = QPushButton("Paste")
        paste_n.setObjectName("actionButton")
        paste_n.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_n.clicked.connect(lambda: self._paste_to(self.modulus_input))
        paste_n.setMaximumWidth(90)
        row.addWidget(paste_n)
        
        clear_n = QPushButton("Clear")
        clear_n.setObjectName("dangerButton")
        clear_n.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_n.clicked.connect(self._clear_all)
        clear_n.setMaximumWidth(90)
        row.addWidget(clear_n)
        
        il.addLayout(row)
        
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.run_btn = QPushButton("Query FactorDB")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run_query)
        br.addWidget(self.run_btn)
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        if isinstance(widget, QTextEdit):
            widget.setPlainText(clipboard)
        else:
            widget.setText(clipboard.strip())
    
    def _clear_all(self):
        """Clear modulus input and previous results."""
        self.modulus_input.clear()
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.result_data = None
    
    def _run_query(self):
        modulus = self.modulus_input.text().strip()
        if not modulus:
            QMessageBox.warning(self, "No Input", "Please enter a modulus (n) to factorize.")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_progress.setValue(0)
        self.status_output.clear()
        self.results_output.clear()
        
        # Immediate feedback so Status tab isn't frozen-looking
        self.status_output.append("[*] Initializing FactorDB query...")
        self.status_output.append(f"[*] Modulus: {modulus[:60]}{'...' if len(modulus) > 60 else ''}")
        self.status_output.append("[*] Starting worker...")
        
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
        
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Querying...")
        
        self.worker = FactorDBWorker(modulus)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, message):
        self.status_output.append(message)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, data):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Query FactorDB")
        if success:
            self.result_data = data
            self.status_progress.setValue(100)
            self._show_results()
            self.tabs.setCurrentIndex(2)
        else:
            self.status_progress.setValue(100)
            self.status_output.append(f"[!] Query failed: {data.get('error', 'Unknown error')}")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
    
    def _show_results(self):
        if not self.result_data:
            return
        
        result = self.result_data
        
        # Build plain text result with proper formatting
        lines = []
        lines.append(f"Status: {result['status']}")
        lines.append(f"Modulus: {result['modulus']}")
        lines.append("")
        lines.append("Factors:")
        
        for i, factor in enumerate(result['factors']):
            label = 'p' if i == 0 else 'q' if i == 1 else f'r{i-1}'
            lines.append(f"{label} = {factor['resolved']}")
        
        self.results_output.setPlainText("\n".join(lines))
    
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        self.status_output.setMinimumHeight(200)
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Result:")
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        l.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Factors will appear here...")
        self.results_output.setMinimumHeight(200)
        self.results_output.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        l.addWidget(self.results_output, 1)
        
        return w
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy yet.")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()