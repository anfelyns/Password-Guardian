# src/gui/components/password_list.py - COMPLETE WITH ALL FEATURES

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QLineEdit, QMenu, QAction, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime


class PasswordCard(QFrame):
    """Compact, beautiful password card with all features"""
    copy_clicked = pyqtSignal(str)
    view_clicked = pyqtSignal(dict)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    favorite_clicked = pyqtSignal(int)

    def __init__(self, password_data, parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles

        # Compact card with fixed height
        self.setFixedHeight(160)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(71, 85, 105, 0.3);
                border-radius: 12px;
            }}
            QFrame:hover {{
                background: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(96, 165, 250, 0.5);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        # ========== TOP: Icon + Site Name + Favorite + Actions ==========
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Icon (smaller, 40x40)
        icon_frame = QFrame()
        icon_frame.setFixedSize(40, 40)
        
        # Get category for color
        category = self.password_data.get('category', 'personal')
        category_colors = {
            'work': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #6d28d9)',
            'personal': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #2563eb)',
            'finance': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #059669)',
            'game': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f59e0b, stop:1 #d97706)',
            'study': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ec4899, stop:1 #db2777)',
        }
        
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: {category_colors.get(category, category_colors['personal'])};
                border-radius: 10px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        # Site icon (emoji or first letter)
        site_icon = self.password_data.get('site_icon', '')
        if not site_icon:
            site_name = self.password_data.get('site_name', 'S')
            site_icon = site_name[0].upper()
        
        icon = QLabel(site_icon)
        icon.setStyleSheet("font-size: 20px; background: transparent; color: white;")
        icon.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon)
        
        top_row.addWidget(icon_frame)

        # Site name + username
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        site_label = QLabel(self.password_data.get('site_name', 'Site'))
        site_label.setStyleSheet("""
            color: white; 
            font-size: 15px; 
            font-weight: 600; 
            background: transparent;
        """)
        site_label.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        
        user_label = QLabel(self.password_data.get('username', ''))
        user_label.setStyleSheet("""
            color: rgba(148, 163, 184, 1); 
            font-size: 12px; 
            background: transparent;
        """)
        
        info_layout.addWidget(site_label)
        info_layout.addWidget(user_label)
        top_row.addLayout(info_layout)
        
        top_row.addStretch()

        # Action buttons: Favorite (star), View (eye), Delete (trash)
        is_favorite = self.password_data.get('favorite', False)
        
        fav_btn = QPushButton("⭐" if is_favorite else "☆")
        fav_btn.setFixedSize(28, 28)
        fav_btn.setCursor(Qt.PointingHandCursor)
        fav_btn.setToolTip("Favori")
        fav_btn.clicked.connect(lambda: self.favorite_clicked.emit(self.password_data['id']))
        fav_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {'rgba(250, 204, 21, 0.2)' if is_favorite else 'rgba(71, 85, 105, 0.3)'}; 
                border: none;
                border-radius: 6px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                background: rgba(250, 204, 21, 0.3); 
            }}
        """)
        
        view_btn = QPushButton("👁️")
        view_btn.setFixedSize(28, 28)
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.setToolTip("Voir le mot de passe")
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.password_data))
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setToolTip("Supprimer")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.password_data['id']))
        
        for btn in (view_btn, delete_btn):
            btn.setStyleSheet("""
                QPushButton { 
                    background: rgba(71, 85, 105, 0.3); 
                    border: none;
                    border-radius: 6px; 
                    font-size: 13px;
                }
                QPushButton:hover { 
                    background: rgba(96, 165, 250, 0.3); 
                }
            """)
        
        top_row.addWidget(fav_btn)
        top_row.addWidget(view_btn)
        top_row.addWidget(delete_btn)

        layout.addLayout(top_row)

        # ========== MIDDLE: Password dots + Copy button ==========
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)

        pwd_dots = QLabel("• • • • • • • • • •")
        pwd_dots.setStyleSheet("""
            color: rgba(148, 163, 184, 0.8); 
            font-size: 14px; 
            font-family: 'Courier New';
            letter-spacing: 2px;
            background: transparent;
        """)
        pwd_row.addWidget(pwd_dots)
        pwd_row.addStretch()

        copy_btn = QPushButton("📋 Copier")
        copy_btn.setFixedHeight(30)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(lambda: self.copy_clicked.emit(
            self.password_data.get('encrypted_password', '')
        ))
        copy_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-size: 12px; 
                font-weight: 600;
                padding: 0px 14px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2563eb, stop:1 #1d4ed8); 
            }
        """)
        pwd_row.addWidget(copy_btn)
        
        layout.addLayout(pwd_row)

        # ========== BOTTOM: Strength bar + Last modified + Category ==========
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        
        # Strength indicator (compact)
        strength = self.password_data.get('strength', 'medium')
        strength_config = {
            'strong': ('Fort:', '#10b981'),
            'medium': ('Moyen:', '#f59e0b'),
            'weak': ('Faible:', '#ef4444')
        }
        
        strength_text, strength_color = strength_config.get(strength, ('Moyen:', '#f59e0b'))
        
        strength_label = QLabel(strength_text)
        strength_label.setStyleSheet(f"""
            color: {strength_color}; 
            font-size: 10px; 
            font-weight: 600;
            background: transparent;
        """)
        bottom_row.addWidget(strength_label)
        
        # Strength bar (mini progress bar)
        strength_value = {'strong': 100, 'medium': 60, 'weak': 30}.get(strength, 60)
        
        strength_bar_container = QFrame()
        strength_bar_container.setFixedSize(50, 4)
        strength_bar_container.setStyleSheet("""
            QFrame {
                background: rgba(71, 85, 105, 0.3);
                border-radius: 2px;
            }
        """)
        
        strength_bar = QFrame(strength_bar_container)
        strength_bar.setFixedSize(int(50 * strength_value / 100), 4)
        strength_bar.setStyleSheet(f"""
            QFrame {{
                background: {strength_color};
                border-radius: 2px;
            }}
        """)
        
        bottom_row.addWidget(strength_bar_container)
        bottom_row.addStretch()
        
        # Last modified date
        last_modified = self.password_data.get('last_updated') or self.password_data.get('created_at')
        if last_modified:
            if isinstance(last_modified, str) and len(last_modified) > 10:
                try:
                    dt = datetime.strptime(last_modified, '%Y-%m-%d %H:%M:%S')
                    # Calculate days ago
                    days_ago = (datetime.now() - dt).days
                    if days_ago == 0:
                        date_text = "Aujourd'hui"
                    elif days_ago == 1:
                        date_text = "Hier"
                    elif days_ago < 7:
                        date_text = f"Il y a {days_ago}j"
                    elif days_ago < 30:
                        weeks = days_ago // 7
                        date_text = f"Il y a {weeks}sem"
                    else:
                        date_text = dt.strftime('%d/%m/%Y')
                except:
                    date_text = "Récent"
            else:
                date_text = "Récent"
        else:
            date_text = "Aujourd'hui"
        
        date_label = QLabel(f"🕐 {date_text}")
        date_label.setStyleSheet("""
            color: rgba(148, 163, 184, 0.8); 
            font-size: 10px;
            background: transparent;
        """)
        bottom_row.addWidget(date_label)
        
        # Category badge
        category_icons = {
            'personal': '👤', 
            'work': '💼', 
            'finance': '💳', 
            'game': '🎮', 
            'study': '📚'
        }
        
        category_label = QLabel(category_icons.get(category, '🔒'))
        category_label.setFixedSize(20, 20)
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setToolTip(category.capitalize())
        category_label.setStyleSheet("""
            font-size: 14px;
            background: transparent;
        """)
        bottom_row.addWidget(category_label)
        
        layout.addLayout(bottom_row)


class PasswordList(QWidget):
    """Password list with 2-column grid"""
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # ========== HEADER ==========
        header = QHBoxLayout()
        header.setSpacing(20)
        
        title = QLabel("Mes Mots de Passe")
        title.setStyleSheet("""
            color: white; 
            font-size: 24px; 
            font-weight: 600; 
            background: transparent;
        """)
        title.setFont(QFont("Segoe UI", 22, QFont.DemiBold))
        header.addWidget(title)

        # Search box (compact)
        search_container = QFrame()
        search_container.setFixedWidth(350)
        search_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.setFrame(False)
        self.search_input.setMinimumHeight(40)
        self.search_input.setFont(QFont("Segoe UI", 13))
        self.search_input.setTextMargins(14, 0, 14, 0)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(71, 85, 105, 0.3);
                border-radius: 10px;
                padding: 8px 14px;
                color: white;
                font-size: 13px;
            }
            QLineEdit::placeholder { color: rgba(148, 163, 184, 0.6); }
            QLineEdit:focus { border: 1px solid rgba(96, 165, 250, 0.5); }
        """)
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input, 1)

        self.filter_btn = QPushButton("🔍")
        self.filter_btn.setFixedSize(40, 40)
        self.filter_btn.setCursor(Qt.PointingHandCursor)
        self.filter_btn.clicked.connect(self.show_filter_menu)
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background: rgba(59, 130, 246, 0.2); 
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 10px; 
                font-size: 16px;
            }
            QPushButton:hover { 
                background: rgba(59, 130, 246, 0.3); 
            }
        """)
        search_layout.addWidget(self.filter_btn)
        header.addWidget(search_container)
        
        main_layout.addLayout(header)

        # ========== GRID ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { 
                background: rgba(30, 41, 59, 0.3); 
                width: 6px; 
                border-radius: 3px; 
            }
            QScrollBar::handle:vertical { 
                background: rgba(96, 165, 250, 0.5); 
                border-radius: 3px; 
                min-height: 20px; 
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
                height: 0px; 
            }
        """)
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("QWidget { background: transparent; }")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        
        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll)

    def show_filter_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background: rgba(30, 41, 59, 0.95); 
                border: 1px solid rgba(71, 85, 105, 0.5); 
                border-radius: 10px; 
                padding: 6px; 
            }
            QMenu::item { 
                padding: 8px 16px; 
                border-radius: 6px; 
                color: white; 
                font-size: 13px; 
            }
            QMenu::item:selected { 
                background: rgba(59, 130, 246, 0.3); 
            }
        """)
        
        filters = [
            ("📋 Tous", 'all'),
            ("🔒 Forts", 'strong'),
            ("⚠️ Moyens", 'medium'),
            ("💔 Faibles", 'weak'),
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
        """Load passwords in 2-column grid"""
        self.passwords = passwords
        self.filtered_passwords = passwords[:]

        # Clear grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        # Empty state
        if not passwords:
            from gui.styles.styles import Styles
            
            empty_frame = QFrame()
            empty_frame.setStyleSheet("background: transparent; border: none;")
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(0, 60, 0, 60)
            empty_layout.setSpacing(16)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            empty_icon = QLabel("🔐")
            empty_icon.setStyleSheet("font-size: 64px; background: transparent;")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_icon)
            
            empty_text = QLabel("Aucun mot de passe")
            empty_text.setStyleSheet("""
                color: white;
                font-size: 20px;
                font-weight: 600;
                background: transparent;
            """)
            empty_text.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_text)
            
            empty_desc = QLabel("Ajoutez votre premier mot de passe")
            empty_desc.setStyleSheet("""
                color: rgba(148, 163, 184, 0.8);
                font-size: 13px;
                background: transparent;
            """)
            empty_desc.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_desc)
            
            self.grid_layout.addWidget(empty_frame, 0, 0, 1, 2)
            return

        # Display in 2-column grid
        for i, pwd in enumerate(self.filtered_passwords):
            row = i // 2
            col = i % 2
            
            card = PasswordCard(pwd)
            card.copy_clicked.connect(self.copy_password.emit)
            card.view_clicked.connect(self.view_password.emit)
            card.edit_clicked.connect(self.edit_password.emit)
            card.delete_clicked.connect(self.delete_password.emit)
            card.favorite_clicked.connect(self.favorite_password.emit)
            
            self.grid_layout.addWidget(card, row, col)

    def on_search(self, text):
        query = text.strip().lower()
        
        if not query:
            self.apply_filter(self.current_filter)
            return
        
        filtered = [
            p for p in self.passwords
            if (query in p.get('site_name', '').lower()
                or query in p.get('username', '').lower())
        ]
        
        self.load_passwords(filtered)