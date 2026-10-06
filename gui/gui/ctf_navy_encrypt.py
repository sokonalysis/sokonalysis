# gui/ctf_navy_encrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QScrollArea, QGridLayout, QFileDialog, QFrame,
    QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QMimeData
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QDrag
import os, sys, base64


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
            while p and not isinstance(p, NavyEncryptPage): p = p.parent()
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
        while p and not isinstance(p, NavyEncryptPage): p = p.parent()
        if p: p._on_style_cleared()
    
    def update_colors(self, tc): self.colors = tc; self._style_filled() if self.is_filled() else self._style_empty(); self.update()


class NavyEncryptPage(QWidget):
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager; self.back_callback = back_callback
        self.symbols_dir = os.path.join(sys._MEIPASS if hasattr(sys,'_MEIPASS') else os.path.join(os.path.dirname(__file__),'..'),'assets','symbols','navy')
        self.style_cards = []; self.alphabet_labels = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(40,24,40,24); layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys,'_MEIPASS') else os.path.join(os.path.dirname(__file__),'..'),'assets','icons')
        if os.path.exists(os.path.join(icons_dir,"back.png")): back_btn.setIcon(QIcon(os.path.join(icons_dir,"back.png"))); back_btn.setIconSize(QSize(16,16))
        back_btn.setObjectName("backButton"); back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback); back_btn.setMaximumWidth(100)
        title = QLabel("Navy Signals - Encrypt"); title.setObjectName("pageTitle")
        header.addWidget(back_btn); header.addWidget(title); header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(),"Setup")
        self.tabs.addTab(self._tab_results(),"Results")
        self.tabs.addTab(self._tab_alphabet(),"Alphabet")
        
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
        for attr in ['style_grp','ig']:
            if hasattr(self,attr) and getattr(self,attr):
                try: getattr(self,attr).setStyleSheet(gs)
                except: pass
        ts = f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:13px;}}"
        if hasattr(self,'pi') and self.pi: self.pi.setStyleSheet(ts)
        if hasattr(self,'rt') and self.rt: self.rt.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-size:18px;font-weight:700;}}")
        if hasattr(self,'ri') and self.ri: self.ri.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
        if hasattr(self,'style_slot') and self.style_slot: self.style_slot.update_colors(t)
        for card in self.style_cards:
            try: card.update_theme(t)
            except: pass
        # Update all alphabet labels
        for lbl in self.alphabet_labels:
            try: lbl.setStyleSheet(f"font-weight:700;font-size:13px;color:{t['text']};background:transparent;")
            except: pass
    
    def _on_style_dropped(self): self.ig.setVisible(True)
    def _on_style_cleared(self): self.ig.setVisible(False)
    
    def _get_symbol_path(self, char):
        if char.isdigit() and self.style_slot and self.style_slot.is_filled() and self.style_slot.style_id == 1:
            alt = NATO_ALT.get(char, char)
            alt_path = os.path.join(self.symbols_dir, f"{alt}.png")
            if os.path.exists(alt_path): return alt_path
        return os.path.join(self.symbols_dir, f"{char}.png")
    
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
        
        self.ig=QGroupBox("2. Plaintext");self.ig.setVisible(False)
        il=QVBoxLayout();il.setSpacing(8)
        self.pi=QTextEdit();self.pi.setPlaceholderText("Enter plaintext to encrypt...");self.pi.setMinimumHeight(120);il.addWidget(self.pi)
        br=QHBoxLayout()
        pb=QPushButton("Paste");pb.setObjectName("actionButton");pb.setCursor(Qt.CursorShape.PointingHandCursor);pb.clicked.connect(self._paste)
        cb=QPushButton("Clear");cb.setObjectName("dangerButton");cb.setCursor(Qt.CursorShape.PointingHandCursor);cb.clicked.connect(self.pi.clear)
        br.addWidget(pb);br.addWidget(cb);br.addStretch();il.addLayout(br)
        self.ig.setLayout(il);l.addWidget(self.ig)
        eb=QPushButton("Encrypt");eb.setObjectName("actionButton");eb.setMinimumHeight(48);eb.setCursor(Qt.CursorShape.PointingHandCursor);eb.clicked.connect(self._enc);l.addWidget(eb)
        l.addStretch()
        s.setWidget(c);ow=QVBoxLayout(w);ow.setContentsMargins(0,0,0,0);ow.addWidget(s);return w
    
    def _tab_results(self):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(20,16,20,16);l.setSpacing(12)
        rh=QHBoxLayout();rh.addWidget(QLabel("Encrypted Output:"));rh.addStretch()
        copy=QPushButton("Copy as Text");copy.setObjectName("actionButton");copy.setCursor(Qt.CursorShape.PointingHandCursor);copy.clicked.connect(self._copy_txt)
        export=QPushButton("Export PNG");export.setObjectName("actionButton");export.setCursor(Qt.CursorShape.PointingHandCursor);export.clicked.connect(self._export)
        rh.addWidget(copy);rh.addWidget(export);l.addLayout(rh)
        self.rt=QTextEdit();self.rt.setReadOnly(True);l.addWidget(self.rt,1)
        self.ri=QLabel("");l.addWidget(self.ri);return w
    
    def _tab_alphabet(self):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(0,0,0,0);l.setSpacing(0)
        t=self.theme.current
        
        # A-M
        r1=QGridLayout();r1.setSpacing(0);r1.setContentsMargins(0,0,0,0)
        for i,ch in enumerate('ABCDEFGHIJKLM'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r1.addWidget(lbl,0,i)
            sp=os.path.join(self.symbols_dir,f"{ch}.png");sym=QLabel();sym.setAlignment(Qt.AlignmentFlag.AlignCenter);sym.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
            if os.path.exists(sp):pix=QPixmap(sp);sym.setPixmap(pix.scaled(48,40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            r1.addWidget(sym,1,i)
        l.addLayout(r1,1)
        
        # N-Z
        r2=QGridLayout();r2.setSpacing(0);r2.setContentsMargins(0,0,0,0)
        for i,ch in enumerate('NOPQRSTUVWXYZ'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r2.addWidget(lbl,0,i)
            sp=os.path.join(self.symbols_dir,f"{ch}.png");sym=QLabel();sym.setAlignment(Qt.AlignmentFlag.AlignCenter);sym.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
            if os.path.exists(sp):pix=QPixmap(sp);sym.setPixmap(pix.scaled(48,40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            r2.addWidget(sym,1,i)
        l.addLayout(r2,1)
        
        # 0-9 Standard
        r3=QGridLayout();r3.setSpacing(0);r3.setContentsMargins(0,0,0,0)
        for i,ch in enumerate('0123456789'):
            lbl=QLabel(ch);lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);self.alphabet_labels.append(lbl)
            r3.addWidget(lbl,0,i)
            sp=os.path.join(self.symbols_dir,f"{ch}.png");sym=QLabel();sym.setAlignment(Qt.AlignmentFlag.AlignCenter);sym.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
            if os.path.exists(sp):pix=QPixmap(sp);sym.setPixmap(pix.scaled(48,40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            r3.addWidget(sym,1,i)
        l.addLayout(r3,1)
        
        # NATO 0-9
        r4=QGridLayout();r4.setSpacing(0);r4.setContentsMargins(0,0,0,0)
        for i,ch in enumerate('0123456789'):
            ap=os.path.join(self.symbols_dir,f"{NATO_ALT[ch]}.png");sym=QLabel();sym.setAlignment(Qt.AlignmentFlag.AlignCenter);sym.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
            if os.path.exists(ap):pix=QPixmap(ap);sym.setPixmap(pix.scaled(48,40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            r4.addWidget(sym,0,i)
        l.addLayout(r4,1)
        
        return w
    
    def _paste(self):
        c=QApplication.clipboard().text()
        if c:self.pi.setPlainText(c)
    
    def _enc(self):
        pt=self.pi.toPlainText().strip().upper()
        if not pt:QMessageBox.warning(self,"No Input","Please enter plaintext.");return
        self._lp=pt
        hp=['<div style="line-height:2.5;">']
        for ch in pt:
            if ch==' ':hp.append('<span style="display:inline-block;width:24px;"></span>')
            elif ch in NAVY_CHARS:
                ip=self._get_symbol_path(ch)
                if os.path.exists(ip):
                    with open(ip,'rb') as f:b64=base64.b64encode(f.read()).decode()
                    hp.append(f'<img src="data:image/png;base64,{b64}" width="64" height="52" style="vertical-align:middle;margin:2px;" title="{ch}">')
        hp.append('</div>')
        self.rt.setHtml(''.join(hp));self.ri.setText(f"Encrypted {len(pt)} characters");self.tabs.setCurrentIndex(1)
    
    def _copy_txt(self):
        if not hasattr(self,'_lp'):QMessageBox.warning(self,"Nothing","Run encryption first.");return
        r=[]
        for ch in self._lp:
            if ch==' ':r.append(' ')
            elif ch in NAVY_CHARS:r.append(f'[{ch}]')
        QApplication.clipboard().setText(''.join(r));QMessageBox.information(self,"Copied","Copied!")
    
    def _export(self):
        if not hasattr(self,'_lp'):QMessageBox.warning(self,"Nothing","Run encryption first.");return
        fp,_=QFileDialog.getSaveFileName(self,"Export","navy.png","PNG (*.png)")
        if not fp:return
        cw,sp,aw=70,4,800;lines=[];cl=[];cw_tot=0
        for ch in self._lp:
            if ch==' ':cw_tot+=28
            elif ch in NAVY_CHARS:cw_tot+=cw+sp
            if cw_tot>aw:lines.append(cl);cl=[];cw_tot=cw+sp if ch!=' ' else 0
            cl.append(ch)
        if cl:lines.append(cl)
        lh,pad=60,10;ph=pad*2+len(lines)*lh
        pm=QPixmap(aw+pad*2,ph);pm.fill(Qt.GlobalColor.transparent);p=QPainter(pm);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        y=pad
        for ln in lines:
            x=pad
            for ch in ln:
                if ch==' ':x+=28
                else:
                    ip=self._get_symbol_path(ch)
                    if os.path.exists(ip):sym=QPixmap(ip).scaled(64,52,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation);p.drawPixmap(x,y+4,sym)
                    x+=cw+sp
            y+=lh
        p.end();pm.save(fp,"PNG");QMessageBox.information(self,"Exported","Saved!")
    
    def refresh_theme(self):self.setStyleSheet("");self._theme()