from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QScrollArea,
                             QLineEdit, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class PasswordCard(QFrame):
    copy_clicked = pyqtSignal(str)
    view_clicked = pyqtSignal(dict)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(self, password_data, parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles

        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 41, 66, 0.7),
                    stop:1 rgba(15, 30, 54, 0.7)
                );
                border: 1px solid rgba(96, 165, 250, 0.2);
                border-radius: 16px;
                padding: 20px;
            }}
            QFrame:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 53, 83, 0.8),
                    stop:1 rgba(15, 30, 54, 0.8)
                );
                border: 1px solid {Styles.BLUE_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QHBoxLayout(); header.setSpacing(14)

        icon_frame = QFrame(); icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 #2563eb);
                border-radius: 12px;
            }}
        """)
        il = QVBoxLayout(icon_frame); il.setContentsMargins(0, 0, 0, 0)

        icon = QLabel(self.password_data.get('site_icon', '🔒'))
        icon.setStyleSheet("font-size: 24px; background: transparent; color: white;")
        icon.setAlignment(Qt.AlignCenter)
        il.addWidget(icon)
        header.addWidget(icon_frame)

        info = QVBoxLayout(); info.setSpacing(4)
        site = QLabel(self.password_data.get('site_name', 'Site'))
        site.setStyleSheet(f"color:{Styles.TEXT_PRIMARY}; font-size:16px; font-weight:bold;")
        site.setFont(QFont("Segoe UI", 13, QFont.Bold))
        user = QLabel(self.password_data.get('username', ''))
        user.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:13px;")
        info.addWidget(site); info.addWidget(user)

        header.addLayout(info); header.addStretch()

        edit_btn = QPushButton("✏️"); edit_btn.setFixedSize(36, 36); edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.password_data['id']))
        delete_btn = QPushButton("🗑️"); delete_btn.setFixedSize(36, 36); delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.password_data['id']))
        for b in (edit_btn, delete_btn):
            b.setStyleSheet("""
                QPushButton { 
                    background: rgba(255,255,255,0.08); 
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius:8px; 
                    font-size:14px; 
                }
                QPushButton:hover { 
                    background: rgba(59,130,246,0.25); 
                    border: 1px solid rgba(59,130,246,0.4);
                }
            """)
            header.addWidget(b)

        layout.addLayout(header)

        pwd_frame = QFrame()
        pwd_frame.setStyleSheet("""
            QFrame { 
                background: rgba(15, 34, 56, 0.6); 
                border: 1px solid rgba(59, 130, 246, 0.2); 
                border-radius:10px; 
                padding:12px; 
            }
        """)
        pl = QHBoxLayout(pwd_frame); pl.setContentsMargins(10,8,10,8)

        from gui.styles.styles import Styles as S
        pwd_label = QLabel("• • • • • • • • • •")
        pwd_label.setStyleSheet(f"color:{S.BLUE_SECONDARY}; font-size:16px; font-family:'Courier New'; letter-spacing:3px; font-weight:bold;")
        pl.addWidget(pwd_label); pl.addStretch()

        copy_btn = QPushButton("📋 Copier"); copy_btn.setFixedHeight(34); copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(self.password_data.get('encrypted_password', '')))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {S.BLUE_PRIMARY}, stop:1 #2563eb);
                color: white; 
                border:none; 
                border-radius:8px; 
                font-size:13px; 
                font-weight:bold;
                padding: 0px 16px;
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #1d4ed8); 
            }}
        """)
        pl.addWidget(copy_btn)

        layout.addWidget(pwd_frame)

        footer = QHBoxLayout(); footer.setSpacing(10)
        strength = self.password_data.get('strength', 'medium')
        sc = {'strong': S.STRONG_COLOR, 'medium': S.MEDIUM_COLOR, 'weak': S.WEAK_COLOR}
        sl = QLabel(f"● {strength.capitalize()}"); sl.setStyleSheet(f"color:{sc.get(strength, S.TEXT_MUTED)}; font-size:10px; font-weight:bold;")
        footer.addWidget(sl); footer.addStretch()
        lm = self.password_data.get('last_modified', "Aujourd'hui")
        dl = QLabel(f"🕒 {lm}"); dl.setStyleSheet("color: rgba(255,255,255,0.6); font-size:10px;")
        footer.addWidget(dl); footer.addSpacing(8)
        cat = self.password_data.get('category', 'personal'); icons = {'personal':'👤','work':'💼','finance':'💳','games':'🎮','study':'📚'}
        cl = QLabel(f"{icons.get(cat,'🔒')} {cat.capitalize()}"); cl.setStyleSheet("color: rgba(255,255,255,0.6); font-size:10px;")
        footer.addWidget(cl)
        layout.addLayout(footer)


class PasswordList(QWidget):
    copy_password = pyqtSignal(str)
    view_password = pyqtSignal(dict)
    edit_password = pyqtSignal(int)
    delete_password = pyqtSignal(int)
    favorite_password = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.passwords = []
        self.filtered_passwords = []
        self.current_filter = 'all'
        self.setStyleSheet("QWidget { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles

        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(20)
        
        title = QLabel("Mes Mots de Passe")
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY}; font-size:24px; font-weight:bold;")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)

        search_container = QFrame(); search_container.setFixedWidth(400)
        search_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        sl = QHBoxLayout(search_container); sl.setContentsMargins(0,0,0,0); sl.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.setFrame(False)
        self.search_input.setMinimumHeight(44)
        self.search_input.setFont(QFont("Segoe UI", 13))
        self.search_input.setTextMargins(16, 0, 16, 0)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(26, 41, 66, 0.8);
                border: 1px solid rgba(96,165,250,0.25);
                border-radius: 22px;
                padding: 10px 16px;
                color: {Styles.TEXT_PRIMARY};
                selection-background-color: {Styles.BLUE_PRIMARY};
                selection-color: white;
                font-size: 14px;
            }}
            QLineEdit::placeholder {{ color: {Styles.TEXT_MUTED}; }}
            QLineEdit:focus {{
                border: 1px solid {Styles.BLUE_PRIMARY};
            }}
        """)
        self.search_input.textChanged.connect(self.on_search)
        sl.addWidget(self.search_input, 1)

        self.filter_btn = QPushButton("🔍"); self.filter_btn.setFixedSize(44,44); self.filter_btn.setCursor(Qt.PointingHandCursor)
        self.filter_btn.clicked.connect(self.show_filter_menu)
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(59,130,246,0.15); 
                border: 1px solid rgba(59,130,246,0.3);
                border-radius:22px; 
                font-size:16px; 
                color:{Styles.BLUE_SECONDARY};
            }}
            QPushButton:hover {{ 
                background: rgba(59,130,246,0.25); 
                border: 1px solid rgba(59,130,246,0.5);
            }}
        """)
        sl.addWidget(self.filter_btn)
        header.addWidget(search_container)
        main.addLayout(header)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: rgba(255,255,255,0.03); width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #3b82f6; border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container); self.grid_layout.setSpacing(16); self.grid_layout.setContentsMargins(5,5,5,5)
        scroll.setWidget(self.grid_container)
        main.addWidget(scroll)

    def show_filter_menu(self):
        from gui.styles.styles import Styles
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:#1a293f; border:1px solid #2d4466; border-radius:12px; padding:8px; }}
            QMenu::item {{ padding:10px 20px; border-radius:8px; color:{Styles.TEXT_PRIMARY}; font-size:13px; }}
            QMenu::item:selected {{ background: rgba(59,130,246,0.2); }}
        """)
        filters = [
            ("📋 Tous les mots de passe", 'all'),
            ("🔒 Forts seulement", 'strong'),
            ("⚠️ Moyens seulement", 'medium'),
            ("💔 Faibles seulement", 'weak'),
            ("⭐ Favoris", 'favorites'),
            ("💼 Travail", 'work'), ("👤 Personnel", 'personal'),
            ("💳 Finance", 'finance'), ("🎮 Jeux", 'games'), ("📚 Étude", 'study')
        ]
        for text, ftype in filters:
            act = QAction(text, self); act.triggered.connect(lambda _, f=ftype: self.apply_filter(f))
            menu.addAction(act)
        menu.exec_(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        if filter_type == 'all': filtered = self.passwords
        elif filter_type in ('strong','medium','weak'): filtered = [p for p in self.passwords if p.get('strength') == filter_type]
        elif filter_type == 'favorites': filtered = [p for p in self.passwords if p.get('favorite')]
        else: filtered = [p for p in self.passwords if p.get('category') == filter_type]
        self.load_passwords(filtered)

    def load_passwords(self, passwords):
        self.passwords = passwords
        self.filtered_passwords = passwords[:]

        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w: w.setParent(None)

        row_widget, row_layout = None, None
        for i, pwd in enumerate(self.filtered_passwords):
            if i % 2 == 0:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setSpacing(15); row_layout.setContentsMargins(0,0,0,0)
                self.grid_layout.addWidget(row_widget)

            card = PasswordCard(pwd)
            card.copy_clicked.connect(self.copy_password.emit)
            card.view_clicked.connect(self.view_password.emit)
            card.edit_clicked.connect(self.edit_password.emit)
            card.delete_clicked.connect(self.delete_password.emit)
            row_layout.addWidget(card)

        if self.filtered_passwords and len(self.filtered_passwords) % 2 == 1:
            row_layout.addStretch()
        self.grid_layout.addStretch()

    def on_search(self, text):
        t = text.strip().lower()
        if not t: self.apply_filter(self.current_filter); return
        filtered = [p for p in self.passwords
                    if (t in p.get('site_name','').lower()
                        or t in p.get('username','').lower()
                        or t in p.get('category','').lower())]
        self.load_passwords(filtered)