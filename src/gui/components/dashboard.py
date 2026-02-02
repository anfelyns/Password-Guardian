# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QSizePolicy, QGraphicsDropShadowEffect, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from src.gui.styles.styles import Styles


class SecurityDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setStyleSheet("QWidget { background: transparent; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea::viewport { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.03);
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(96, 165, 250, 0.35);
                border-radius: 4px;
                min-height: 18px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(96, 165, 250, 0.5); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(22)

        title = QLabel("Tableau de securite")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet(Styles.get_section_title_style() + " font-size:28px;")
        root.addWidget(title)

        subtitle = QLabel("Vue d'ensemble de votre hygiene de mots de passe")
        subtitle.setStyleSheet(f"{Styles.get_muted_text_style()} font-size:14px;")
        root.addWidget(subtitle)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self.card_weak = self._card("Faibles", Styles.WEAK_COLOR)
        self.card_medium = self._card("Moyens", Styles.MEDIUM_COLOR)
        self.card_strong = self._card("Forts", Styles.STRONG_COLOR)
        self.card_reused = self._card("Reutilises", Styles.BLUE_SECONDARY)
        self.card_pwned = self._card("Pwned", Styles.PURPLE)
        self.card_old = self._card("Anciens 90j+", Styles.TEXT_MUTED)

        for c in [self.card_weak, self.card_medium, self.card_strong]:
            stats_row.addWidget(c)
        root.addLayout(stats_row)

        stats_row2 = QHBoxLayout()
        stats_row2.setSpacing(16)
        for c in [self.card_reused, self.card_pwned, self.card_old]:
            stats_row2.addWidget(c)
        root.addLayout(stats_row2)

        # Strength mix bar
        mix = QFrame()
        mix.setStyleSheet("""
            QFrame {
                background: rgba(18, 32, 54, 0.92);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
            }
        """)
        self._elevate(mix)
        mix_l = QVBoxLayout(mix)
        mix_l.setContentsMargins(18, 16, 18, 16)
        mix_l.setSpacing(10)

        mix_title = QLabel("Repartition (Faible / Moyen / Fort)")
        mix_title.setStyleSheet(Styles.get_muted_text_style())
        mix_l.addWidget(mix_title)

        self.mix_bar = QFrame()
        self.mix_bar.setFixedHeight(16)
        self.mix_bar.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
            }
        """)
        mix_row = QHBoxLayout(self.mix_bar)
        mix_row.setContentsMargins(2, 2, 2, 2)
        mix_row.setSpacing(2)

        self.seg_weak = QFrame()
        self.seg_medium = QFrame()
        self.seg_strong = QFrame()
        for seg, color in [
            (self.seg_weak, Styles.WEAK_COLOR),
            (self.seg_medium, Styles.MEDIUM_COLOR),
            (self.seg_strong, Styles.STRONG_COLOR),
        ]:
            seg.setStyleSheet(f"QFrame {{ background:{color}; border-radius:4px; }}")
            seg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            mix_row.addWidget(seg)

        mix_l.addWidget(self.mix_bar)
        root.addWidget(mix)

        # Risk detail bars
        risk = QFrame()
        risk.setStyleSheet("""
            QFrame {
                background: rgba(18, 32, 54, 0.92);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
            }
        """)
        self._elevate(risk)
        rl = QVBoxLayout(risk)
        rl.setContentsMargins(18, 16, 18, 16)
        rl.setSpacing(10)

        risk_title = QLabel("Indicateurs de risque")
        risk_title.setStyleSheet(Styles.get_muted_text_style())
        rl.addWidget(risk_title)

        self.bar_reused = self._risk_row(rl, "Reutilises", Styles.BLUE_SECONDARY)
        self.bar_pwned = self._risk_row(rl, "Pwned", Styles.PURPLE)
        self.bar_old = self._risk_row(rl, "Anciens 90j+", Styles.TEXT_MUTED)

        root.addWidget(risk)

        # Score bar
        chart = QFrame()
        chart.setStyleSheet("""
            QFrame {
                background: rgba(18, 32, 54, 0.92);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
            }
        """)
        self._elevate(chart)
        cl = QVBoxLayout(chart)
        cl.setContentsMargins(18, 18, 18, 18)
        cl.setSpacing(8)

        self.bar_strength = QProgressBar()
        self.bar_strength.setRange(0, 100)
        self.bar_strength.setValue(0)
        self.bar_strength.setTextVisible(False)
        self.bar_strength.setFixedHeight(12)
        self.bar_strength.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 5px;
                background: rgba(255,255,255,0.05);
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444, stop:0.5 #f59e0b, stop:1 #10b981);
            }
        """)
        score_label = QLabel("Score global")
        score_label.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:13px;")
        cl.addWidget(score_label)
        cl.addWidget(self.bar_strength)

        root.addWidget(chart)
        root.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _card(self, title: str, color: str):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(18, 32, 54, 0.92);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 18px;
            }
        """)
        card.setMinimumHeight(90)
        self._elevate(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px;")
        lay.addWidget(t)

        val = QLabel("0")
        val.setObjectName("value")
        val.setStyleSheet(f"color:{color}; font-size:30px; font-weight:800;")
        lay.addWidget(val)
        return card

    def _risk_row(self, layout: QVBoxLayout, label: str, color: str) -> QProgressBar:
        wrap = QFrame()
        wrap.setStyleSheet("QFrame { background: transparent; }")
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px;")
        row.addWidget(lbl)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(12)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
                background: rgba(255,255,255,0.05);
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background: {color};
            }}
        """)
        row.addWidget(bar, 1)
        layout.addWidget(wrap)
        return bar

    def _elevate(self, widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 140))
        widget.setGraphicsEffect(shadow)

    def _set_card_value(self, card: QFrame, value: int):
        lbl = card.findChild(QLabel, "value")
        if lbl:
            lbl.setText(str(value))

    def update_stats(self, data: dict):
        weak = int(data.get("weak", 0))
        medium = int(data.get("medium", 0))
        strong = int(data.get("strong", 0))
        reused = int(data.get("reused", 0))
        pwned = int(data.get("pwned", 0))
        old = int(data.get("old", 0))
        total = max(weak + medium + strong, 1)

        self._set_card_value(self.card_weak, weak)
        self._set_card_value(self.card_medium, medium)
        self._set_card_value(self.card_strong, strong)
        self._set_card_value(self.card_reused, reused)
        self._set_card_value(self.card_pwned, pwned)
        self._set_card_value(self.card_old, old)
        self.bar_strength.setValue(int(data.get("score", 0)))

        # Mix bar: use stretch factors
        mix_total = max(weak + medium + strong, 1)
        self.mix_bar.layout().setStretch(0, max(1, weak))
        self.mix_bar.layout().setStretch(1, max(1, medium))
        self.mix_bar.layout().setStretch(2, max(1, strong))

        # Risk bars relative to total
        self.bar_reused.setValue(int((reused / total) * 100))
        self.bar_pwned.setValue(int((pwned / total) * 100))
        self.bar_old.setValue(int((old / total) * 100))
