# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor
from src.gui.styles.styles import Styles


class StatCircle(QWidget):
    """Circular progress indicator for password strength"""

    def __init__(self, percentage: int, color: str, label: str, parent=None):
        super().__init__(parent)
        self.percentage = percentage
        self.color = color
        self.label = label
        self.setFixedSize(80, 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Circle background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawEllipse(10, 5, 60, 60)

        # Progress arc
        if self.percentage > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self.color))

            # Calculate arc angle (360 degrees = full circle)
            angle = int(360 * (self.percentage / 100))
            painter.drawPie(10, 5, 60, 60, 90 * 16, -angle * 16)

            # Inner circle (donut effect)
            painter.setBrush(QColor(26, 41, 66))
            painter.drawEllipse(20, 15, 40, 40)

        # Percentage text
        painter.setPen(QColor(self.color))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(10, 5, 60, 60, Qt.AlignCenter, f"{self.percentage}%")

        # Label
        painter.setPen(QColor(148, 163, 184))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(0, 70, 80, 20, Qt.AlignCenter, self.label)


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

        # Statistics data
        self.stats = {
            'strong': 0,
            'medium': 0,
            'weak': 0
        }

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # =============================================
        # 1. ADD BUTTON
        # =============================================
        self.add_btn = QPushButton("➕  Nouveau Mot de Passe")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.BLUE_PRIMARY},
                    stop:1 #2563eb
                );
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 18px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb,
                    stop:1 {Styles.BLUE_PRIMARY}
                );
            }}
            QPushButton:pressed {{ background: #1d4ed8; }}
        """)
        self.add_btn.setFixedHeight(50)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_password_clicked.emit)
        layout.addWidget(self.add_btn)

        layout.addSpacing(10)

        # =============================================
        # 2. STATISTICS SECTION (NEW!)
        # =============================================
        stats_label = QLabel("📊 STATISTIQUES")
        stats_label.setStyleSheet(f"""
            color: {Styles.TEXT_MUTED};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(stats_label)

        # Statistics container
        stats_container = QWidget()
        stats_container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 15px;
            }}
        """)

        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(5)

        # Create 3 circles
        self.circle_strong = StatCircle(0, Styles.STRONG_COLOR, "Forts")
        self.circle_medium = StatCircle(0, Styles.MEDIUM_COLOR, "Moyens")
        self.circle_weak = StatCircle(0, Styles.WEAK_COLOR, "Faibles")

        stats_layout.addWidget(self.circle_strong)
        stats_layout.addWidget(self.circle_medium)
        stats_layout.addWidget(self.circle_weak)

        layout.addWidget(stats_container)

        layout.addSpacing(10)

        # =============================================
        # 3. CATEGORIES SECTION
        # =============================================
        cat_label = QLabel("CATÉGORIES")
        cat_label.setStyleSheet(f"""
            color: {Styles.TEXT_MUTED};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(cat_label)

        # Categories with icons
        self.categories = {
            'all': CategoryButton("📋", "Tous", 0),
            'work': CategoryButton("💼", "Travail", 0),
            'personal': CategoryButton("👤", "Personnel", 0),
            'finance': CategoryButton("💳", "Finance", 0),
            'game': CategoryButton("🎮", "Jeux", 0),
            'study': CategoryButton("📚", "Étude", 0),
            'favorites': CategoryButton("⭐", "Favoris", 0),
            'trash': CategoryButton("🗑️", "Corbeille", 0)
        }

        for key, btn in self.categories.items():
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.on_category_click(k))
            layout.addWidget(btn)

        # Select "All" by default
        self.categories['all'].setChecked(True)

        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: rgba(26, 41, 66, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 0px;
            }}
        """)

    def on_category_click(self, category):
        # Uncheck other categories
        for key, btn in self.categories.items():
            if key != category:
                btn.setChecked(False)

        # Emit change signal
        self.category_changed.emit(category)

    def update_counts(self, counts):
        """
        Update category counts from dictionary
        counts = {
            'all': 10,
            'work': 3,
            'strong': 5,
            'medium': 3,
            'weak': 2,
            ...
        }
        """
        # Update category buttons
        for key, count in counts.items():
            if key in self.categories:
                btn = self.categories[key]
                btn.count = count
                btn.update_text()

        # Update statistics circles
        if 'strong' in counts or 'medium' in counts or 'weak' in counts:
            self.update_statistics(
                counts.get('strong', 0),
                counts.get('medium', 0),
                counts.get('weak', 0)
            )

    def update_statistics(self, strong: int, medium: int, weak: int):
        """Update the statistics circles with new percentages"""
        total = strong + medium + weak

        if total > 0:
            strong_pct = int((strong / total) * 100)
            medium_pct = int((medium / total) * 100)
            weak_pct = int((weak / total) * 100)
        else:
            strong_pct = medium_pct = weak_pct = 0

        # Update circles
        self.circle_strong.percentage = strong_pct
        self.circle_medium.percentage = medium_pct
        self.circle_weak.percentage = weak_pct

        # Force repaint
        self.circle_strong.update()
        self.circle_medium.update()
        self.circle_weak.update()