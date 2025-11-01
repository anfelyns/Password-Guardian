from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QScrollArea,
                             QLineEdit, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class PasswordCard(QFrame):
    """Modern password card with rounded design - optimized width"""
    copy_clicked = pyqtSignal(str)
    view_clicked = pyqtSignal(dict)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    favorite_clicked = pyqtSignal(int)
    
    # 2FA signals
    request_2fa_for_copy = pyqtSignal(str)
    request_2fa_for_view = pyqtSignal(dict)

    def __init__(self, password_data, parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self.init_ui()

    def init_ui(self):
        from src.gui.styles.styles import Styles

        # Modern card with fixed width
        self.setFixedWidth(650)  # Fixed width to prevent horizontal scrolling
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 48, 80, 0.85),
                    stop:1 rgba(20, 35, 60, 0.85)
                );
                border: 1px solid rgba(96, 165, 250, 0.25);
                border-radius: 20px;
                padding: 20px;
            }}
            QFrame:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 60, 95, 0.9),
                    stop:1 rgba(25, 40, 70, 0.9)
                );
                border: 1px solid {Styles.BLUE_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header: Icon + Site Name + Action Buttons
        header = QHBoxLayout()
        header.setSpacing(12)

        # Icon with gradient background
        icon_frame = QFrame()
        icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.PURPLE});
                border-radius: 14px;
                border: none;
            }}
        """)
        il = QVBoxLayout(icon_frame)
        il.setContentsMargins(0, 0, 0, 0)

        icon = QLabel(self.password_data.get('site_icon', '🔒'))
        icon.setStyleSheet("font-size: 24px; background: transparent; color: white;")
        icon.setAlignment(Qt.AlignCenter)
        il.addWidget(icon)
        header.addWidget(icon_frame)

        # Site name and username
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        site = QLabel(self.password_data.get('site_name', 'Site'))
        site.setStyleSheet(f"""
            color: {Styles.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        """)
        site.setFont(QFont("Segoe UI", 14, QFont.Bold))
        
        user = QLabel(self.password_data.get('username', ''))
        user.setStyleSheet(f"""
            color: {Styles.TEXT_SECONDARY};
            font-size: 12px;
            background: transparent;
        """)
        user.setWordWrap(True)
        
        info_layout.addWidget(site)
        info_layout.addWidget(user)
        header.addLayout(info_layout, 1)

        # Action buttons (view, edit, delete)
        btn_container = QHBoxLayout()
        btn_container.setSpacing(6)

        view_btn = QPushButton("👁️")
        edit_btn = QPushButton("✏️")
        delete_btn = QPushButton("🗑️")

        for btn in (view_btn, edit_btn, delete_btn):
            btn.setFixedSize(34, 34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { 
                    background: rgba(255,255,255,0.08); 
                    border: 1px solid rgba(255,255,255,0.15);
                    border-radius: 10px; 
                    font-size: 14px; 
                }
                QPushButton:hover { 
                    background: rgba(59,130,246,0.3); 
                    border: 1px solid rgba(59,130,246,0.5);
                }
            """)

        view_btn.setToolTip("Voir le mot de passe")
        edit_btn.setToolTip("Modifier")
        delete_btn.setToolTip("Supprimer")
        
        # View and edit with 2FA
        view_btn.clicked.connect(lambda: self.request_2fa_for_view.emit(self.password_data))
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.password_data['id']))
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.password_data['id']))

        btn_container.addWidget(view_btn)
        btn_container.addWidget(edit_btn)
        btn_container.addWidget(delete_btn)
        
        header.addLayout(btn_container)
        layout.addLayout(header)

        # Password display with copy button
        pwd_container = QFrame()
        pwd_container.setStyleSheet(f"""
            QFrame {{ 
                background: rgba(15, 34, 56, 0.7); 
                border: 1px solid rgba(59, 130, 246, 0.25); 
                border-radius: 12px; 
                padding: 12px 14px; 
            }}
        """)
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        pwd_layout.setSpacing(10)

        pwd_label = QLabel("• • • • • • • • • •")
        pwd_label.setStyleSheet(f"""
            color: {Styles.BLUE_SECONDARY};
            font-size: 16px;
            font-family: 'Courier New', monospace;
            letter-spacing: 3px;
            font-weight: bold;
            background: transparent;
        """)
        pwd_layout.addWidget(pwd_label)
        pwd_layout.addStretch()

        copy_btn = QPushButton("📋 Copier")
        copy_btn.setFixedHeight(36)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setToolTip("Copier le mot de passe (nécessite 2FA)")
        # Copy with 2FA
        copy_btn.clicked.connect(lambda: self.request_2fa_for_copy.emit(
            self.password_data.get('encrypted_password', '')
        ))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.BLUE_SECONDARY});
                color: white; 
                border: none; 
                border-radius: 10px; 
                font-size: 12px; 
                font-weight: bold;
                padding: 0px 16px;
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.BLUE_SECONDARY}, stop:1 {Styles.BLUE_PRIMARY});
            }}
        """)
        pwd_layout.addWidget(copy_btn)

        layout.addWidget(pwd_container)

        # Footer: Strength + Category + Date + Favorite
        footer = QHBoxLayout()
        footer.setSpacing(10)
        
        # Strength indicator
        strength = self.password_data.get('strength', 'medium')
        sc = {
            'strong': (Styles.STRONG_COLOR, 'Fort'),
            'medium': (Styles.MEDIUM_COLOR, 'Moyen'),
            'weak': (Styles.WEAK_COLOR, 'Faible')
        }
        color, text = sc.get(strength, (Styles.TEXT_MUTED, 'Inconnu'))
        
        strength_frame = QFrame()
        strength_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (26,)};
                border: 1px solid rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (51,)};
                border-radius: 8px;
                padding: 5px 10px;
            }}
        """)
        sl_layout = QHBoxLayout(strength_frame)
        sl_layout.setContentsMargins(0, 0, 0, 0)
        sl_layout.setSpacing(5)
        
        sl = QLabel(f"● {text}")
        sl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: transparent;")
        sl_layout.addWidget(sl)
        
        footer.addWidget(strength_frame)
        
        # Category
        cat = self.password_data.get('category', 'personal')
        icons = {'personal':'👤','work':'💼','finance':'💳','game':'🎮','games':'🎮','study':'📚','trash':'🗑️'}
        cat_labels = {
            'personal': 'Personnel',
            'work': 'Travail',
            'finance': 'Finance',
            'game': 'Jeux',
            'study': 'Étude'
        }
        
        cl = QLabel(f"{icons.get(cat,'🔒')} {cat_labels.get(cat, cat.capitalize())}")
        cl.setStyleSheet(f"color: {Styles.TEXT_MUTED}; font-size: 10px; background: transparent;")
        footer.addWidget(cl)
        
        # Last modified date
        last_updated = self.password_data.get('last_updated', '')
        if last_updated:
            # Format date nicely
            from datetime import datetime
            try:
                if isinstance(last_updated, str):
                    # Try to parse and format
                    date_label = QLabel(f"🕒 {last_updated}")
                else:
                    date_label = QLabel(f"🕒 {last_updated.strftime('%d/%m/%Y %H:%M')}")
            except:
                date_label = QLabel(f"🕒 {str(last_updated)}")
            
            date_label.setStyleSheet(f"color: {Styles.TEXT_MUTED}; font-size: 10px; background: transparent;")
            footer.addWidget(date_label)
        
        footer.addStretch()
        
        # Favorite button
        is_favorite = self.password_data.get('favorite', False)
        self.favorite_btn = QPushButton("⭐" if is_favorite else "☆")
        self.favorite_btn.setFixedSize(30, 30)
        self.favorite_btn.setCursor(Qt.PointingHandCursor)
        self.favorite_btn.setToolTip("Ajouter aux favoris" if not is_favorite else "Retirer des favoris")
        self.favorite_btn.clicked.connect(lambda: self.favorite_clicked.emit(self.password_data['id']))
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {'rgba(255,193,7,0.2)' if is_favorite else 'rgba(255,255,255,0.08)'}; 
                border: 1px solid {'rgba(255,193,7,0.4)' if is_favorite else 'rgba(255,255,255,0.15)'};
                border-radius: 8px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                background: rgba(255,193,7,0.3); 
                border: 1px solid rgba(255,193,7,0.5);
            }}
        """)
        footer.addWidget(self.favorite_btn)
        
        layout.addLayout(footer)


class PasswordList(QWidget):
    copy_password = pyqtSignal(str)
    view_password = pyqtSignal(dict)
    edit_password = pyqtSignal(int)
    delete_password = pyqtSignal(int)
    favorite_password = pyqtSignal(int)
    restore_password = pyqtSignal(int)
    
    # 2FA signals
    request_2fa_for_copy = pyqtSignal(str)
    request_2fa_for_view = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.passwords = []
        self.filtered_passwords = []
        self.current_filter = 'all'
        self.setStyleSheet("QWidget { background: transparent; }")
        self.init_ui()

    def init_ui(self):
        from src.gui.styles.styles import Styles

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(20)
        
        title = QLabel("Mes Mots de Passe")
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY}; font-size:24px; font-weight:bold;")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)

        search_container = QFrame()
        search_container.setFixedWidth(400)
        search_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        sl = QHBoxLayout(search_container)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(8)

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

        self.filter_btn = QPushButton("🔍")
        self.filter_btn.setFixedSize(44, 44)
        self.filter_btn.setCursor(Qt.PointingHandCursor)
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scroll
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { 
                background: rgba(255,255,255,0.03); 
                width: 10px; 
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(96, 165, 250, 0.3);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(96, 165, 250, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.grid_container)
        main.addWidget(scroll)

    def show_filter_menu(self):
        from src.gui.styles.styles import Styles
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ 
                background: {Styles.PRIMARY_BG}; 
                border: 1px solid rgba(255,255,255,0.2); 
                border-radius: 12px; 
                padding: 10px; 
            }}
            QMenu::item {{ 
                padding:10px 20px; 
                border-radius:8px; 
                color:{Styles.TEXT_PRIMARY}; 
                font-size:13px; 
            }}
            QMenu::item:selected {{ 
                background: rgba(59,130,246,0.2); 
            }}
        """)
        filters = [
            ("📋 Tous les mots de passe", 'all'),
            ("🔒 Forts seulement", 'strong'),
            ("⚠️ Moyens seulement", 'medium'),
            ("💔 Faibles seulement", 'weak'),
            ("⭐ Favoris", 'favorites'),
            ("💼 Travail", 'work'),
            ("👤 Personnel", 'personal'),
            ("💳 Finance", 'finance'),
            ("🎮 Jeux", 'game'),
            ("📚 Étude", 'study')
        ]
        for text, ftype in filters:
            act = QAction(text, self)
            act.triggered.connect(lambda _, f=ftype: self.apply_filter(f))
            menu.addAction(act)
        menu.exec_(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        if filter_type == 'all':
            filtered = self.passwords
        elif filter_type in ('strong', 'medium', 'weak'):
            filtered = [p for p in self.passwords if p.get('strength') == filter_type]
        elif filter_type == 'favorites':
            filtered = [p for p in self.passwords if p.get('favorite')]
        else:
            filtered = [p for p in self.passwords if p.get('category') == filter_type]
        self.load_passwords(filtered)

    def load_passwords(self, passwords):
        """Load passwords in single column layout (vertical only)"""
        self.passwords = passwords
        self.filtered_passwords = passwords[:]

        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w: 
                w.setParent(None)

        if not passwords or len(passwords) == 0:
            from src.gui.styles.styles import Styles
            
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background: transparent; border: none;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(0, 80, 0, 80)
            empty_layout.setSpacing(20)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            empty_icon = QLabel("🔒")
            empty_icon.setStyleSheet("font-size: 80px; background: transparent;")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_icon)
            
            empty_text = QLabel("Aucun mot de passe")
            empty_text.setStyleSheet(f"""
                color: {Styles.TEXT_PRIMARY};
                font-size: 22px;
                font-weight: bold;
                background: transparent;
            """)
            empty_text.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_text)
            
            empty_desc = QLabel("Cliquez sur 'Nouveau Mot de Passe' pour commencer à sécuriser vos comptes")
            empty_desc.setStyleSheet(f"""
                color: {Styles.TEXT_MUTED};
                font-size: 14px;
                background: transparent;
            """)
            empty_desc.setAlignment(Qt.AlignCenter)
            empty_desc.setWordWrap(True)
            empty_desc.setMaximumWidth(400)
            empty_layout.addWidget(empty_desc)
            
            self.grid_layout.addWidget(empty_frame)
            return

        # Create single column layout (vertical scrolling only)
        for pwd in self.filtered_passwords:
            card = PasswordCard(pwd)
            # Forward 2FA signals
            card.request_2fa_for_copy.connect(self.request_2fa_for_copy.emit)
            card.request_2fa_for_view.connect(self.request_2fa_for_view.emit)
            # Regular signals
            card.copy_clicked.connect(self.copy_password.emit)
            card.view_clicked.connect(self.view_password.emit)
            card.edit_clicked.connect(self.edit_password.emit)
            card.delete_clicked.connect(self.delete_password.emit)
            card.favorite_clicked.connect(self.favorite_password.emit)
            
            # Center the card
            card_wrapper = QWidget()
            card_layout = QHBoxLayout(card_wrapper)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.addStretch()
            card_layout.addWidget(card)
            card_layout.addStretch()
            
            self.grid_layout.addWidget(card_wrapper)
        
        self.grid_layout.addStretch()

    def on_search(self, text):
        t = text.strip().lower()
        if not t:
            self.apply_filter(self.current_filter)
            return
        filtered = [p for p in self.passwords
                    if (t in p.get('site_name', '').lower()
                        or t in p.get('username', '').lower()
                        or t in p.get('category', '').lower())]
        self.load_passwords(filtered)