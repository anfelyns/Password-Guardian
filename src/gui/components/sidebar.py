# -*- coding: utf-8 -*-
"""
Sidebar (pro UI)

Upgrades:
- Consistent spacing + sections
- Donut stats (Fort/Moyen/Faible) like modern password managers
- Security score bar + label (accent fixed)
- Better quick actions (icons + tooltips)
- Clean scrollbar + hover/checked states
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QProgressBar,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from src.gui.styles.styles import Styles


class StatCircle(QWidget):
    """Circular donut progress indicator with percentage + label."""

    def __init__(self, percentage: int, color: str, label: str, parent=None):
        super().__init__(parent)
        self._percentage = int(max(0, min(100, percentage)))
        self._color = color
        self._label = label
        self.setFixedSize(90, 105)

    def set_percentage(self, p: int):
        p = int(max(0, min(100, p)))
        if p != self._percentage:
            self._percentage = p
            self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background circle
        bg = QColor(255, 255, 255, 18)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawEllipse(14, 6, 62, 62)

        # Arc (donut gauge)
        if self._percentage > 0:
            # Draw pie slice
            painter.setBrush(QColor(self._color))
            angle = int(360 * (self._percentage / 100.0))
            painter.drawPie(14, 6, 62, 62, 90 * 16, -angle * 16)  # clockwise

            # Inner cutout (donut)
            painter.setBrush(QColor(26, 41, 66))
            painter.drawEllipse(24, 16, 42, 42)

        # Percentage text
        painter.setPen(QColor(self._color))
        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
        painter.drawText(14, 6, 62, 62, Qt.AlignCenter, f"{self._percentage}%")

        # Label
        painter.setPen(QColor(148, 163, 184))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(0, 74, 90, 22, Qt.AlignCenter, self._label)


class CategoryButton(QPushButton):
    """Category item with (optional) count; uses checked state for selection."""

    def __init__(self, icon: str, text: str, count: int = 0, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.label_text = text
        self.count = int(count or 0)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setStyleSheet(self._style())
        self._apply_text()

    def _apply_text(self):
        if self.count > 0:
            self.setText(f"{self.icon_text}  {self.label_text}  ({self.count})")
        else:
            self.setText(f"{self.icon_text}  {self.label_text}")

    def set_count(self, c: int):
        self.count = int(c or 0)
        self._apply_text()

    @staticmethod
    def _style():
        return f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.03);
                color: {Styles.TEXT_SECONDARY};
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 10px 14px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.14);
                border: 1px solid rgba(59, 130, 246, 0.20);
                color: {Styles.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: rgba(59, 130, 246, 0.22);
                border: 1px solid rgba(96, 165, 250, 0.35);
                color: {Styles.BLUE_SECONDARY};
                font-weight: 600;
            }}
        """


class Sidebar(QFrame):
    """Left sidebar: Add, Stats, Categories, Quick Actions."""

    category_changed = pyqtSignal(str)
    add_password_clicked = pyqtSignal()

    show_statistics_clicked = pyqtSignal()
    show_profile_clicked = pyqtSignal()
    show_devices_clicked = pyqtSignal()
    lock_now_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(390)
        self._init_ui()

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {Styles.TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
        return lbl

    def _divider(self) -> QFrame:
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet("background: rgba(255,255,255,0.06); border: none;")
        return d

    def _quick_btn(self, text: str, icon: str, tooltip: str) -> QPushButton:
        b = QPushButton(f"{icon}  {text}")
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedHeight(40)
        b.setToolTip(tooltip)
        b.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.03);
                color: {Styles.TEXT_SECONDARY};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 9px 12px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.14);
                border: 1px solid rgba(59, 130, 246, 0.22);
                color: {Styles.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: rgba(59, 130, 246, 0.20);
            }}
            """
        )
        return b

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollArea::viewport { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.04);
                width: 8px;
                border-radius: 4px;
                margin: 6px 0 6px 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(59,130,246,0.6);
                border-radius: 4px;
                min-height: 22px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(59,130,246,0.85);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # === ADD BUTTON ===
        self.add_btn = QPushButton("➕  Nouveau Mot de Passe")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setFixedHeight(48)
        self.add_btn.clicked.connect(self.add_password_clicked.emit)
        self.add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 14px;
                padding: 11px 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 {Styles.BLUE_PRIMARY});
            }}
            QPushButton:pressed {{ background: #1d4ed8; }}
            """
        )
        layout.addWidget(self.add_btn)

        layout.addSpacing(4)

        # === STATISTICS ===
        layout.addWidget(self._section_title("📊 STATISTIQUES"))

        stats_card = QFrame()
        stats_card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            """
        )
        stats_l = QVBoxLayout(stats_card)
        stats_l.setContentsMargins(14, 12, 14, 14)
        stats_l.setSpacing(10)

        circles_row = QHBoxLayout()
        circles_row.setSpacing(10)
        circles_row.setContentsMargins(0, 0, 0, 0)

        self.circle_strong = StatCircle(0, Styles.STRONG_COLOR, "Forts")
        self.circle_medium = StatCircle(0, Styles.MEDIUM_COLOR, "Moyens")
        self.circle_weak = StatCircle(0, Styles.WEAK_COLOR, "Faibles")

        circles_row.addWidget(self.circle_strong)
        circles_row.addWidget(self.circle_medium)
        circles_row.addWidget(self.circle_weak)
        stats_l.addLayout(circles_row)

        self.score_label = QLabel("Score sécurité: 0%")
        self.score_label.setStyleSheet(f"color: {Styles.TEXT_MUTED}; font-size: 11px;")
        stats_l.addWidget(self.score_label)

        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setValue(0)
        self.score_bar.setTextVisible(False)
        self.score_bar.setFixedHeight(8)
        self.score_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 4px;
                background: rgba(255,255,255,0.06);
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444, stop:0.5 #f59e0b, stop:1 #10b981);
            }
            """
        )
        stats_l.addWidget(self.score_bar)
        layout.addWidget(stats_card)

        layout.addSpacing(6)

        # === CATEGORIES ===
        layout.addWidget(self._section_title("CATÉGORIES"))

        self.categories = {
            "all": CategoryButton("📋", "Tous", 0),
            "work": CategoryButton("💼", "Travail", 0),
            "personal": CategoryButton("👤", "Personnel", 0),
            "finance": CategoryButton("💳", "Finance", 0),
            "game": CategoryButton("🎮", "Jeux", 0),
            "study": CategoryButton("📚", "Étude", 0),
            "favorites": CategoryButton("⭐", "Favoris", 0),
            "trash": CategoryButton("🗑️", "Corbeille", 0),
        }

        for key, btn in self.categories.items():
            btn.clicked.connect(lambda _checked, k=key: self.on_category_click(k))
            layout.addWidget(btn)

        self.categories["all"].setChecked(True)

        layout.addSpacing(8)

        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

        self.setStyleSheet(
            """
            QFrame#sidebar {
                background-color: #0f1e36;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 20px;
            }
            """
        )

    def on_category_click(self, category: str):
        # Uncheck others
        for key, btn in self.categories.items():
            if key != category:
                btn.setChecked(False)
        self.category_changed.emit(category)

    def update_counts(self, counts: dict):
        """
        counts example:
        {
            'all': 10, 'work': 3, ...,
            'strong': 5, 'medium': 3, 'weak': 2,
            'favorites': 2, 'trash': 1
        }
        """
        for key, val in counts.items():
            if key in self.categories:
                self.categories[key].set_count(val)

        # update stats if provided
        self.update_statistics(counts.get("strong", 0), counts.get("medium", 0), counts.get("weak", 0))

    def update_statistics(self, strong: int, medium: int, weak: int):
        total = int(strong) + int(medium) + int(weak)
        if total <= 0:
            self.circle_strong.set_percentage(0)
            self.circle_medium.set_percentage(0)
            self.circle_weak.set_percentage(0)
            self.score_bar.setValue(0)
            self.score_label.setText("Score sécurité: 0%")
            return

        p_strong = int(round((strong / total) * 100))
        p_medium = int(round((medium / total) * 100))
        p_weak = max(0, 100 - p_strong - p_medium)

        self.circle_strong.set_percentage(p_strong)
        self.circle_medium.set_percentage(p_medium)
        self.circle_weak.set_percentage(p_weak)

        # Score: weight strong > medium > weak
        score = int(round(((strong * 1.0) + (medium * 0.6)) / total * 100))
        self.score_bar.setValue(score)
        self.score_label.setText(f"Score sécurité: {score}%")
