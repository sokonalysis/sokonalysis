# gui/ctf_navy_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QScrollArea, QGridLayout, QSizePolicy,
    QApplication, QFrame
)
from PySide6.QtCore import Qt, QSize, QMimeData
from PySide6.QtGui import QIcon, QPixmap, QColor, QFont, QDrag, QPainter
import os, sys


NAVY_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
NATO_ALT = {'0':'0.1','1':'1.1','2':'2.2','3':'3.3','4':'4.4','5':'5.5','6':'6.6','7':'7.7','8':'8.8','9':'9.9'}


class DraggableStyleCard(QFrame):
    def __init__(self, style_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.style_id = style_id; self.style_name = name; self.colors = theme_colors
        self.name_label = None
        self.setFixedSize(200, 60); self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build()
    
    def _build(self):
        t = self.colors
        if self.name_label is None:
            l = QVBoxLayout(self); l.setContentsMargins(14,10,14,10); l.setSpacing(2)
            self.name_label = QLabel(self.style_name); self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.name_label.setWordWrap(True)
            l.addWidget(self.name_label)
        self.name_label.setStyleSheet(f"color:{t['text']};font-size:12px;font-weight:600;background:transparent;")
        self.setStyleSheet(f"QFrame{{background:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background:{t['surface0']};}}")
    
    def update_theme(self, tc): self.colors = tc; self._build()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(e)
    def mouseReleaseEvent(self, e): self.setCursor(Qt.CursorShape.OpenHandCursor); super().mouseReleaseEvent(e)
    
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self); mime = QMimeData(); mime.setText(f"{self.style_id}:{self.style_name}")
            drag.setMimeData(mime); pixmap = QPixmap(self.size()); self.render(pixmap)
            drag.setPixmap(pixmap); drag.setHotSpot(e.pos()); drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class StyleDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors; self.style_id = None; self.style_name = None
        self.setFixedSize(260, 80); self.setAcceptDrops(True); self._style_empty()
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}")
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}")
    def is_filled(self): return self.style_id is not None
    def clear_slot(self): self.style_id = None; self.style_name = None; self._style_empty(); self.update()
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText(): e.acceptProposedAction()
    
    def dropEvent(self, e):
        data = e.mimeData().text()
        try:
            sid, sn = data.split(':',1); self.style_id = int(sid); self.style_name = sn
            self._style_filled(); self.update(); e.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, NavyDecryptPage): p = p.parent()
            if p: p._on_style_dropped()
        except: pass
    
    def paintEvent(self, e):
        super().paintEvent(e); p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        if self.is_filled():
            p.setPen(QColor(t['accent'])); p.setFont(QFont("JetBrains Mono",13,QFont.Weight.Bold))
            p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self.style_name)
        else:
            p.setPen(QColor(t['text_tertiary'])); p.setFont(QFont("JetBrains Mono",10))
            p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,"Drag number style here to start")
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.clear_slot()
        p = self.parent()
        while p and not isinstance(p, NavyDecryptPage): p = p.parent()
        if p: p._on_style_cleared()
    
    def update_colors(self, tc): self.colors = tc; self._style_filled() if self.is_filled() else self._style_empty(); self.update()


class ClickableNavyLabel(QLabel):
    def __init__(self, char, parent_page):
        super().__init__()
        self.char = char; self.parent_page = parent_page
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setToolTip(f"Click to add '{char}'")
    
    def mousePressEvent(self, event):
        current = self.parent_page.ci.toPlainText()
        self.parent_page.ci.setPlainText(current + self.char)


class NavyDecryptPage(QWidget):
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager; self.back_callback = back_callback
        self.symbols_dir = os.path.join(sys._MEIPASS if hasattr(sys,'_MEIPASS') else os.path.join(os.path.dirname(__file__),'..'),'assets','symbols','navy')
        self.style_cards = []; self.alphabet_labels = []; self.clickable_labels = []
        self.image_path = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp: self.image_path = fp; self.ip.setText(fp); self._update_image_preview(); break
    
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(40,24,40,24); layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys,'_MEIPASS') else os.path.join(os.path.dirname(__file__),'..'),'assets','icons')
        if os.path.exists(os.path.join(icons_dir,"back.png")): back_btn.setIcon(QIcon(os.path.join(icons_dir,"back.png"))); back_btn.setIconSize(QSize(16,16))
        back_btn.setObjectName("backButton"); back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback); back_btn.setMaximumWidth(100)
        title = QLabel("Navy Signals - Decrypt"); title.setObjectName("pageTitle")
        header.addWidget(back_btn); header.addWidget(title); header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(),"Setup")
        self.tabs.addTab(self._tab_results(),"Results")
        
        layout.addLayout(header); layout.addWidget(self.tabs,1); self._theme()
    
    def _theme(self):
        t = self.theme.current
        self.tabs.setStyleSheet(f"QTabWidget::pane{{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}} QTabBar::tab{{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}} QTabBar::tab:selected{{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}")
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName()=="actionButton": btn.setStyleSheet(f"QPushButton{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background:{t['surface0']};}}")
                elif btn.objectName()=="dangerButton": btn.setStyleSheet(f"QPushButton{{background:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background:{t['surface0']};}}")
            except: pass
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['style_grp','image_group','symbols_group','input_group']:
            if hasattr(self,attr) and getattr(self,attr):
                try: getattr(self,attr).setStyleSheet(gs)
                except: pass
        ts = f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:13px;}}"
        if hasattr(self,'ci') and self.ci: self.ci.setStyleSheet(ts)
        if hasattr(self,'ro') and self.ro: self.ro.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-size:18px;font-weight:700;}}")
        if hasattr(self,'ri') and self.ri: self.ri.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
        if hasattr(self,'ip') and self.ip: self.ip.setStyleSheet(f"QLineEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}")
        if hasattr(self,'image_preview') and self.image_preview: self.image_preview.setStyleSheet(f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['text_tertiary']};font-size:13px;")
        if hasattr(self,'ii') and self.ii: self.ii.setStyleSheet(f"color:{t['text_tertiary']};font-size:11px;background:transparent;")
        if hasattr(self,'style_slot') and self.style_slot: self.style_slot.update_colors(t)
        for card in self.style_cards:
            try: card.update_theme(t)
            except: pass
        for lbl in self.alphabet_labels:
            try: lbl.setStyleSheet(f"font-weight:700;font-size:13px;color:{t['text']};background:transparent;")
            except: pass
        for lbl in self.clickable_labels:
            try: lbl.setStyleSheet(f"QLabel{{background:transparent;border:1px solid transparent;border-radius:4px;padding:2px;}} QLabel:hover{{border:1px solid {t['border']};background:{t['hover']};}}")
            except: pass
        self._reload_symbols()
    
    def _get_symbol_path(self, char):
        if char.isdigit() and self.style_slot and self.style_slot.is_filled() and self.style_slot.style_id == 1:
            alt = NATO_ALT.get(char, char)
            alt_path = os.path.join(self.symbols_dir, f"{alt}.png")
            if os.path.exists(alt_path): return alt_path
        return os.path.join(self.symbols_dir, f"{char}.png")
    
    def _on_style_dropped(self):
        self.symbols_group.setVisible(True)
        self.input_group.setVisible(True)
        self._reload_symbols()
    
    def _on_style_cleared(self):
        self.symbols_group.setVisible(False)
        self.input_group.setVisible(False)
    
    def _reload_symbols(self):
        for lbl in self.clickable_labels:
            try:
                ch = lbl.char
                sp = self._get_symbol_path(ch)
                if os.path.exists(sp):
                    pix = QPixmap(sp)
                    lbl.setPixmap(pix.scaled(44, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            except: pass
    
    def _tab_setup(self):
        w=QWidget();s=QScrollArea();s.setWidgetResizable(True);s.setStyleSheet("border:none;background:transparent;")
        c=QWidget();l=QVBoxLayout(c);l.setContentsMargins(20,16,20,16);l.setSpacing(14)
        
        self.style_grp=QGroupBox("1. Number Style (Drag & Drop)")
        sl=QVBoxLayout();sl.setSpacing(10);cr=QHBoxLayout();cr.setSpacing(12)
        t=self.theme.current
        for sid,sn in [(0,"Normal Numbers"),(1,"NATO Numbers")]:
            card=DraggableStyleCard(sid,sn,t);self.style_cards.append(card);cr.addWidget(card)
        cr.addStretch();sl.addLayout(cr)
        dr=QHBoxLayout();self.style_slot=StyleDropSlot(t);dr.addWidget(self.style_slot);dr.addStretch();sl.addLayout(dr)
        self.style_grp.setLayout(sl);l.addWidget(self.style_grp)
        
        self.image_group=QGroupBox("2. Upload Image")
        il=QVBoxLayout()
        self.image_preview=QLabel("Drag & drop an image here\nor click Browse");self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.image_preview.setFixedHeight(100)
        il.addWidget(self.image_preview)
        ir=QHBoxLayout()
        self.ip=QLineEdit();self.ip.setReadOnly(True);self.ip.setPlaceholderText("Select image...")
        browse=QPushButton("Browse");browse.setObjectName("actionButton");browse.setCursor(Qt.CursorShape.PointingHandCursor);browse.clicked.connect(self._browse)
        ir.addWidget(self.ip,1);ir.addWidget(browse);il.addLayout(ir)
        self.ii=QLabel("");il.addWidget(self.ii)
        self.image_group.setLayout(il);l.addWidget(self.image_group)
        
        self.symbols_group=QGroupBox("3. Click Flags in Order");self.symbols_group.setVisible(False)
        sl2=QVBoxLayout();sl2.setSpacing(2)
        
        r1=QGridLayout();r1.setSpacing(2)
        for i,ch in enumerate('ABCDEFGHIJKLM'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r1.addWidget(lbl,0,i)
            sym=ClickableNavyLabel(ch,self);self.clickable_labels.append(sym)
            r1.addWidget(sym,1,i)
        sl2.addLayout(r1)
        
        r2=QGridLayout();r2.setSpacing(2)
        for i,ch in enumerate('NOPQRSTUVWXYZ'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r2.addWidget(lbl,0,i)
            sym=ClickableNavyLabel(ch,self);self.clickable_labels.append(sym)
            r2.addWidget(sym,1,i)
        sl2.addLayout(r2)
        
        r3=QGridLayout();r3.setSpacing(2)
        for i,ch in enumerate('0123456789'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r3.addWidget(lbl,0,i)
            sym=ClickableNavyLabel(ch,self);self.clickable_labels.append(sym)
            r3.addWidget(sym,1,i)
        sl2.addLayout(r3)
        
        self.symbols_group.setLayout(sl2);l.addWidget(self.symbols_group)
        
        self.input_group=QGroupBox("4. Decoded Characters");self.input_group.setVisible(False)
        dl=QVBoxLayout();dl.setSpacing(8)
        self.ci=QTextEdit();self.ci.setPlaceholderText("Click flags above in order...");self.ci.setMinimumHeight(60);self.ci.setMaximumHeight(80)
        dl.addWidget(self.ci)
        br=QHBoxLayout()
        space=QPushButton("Add Space");space.setObjectName("actionButton");space.setCursor(Qt.CursorShape.PointingHandCursor)
        space.clicked.connect(lambda:self.ci.setPlainText(self.ci.toPlainText()+' '))
        undo=QPushButton("Undo");undo.setObjectName("actionButton");undo.setCursor(Qt.CursorShape.PointingHandCursor)
        undo.clicked.connect(lambda:self.ci.setPlainText(self.ci.toPlainText()[:-1]))
        clear=QPushButton("Clear");clear.setObjectName("dangerButton");clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self.ci.clear)
        br.addWidget(space);br.addWidget(undo);br.addStretch();br.addWidget(clear)
        dl.addLayout(br);self.input_group.setLayout(dl);l.addWidget(self.input_group)
        
        eb=QPushButton("Show Decrypted Text");eb.setObjectName("actionButton");eb.setMinimumHeight(42)
        eb.setCursor(Qt.CursorShape.PointingHandCursor);eb.clicked.connect(self._dec);l.addWidget(eb)
        l.addStretch()
        s.setWidget(c);ow=QVBoxLayout(w);ow.setContentsMargins(0,0,0,0);ow.addWidget(s);return w
    
    def _tab_results(self):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(20,16,20,16);l.setSpacing(12)
        rh=QHBoxLayout();rh.addWidget(QLabel("Decrypted Output:"));rh.addStretch()
        copy=QPushButton("Copy");copy.setObjectName("actionButton");copy.setCursor(Qt.CursorShape.PointingHandCursor);copy.clicked.connect(self._copy)
        rh.addWidget(copy);l.addLayout(rh)
        self.ro=QTextEdit();self.ro.setReadOnly(True);self.ro.setPlaceholderText("Decrypted text...");l.addWidget(self.ro,1)
        self.ri=QLabel("");l.addWidget(self.ri);return w
    
    def _browse(self):
        fp,_=QFileDialog.getOpenFileName(self,"Select Image","","Images (*.png *.jpg *.jpeg *.bmp);;All (*)")
        if fp:self.image_path=fp;self.ip.setText(fp);self._update_image_preview()
    
    def _update_image_preview(self):
        if not self.image_path or not os.path.exists(self.image_path):
            self.image_preview.setText("Drag & drop an image here\nor click Browse");self.ii.setText("");return
        fn=os.path.basename(self.image_path);sz=os.path.getsize(self.image_path)
        ss=f"{sz}B" if sz<1024 else f"{sz/1024:.1f}KB" if sz<1048576 else f"{sz/1048576:.1f}MB"
        pm=QPixmap(self.image_path)
        if not pm.isNull():self.image_preview.setPixmap(pm.scaledToHeight(90,Qt.TransformationMode.SmoothTransformation))
        else:self.image_preview.setText(f"Image\n{fn}")
        self.ii.setText(f"{fn} | {ss}")
    
    def _dec(self):
        ct=self.ci.toPlainText().strip()
        if not ct:QMessageBox.warning(self,"No Input","Please click flags to build ciphertext.");return
        self.ro.setText(ct.upper());self.ri.setText(f"Decoded {len(ct)} characters");self.tabs.setCurrentIndex(1)
    
    def _copy(self):
        t=self.ro.toPlainText()
        if t:QApplication.clipboard().setText(t);QMessageBox.information(self,"Copied","Results copied!")
    
    def refresh_theme(self):self.setStyleSheet("");self._theme()