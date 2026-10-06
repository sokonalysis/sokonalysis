# gui/config_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QLineEdit, QFileDialog,
    QMessageBox, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QSize
import os
from multiprocessing import cpu_count
from PySide6.QtGui import QIcon, QPixmap
import sys
from gui.layout_manager import layout_manager


class ConfigPage(QWidget):
    """Shared configurations page for wordlist management."""
    
    wordlist_configured = Signal(str, int)
    
    def __init__(self, theme_manager, back_callback, wordlist_path="", split_parts=4):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.wordlist_path = wordlist_path
        self.split_parts = split_parts
        self.wordlist_word_count = 0
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if filepath and filepath.endswith('.txt'):
                self.wordlist_path = filepath
                self.wordlist_display.setText(filepath)
                self._update_wordlist_info_fast()
                self._update_recommendation()
                self._update_drop_preview()
                self._update_badge()
                break
    
    def _init_ui(self):
        scale = layout_manager.font_scale()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(max(14, int(16 * scale)), max(14, int(16 * scale))))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(max(80, int(100 * scale)))
        
        title = QLabel("Configurations")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        # Wordlist status badge
        wl_container = QHBoxLayout()
        wl_container.setSpacing(4)
        self.wl_icon = QLabel()
        self.wl_icon.setFixedSize(
            max(16, int(18 * scale)),
            max(16, int(18 * scale))
        )
        self.wl_icon.setStyleSheet("background:transparent;")
        self.wl_badge = QLabel()
        self._update_badge()
        wl_container.addWidget(self.wl_icon)
        wl_container.addWidget(self.wl_badge)
        header.addLayout(wl_container)
        
        layout.addLayout(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        
        # Description
        desc = QLabel("Configure wordlist settings for all hashing and cracking operations.")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        content_layout.addWidget(desc)
        
        # Drop zone for wordlist
        self.drop_group = QGroupBox("Wordlist File")
        drop_layout = QVBoxLayout()
        
        self.drop_preview = QLabel()
        self.drop_preview.setFixedHeight(max(90, int(120 * scale)))
        self.drop_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_preview.setText("Drag & drop a .txt wordlist file here\nor click Browse to select")
        drop_layout.addWidget(self.drop_preview)
        
        self.wordlist_info = QLabel("")
        drop_layout.addWidget(self.wordlist_info)
        
        upload_row = QHBoxLayout()
        self.wordlist_display = QLineEdit()
        self.wordlist_display.setReadOnly(True)
        self.wordlist_display.setPlaceholderText("No wordlist selected...")
        if self.wordlist_path:
            self.wordlist_display.setText(self.wordlist_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("actionButton")
        browse_btn.setMinimumHeight(max(36, int(42 * scale)))
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_wordlist)
        
        upload_row.addWidget(self.wordlist_display, 1)
        upload_row.addWidget(browse_btn)
        drop_layout.addLayout(upload_row)
        
        self.drop_group.setLayout(drop_layout)
        content_layout.addWidget(self.drop_group)
        
        # Splitting options
        self.split_group = QGroupBox("Wordlist Splitting")
        split_layout = QFormLayout()
        split_layout.setSpacing(max(8, int(10 * scale)))
        
        self.split_label = QLabel("Number of parts:")
        self.split_label.setObjectName("formLabel")
        
        self.auto_detect_cb = QCheckBox("Auto-detect optimal split count")
        self.auto_detect_cb.setChecked(True)
        self.auto_detect_cb.toggled.connect(self._on_auto_detect_toggled)
        split_layout.addRow("", self.auto_detect_cb)
        
        self.split_spin = QSpinBox()
        self.split_spin.setRange(1, 32)
        self.split_spin.setValue(self.split_parts)
        self.split_spin.setEnabled(False)
        split_layout.addRow(self.split_label, self.split_spin)
        
        self.recommendation_label = QLabel("")
        split_layout.addRow("", self.recommendation_label)
        
        self.split_group.setLayout(split_layout)
        content_layout.addWidget(self.split_group)
        
        # Save button
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setObjectName("actionButton")
        self.save_btn.setMinimumHeight(max(40, int(44 * scale)))
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_configuration)
        content_layout.addWidget(self.save_btn)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self._apply_theme()
        
        if self.wordlist_path:
            self._update_recommendation()
            self._update_drop_preview()
    
    def _update_drop_preview(self):
        """Update drop zone preview with file info - using theme colors."""
        t = self.theme.current
        scale = layout_manager.font_scale()
        if self.wordlist_path and os.path.exists(self.wordlist_path):
            fn = os.path.basename(self.wordlist_path)
            sz = os.path.getsize(self.wordlist_path)
            ss = (
                f"{sz} B" if sz < 1024
                else f"{sz/1024:.1f} KB" if sz < 1048576
                else f"{sz/1048576:.1f} MB"
            )
            self.drop_preview.setText(f"{fn}\n{ss}")
            self.drop_preview.setStyleSheet(
                f"border: 2px dashed {t['border']};border-radius: 8px;"
                f"background: transparent;color: {t['text']};"
                f"font-size: {max(12, int(14 * scale))}px;font-weight: 600;padding: 10px;"
            )
        else:
            self.drop_preview.setText("Drag & drop a .txt wordlist file here\nor click Browse to select")
            self.drop_preview.setStyleSheet(
                f"border: 2px dashed {t['border']};border-radius: 8px;"
                f"background: transparent;color: {t['text_tertiary']};"
                f"font-size: {max(11, int(13 * scale))}px;padding: 10px;"
            )
    
    def _update_badge(self):
        """Update wordlist status badge."""
        t = self.theme.current
        scale = layout_manager.font_scale()
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        if self.wordlist_path and os.path.exists(self.wordlist_path):
            self.wl_badge.setText("Wordlist Ready")
            c = t['success']
            icon_path = os.path.join(icons_dir, "wordlist.png")
        else:
            self.wl_badge.setText("No Wordlist")
            c = t['warning']
            icon_path = os.path.join(icons_dir, "no.png")
        
        self.wl_badge.setStyleSheet(
            f"padding:{max(3, int(4 * scale))}px {max(8, int(12 * scale))}px;"
            f"border-radius:{max(10, int(12 * scale))}px;"
            f"font-size:{max(10, int(11 * scale))}px;"
            f"font-weight:600;background:{c}22;color:{c};"
        )
        if os.path.exists(icon_path) and hasattr(self, 'wl_icon'):
            icon_px = max(14, int(16 * scale))
            self.wl_icon.setPixmap(QIcon(icon_path).pixmap(icon_px, icon_px))
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        group_style = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:{int(20 * scale)}px {int(16 * scale)}px {int(16 * scale)}px;"
            f"font-weight:600;font-size:{max(12, int(13 * scale))}px;}} "
            f"QGroupBox::title{{subcontrol-origin:margin;left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'drop_group') and self.drop_group is not None:
            self.drop_group.setStyleSheet(group_style)
        if hasattr(self, 'split_group') and self.split_group is not None:
            self.split_group.setStyleSheet(group_style)
        
        # Description + form labels
        for label in self.findChildren(QLabel):
            try:
                if label.objectName() == "pageSubtitle":
                    label.setStyleSheet(
                        f"color:{t['text_secondary']};"
                        f"font-size:{max(12, int(14 * scale))}px;background:transparent;"
                    )
                elif label.objectName() == "pageTitle":
                    label.setStyleSheet(
                        f"font-size:{max(20, int(26 * scale))}px;"
                        f"font-weight:700;color:{t['text']};background:transparent;"
                    )
                elif label.objectName() == "formLabel":
                    label.setStyleSheet(
                        f"color:{t['text']};"
                        f"font-size:{max(12, int(13 * scale))}px;background:transparent;"
                    )
            except RuntimeError:
                pass
        
        if hasattr(self, 'wordlist_info') and self.wordlist_info is not None:
            self.wordlist_info.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{max(11, int(12 * scale))}px;background:transparent;"
            )
        if hasattr(self, 'recommendation_label') and self.recommendation_label is not None:
            self.recommendation_label.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{max(11, int(12 * scale))}px;background:transparent;"
            )
        
        if hasattr(self, 'wordlist_display') and self.wordlist_display is not None:
            self.wordlist_display.setStyleSheet(
                f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;"
                f"padding:{int(8 * scale)}px {int(12 * scale)}px;"
                f"font-size:{max(12, int(13 * scale))}px;}}"
            )
        
        if hasattr(self, 'split_spin') and self.split_spin is not None:
            self.split_spin.setStyleSheet(
                f"QSpinBox{{background-color:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;"
                f"padding:{int(8 * scale)}px {int(12 * scale)}px;"
                f"font-size:{max(12, int(14 * scale))}px;}} "
                f"QSpinBox:focus{{border-color:{t['accent']};}} "
                f"QSpinBox::up-button, QSpinBox::down-button{{background-color:{t['surface0']};"
                f"border:none;border-radius:3px;width:{max(16, int(20 * scale))}px;}} "
                f"QSpinBox::up-button:hover, QSpinBox::down-button:hover{{background-color:{t['hover']};}} "
                f"QSpinBox:disabled{{background-color:{t['surface0']};color:{t['text_tertiary']};}}"
            )
        
        if hasattr(self, 'auto_detect_cb') and self.auto_detect_cb is not None:
            ind = max(16, int(18 * scale))
            self.auto_detect_cb.setStyleSheet(
                f"QCheckBox{{color:{t['text']};font-size:{max(12, int(13 * scale))}px;spacing:8px;}} "
                f"QCheckBox::indicator{{width:{ind}px;height:{ind}px;"
                f"border:2px solid {t['border']};border-radius:4px;background-color:{t['crust']};}} "
                f"QCheckBox::indicator:checked{{background-color:{t['accent']};border-color:{t['accent']};}}"
            )
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{int(10 * scale)}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(12, int(15 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "backButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:transparent;color:{t['text_secondary']};"
                        f"border:none;font-size:{max(12, int(13 * scale))}px;font-weight:500;"
                        f"padding:6px 0px;}} "
                        f"QPushButton:hover{{color:{t['text']};}}"
                    )
            except RuntimeError:
                pass
        
        self._update_drop_preview()
        self._update_badge()
    
    def _browse_wordlist(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.wordlist_path = file_path
            self.wordlist_display.setText(file_path)
            self._update_wordlist_info_fast()
            self._update_recommendation()
            self._update_drop_preview()
            self._update_badge()
    
    def _update_wordlist_info_fast(self):
        try:
            size = os.path.getsize(self.wordlist_path)
            self.wordlist_word_count = size // 8
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/(1024*1024):.1f}MB"
            self.wordlist_info.setText(f"~{self.wordlist_word_count:,} words • {size_str}")
        except Exception:
            self.wordlist_info.setText("Could not read wordlist")
            self.wordlist_word_count = 0
    
    def _calculate_optimal_parts(self):
        if self.wordlist_word_count == 0:
            return 4
        cpu_cores = cpu_count()
        if self.wordlist_word_count < 100000:
            return min(2, cpu_cores)
        elif self.wordlist_word_count < 1000000:
            return min(4, cpu_cores)
        elif self.wordlist_word_count < 10000000:
            return min(8, cpu_cores)
        else:
            return min(16, cpu_cores)
    
    def _update_recommendation(self):
        optimal = self._calculate_optimal_parts()
        cpu_cores = cpu_count()
        self.recommendation_label.setText(
            f"Recommended: {optimal} parts "
            f"(based on ~{self.wordlist_word_count:,} words, {cpu_cores} CPU cores)"
        )
        if self.auto_detect_cb.isChecked():
            self.split_spin.setValue(optimal)
            self.split_parts = optimal
    
    def _on_auto_detect_toggled(self, checked):
        self.split_spin.setEnabled(not checked)
        if checked:
            self._update_recommendation()
    
    def _save_configuration(self):
        if not self.wordlist_path:
            QMessageBox.warning(self, "No Wordlist", "Please select a wordlist first.")
            return
        if not os.path.exists(self.wordlist_path):
            QMessageBox.warning(self, "File Not Found", "Selected wordlist does not exist.")
            return
        self.split_parts = self.split_spin.value()
        self.wordlist_configured.emit(self.wordlist_path, self.split_parts)
        self._update_badge()
        
        scale = layout_manager.font_scale()
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        yes_icon_path = os.path.join(icons_dir, "yes.png")
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Configuration Saved")
        msg.setIcon(QMessageBox.Icon.Information)
        if os.path.exists(yes_icon_path):
            icon_size = max(36, int(48 * scale))
            msg.setIconPixmap(
                QPixmap(yes_icon_path).scaled(
                    icon_size, icon_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        msg.setText("Wordlist configuration saved!")
        msg.setInformativeText(
            f"File: {os.path.basename(self.wordlist_path)}\nSplit parts: {self.split_parts}"
        )
        msg.exec()
        
        self.back_callback()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()