from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class CategoryButton(QPushButton):
    def __init__(self, icon, text, count=0, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.label_text = text
        self.count = count
        self.update_text()
        self.setStyleSheet(self.get_style())
        self.setFixedHeight(45)
        self.setCursor(Qt.PointingHandCursor)
    
    def update_text(self):
        if self.count > 0:
            self.setText(f"{self.icon_text}  {self.label_text}  ({self.count})")
        else:
            self.setText(f"{self.icon_text}  {self.label_text}")
    
    def get_style(self):
        from gui.styles.styles import Styles
        return f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.03);
                color: {Styles.TEXT_SECONDARY};
                border: none;
                border-radius: 10px;
                padding: 12px 15px;
                text-align: left;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.15);
                color: {Styles.BLUE_SECONDARY};
            }}
            QPushButton:checked {{
                background-color: rgba(59, 130, 246, 0.2);
                color: {Styles.BLUE_SECONDARY};
                font-weight: bold;
            }}
        """


class Sidebar(QFrame):
    category_changed = pyqtSignal(str)
    add_password_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(300)
        self.init_ui()
        
    def init_ui(self):
        from gui.styles.styles import Styles
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Bouton Ajouter
        self.add_btn = QPushButton("➕  Nouveau Mot de Passe")
        self.add_btn.setStyleSheet(Styles.get_button_style(primary=True))
        self.add_btn.setFixedHeight(50)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_password_clicked.emit)
        layout.addWidget(self.add_btn)
        
        layout.addSpacing(20)
        
        # Titre CATÉGORIES
        cat_label = QLabel("CATÉGORIES")
        cat_label.setStyleSheet(f"""
            color: {Styles.TEXT_MUTED};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(cat_label)

        self.categories = {
            'all': CategoryButton("📋", "Tous", 0),
            'work': CategoryButton("💼", "Travail", 0),
            'personal': CategoryButton("👤", "Personnel", 0),
            'finance': CategoryButton("💳", "Finance", 0),
            'games': CategoryButton("🎮", "Jeux", 0),
            'study': CategoryButton("📚", "Étude", 0),
            'favorites': CategoryButton("⭐", "Favoris", 0),
            'trash': CategoryButton("🗑️", "Corbeille", 0)
        }
        
        for key, btn in self.categories.items():
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.on_category_click(k))
            layout.addWidget(btn)
        
        self.categories['all'].setChecked(True)
        
        layout.addStretch()
        self.setLayout(layout)
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
            }}
        """)
    
    def on_category_click(self, category):
        for key, btn in self.categories.items():
            if key != category:
                btn.setChecked(False)
        
        self.category_changed.emit(category)
    
    def update_counts(self, counts):
        for key, count in counts.items():
            if key in self.categories:
                btn = self.categories[key]
                btn.count = count
                btn.update_text()