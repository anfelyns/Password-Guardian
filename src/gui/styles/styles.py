class Styles:
    # Couleurs principales
    PRIMARY_BG = "#0a1628"
    SECONDARY_BG = "#1a2942"
    ACCENT_BG = "#0f1e36"

    # Couleurs d'accentuation
    BLUE_PRIMARY = "#3b82f6"
    BLUE_SECONDARY = "#60a5fa"
    PURPLE = "#8b5cf6"

    # Couleurs de texte
    TEXT_PRIMARY = "#e0e7ff"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"

    # Couleurs de force
    STRONG_COLOR = "#10b981"
    MEDIUM_COLOR = "#f59e0b"
    WEAK_COLOR = "#ef4444"

    @staticmethod
    def get_main_window_style():
        return f"""
            QMainWindow {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.PRIMARY_BG},
                    stop:0.5 {Styles.SECONDARY_BG},
                    stop:1 {Styles.ACCENT_BG}
                );
            }}
        """

    @staticmethod
    def get_sidebar_style():
        return f"""
            QFrame#sidebar {{
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }}
        """

    @staticmethod
    def get_button_style(primary=True):
        if primary:
            return f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {Styles.BLUE_PRIMARY},
                        stop:1 #2563eb
                    );
                    color: white;
                    border: none;
                    border-radius: 22px;   /* pilule */
                    padding: 12px 18px;
                    font-size: 16px;
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
                QPushButton:disabled {{
                    background-color: rgba(255,255,255,0.10);
                    color: rgba(255,255,255,0.50);
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.06);
                    color: {Styles.TEXT_SECONDARY};
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 22px;
                    padding: 10px 16px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.10);
                    color: {Styles.TEXT_PRIMARY};
                }}
                QPushButton:disabled {{
                    color: rgba(255,255,255,0.45);
                    border-color: rgba(255,255,255,0.08);
                }}
            """

    @staticmethod
    def get_input_style():
        return f"""
        QLineEdit, QComboBox {{
            background-color: rgba(255,255,255,0.06);
            border: 1px solid rgba(96,165,250,0.35);
            border-radius: 22px;
            padding: 10px 14px;
            color: {Styles.TEXT_PRIMARY};
            selection-background-color: {Styles.BLUE_PRIMARY};
            selection-color: #0a1628;
            font-size: 14px;
        }}
        QLineEdit::placeholder {{ color: {Styles.TEXT_MUTED}; }}
        QLineEdit[readonly="true"] {{
            background-color: rgba(255,255,255,0.06); /* garder le même look */
            color: {Styles.TEXT_PRIMARY};
        }}
        QComboBox::drop-down {{ width: 0px; border: none; }}
        QComboBox::down-arrow {{ image: none; width:0; height:0; }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {Styles.BLUE_SECONDARY};
            outline: none;
        }}
        """

    @staticmethod
    def get_label_style(size=14, color=None):
        if color is None:
            color = Styles.TEXT_PRIMARY
        return f"""
            QLabel {{
                color: {color};
                font-size: {size}px;
                background: transparent;
            }}
        """
