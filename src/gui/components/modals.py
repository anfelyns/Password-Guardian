# ==========================================================
# SecureVault - GUI Modals (Fixed Version)
# ==========================================================

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QCheckBox, QComboBox, QWidget, QFrame, QMessageBox,
    QApplication, QProgressBar, QSizePolicy, QTextEdit
)

from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont
import random, string, re
from datetime import datetime
from src.gui.styles.styles import Styles
import webbrowser


# ==================== HELPER FUNCTIONS ====================

def style_line_edit(line_edit):
    """Apply consistent styling to QLineEdit widgets"""
    line_edit.setMinimumHeight(48)
    line_edit.setFont(QFont("Segoe UI", 12))
    line_edit.setStyleSheet(Styles.get_input_style())


class PasswordStrengthChecker:
    """Password strength checking utilities"""
    
    @staticmethod
    def check_strength(password):
        """Check password strength - Returns: (strength_level, score, feedback)"""
        if not password:
            return "weak", 0, ["Password is empty"]
        
        score = 0
        feedback = []
        
        # Length check
        length = len(password)
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        else:
            feedback.append("Utilisez au moins 8 caractères")
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Ajoutez des minuscules")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Ajoutez des majuscules")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Ajoutez des chiffres")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Ajoutez des caractères spéciaux")
        
        # Determine strength level
        if score >= 5:
            return "strong", score, ["Mot de passe fort !"]
        elif score >= 3:
            return "medium", score, feedback or ["Bon mot de passe"]
        else:
            return "weak", score, feedback or ["Mot de passe faible"]
    
    @staticmethod
    def generate_strong_password(length=16):
        """Generate a strong random password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        return password


class PasswordStrengthWidget(QWidget):
    """Visual password strength indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(6)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 4px;
                background: rgba(255,255,255,0.05);
            }
            QProgressBar::chunk {
                border-radius: 3px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444, stop:0.5 #f59e0b, stop:1 #10b981);
            }
        """)
        layout.addWidget(self.progress)
        
        # Status label
        self.label = QLabel("Entrez un mot de passe")
        self.label.setStyleSheet(f"color: {Styles.TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(self.label)
    
    def update_strength(self, password):
        """Update strength indicator based on password"""
        strength, score, feedback = PasswordStrengthChecker.check_strength(password)
        
        self.progress.setValue(score)
        
        colors = {
            'weak': Styles.WEAK_COLOR,
            'medium': Styles.MEDIUM_COLOR,
            'strong': Styles.STRONG_COLOR
        }
        
        color = colors.get(strength, Styles.TEXT_MUTED)
        
        if not password:
            self.label.setText("Entrez un mot de passe")
            self.label.setStyleSheet(f"color: {Styles.TEXT_MUTED}; font-size: 12px; background: transparent;")
        else:
            self.label.setText(f"{strength.capitalize()}: {', '.join(feedback)}")
            self.label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; background: transparent;")


class AnimatedButton(QPushButton):
    """Button with hover animation"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)


# ==================== LOGIN MODAL ====================

class LoginModal(QDialog):
    login_success = pyqtSignal(str, str)
    switch_to_register = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Connexion")
        self.setFixedSize(450, 570)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(22)

        head = QVBoxLayout()
        head.setSpacing(12)
        head.setAlignment(Qt.AlignCenter)
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:46px; background: transparent;")
        title = QLabel("Connexion")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(24))
        sub = QLabel("Accédez à votre coffre-fort sécurisé")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        head.addWidget(icon)
        head.addWidget(title)
        head.addWidget(sub)
        layout.addLayout(head)

        form = QVBoxLayout()
        form.setSpacing(18)

        # Email
        lbl = QLabel("📧 Adresse e-mail")
        lbl.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        form.addWidget(lbl)
        
        self.email_input = QLineEdit()
        style_line_edit(self.email_input)
        self.email_input.setPlaceholderText("votre@email.com")
        form.addWidget(self.email_input)
        form.addSpacing(6)

        # Password
        lbl2 = QLabel("🔒 Mot de passe")
        lbl2.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        form.addWidget(lbl2)
        
        row = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        style_line_edit(self.password_input)
        self.password_input.setPlaceholderText("Entrez votre mot de passe")
        self.toggle_pwd_btn = QPushButton("👁️")
        self.toggle_pwd_btn.setFixedSize(40, 40)
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:8px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_pwd_btn.toggled.connect(
            lambda c: self.password_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password)
        )
        row.addWidget(self.password_input)
        row.addWidget(self.toggle_pwd_btn)
        form.addLayout(row)

        # Error message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold; background: transparent;")
        self.error_label.setWordWrap(True)
        form.addWidget(self.error_label)

        layout.addLayout(form)

        login_btn = AnimatedButton("🚀 Se connecter")
        login_btn.setStyleSheet(Styles.get_button_style(primary=True))
        login_btn.setMinimumHeight(50)
        login_btn.clicked.connect(self.on_login)
        layout.addWidget(login_btn)

        # Forgot password
        forgot_layout = QHBoxLayout()
        forgot_layout.setAlignment(Qt.AlignCenter)
        forgot_text = QLabel("Mot de passe oublié?")
        forgot_text.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_MUTED))
        forgot_link = QLabel("<a href='#' style='color:#60a5fa; text-decoration:none; font-weight:bold;'>Réinitialiser</a>")
        forgot_link.setOpenExternalLinks(False)
        forgot_link.linkActivated.connect(self.show_forgot_password)
        forgot_layout.addWidget(forgot_text)
        forgot_layout.addWidget(forgot_link)
        layout.addLayout(forgot_layout)

        # Register link
        footer = QHBoxLayout()
        footer.setAlignment(Qt.AlignCenter)
        t = QLabel("Nouveau chez SecureVault?")
        t.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_MUTED))
        link = QLabel("<a href='#' style='color:#60a5fa; text-decoration:none; font-weight:bold;'>Créer un compte</a>")
        link.setOpenExternalLinks(False)
        link.linkActivated.connect(lambda: self.switch_to_register.emit())
        footer.addWidget(t)
        footer.addWidget(link)
        layout.addLayout(footer)

    def on_login(self):
        email = self.email_input.text().strip()
        pwd = self.password_input.text()
        
        self.error_label.setText("")
        
        if not email:
            self.error_label.setText("❌ Veuillez saisir votre adresse email")
            return
        if not pwd:
            self.error_label.setText("❌ Veuillez saisir votre mot de passe")
            return
        if '@' not in email or '.' not in email:
            self.error_label.setText("❌ Adresse email invalide")
            return
        
        self.login_success.emit(email, pwd)
        self.accept()

    def show_forgot_password(self):
        """Open forgot password dialog"""
        from src.auth.auth_manager import AuthManager
        
        auth = AuthManager(
            host='localhost',
            user='root',
            password='inessouai2005_',
            database='password_guardian',
            port=3306
        )
        
        dlg = ForgotPasswordDialog(auth, parent=self)
        result = dlg.exec_()
        
        if result == QDialog.Accepted:
            self.email_input.clear()
            self.password_input.clear()
            self.error_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: bold; background: transparent;")
            self.error_label.setText("✅ Mot de passe réinitialisé. Connectez-vous avec votre nouveau mot de passe.")


# ==================== REGISTER MODAL ====================

class RegisterModal(QDialog):
    register_success = pyqtSignal(str, str, str)
    switch_to_login = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Inscription")
        self.setFixedSize(500, 750)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        head = QVBoxLayout()
        head.setAlignment(Qt.AlignCenter)
        head.setSpacing(10)
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size:46px; background: transparent;")
        title = QLabel("Créer un compte")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(24))
        sub = QLabel("Rejoignez la communauté SecureVault")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        head.addWidget(icon)
        head.addWidget(title)
        head.addWidget(sub)
        layout.addLayout(head)

        form = QVBoxLayout()
        form.setSpacing(18)

        # Name
        nlab = QLabel("👤 Nom complet")
        nlab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        self.name_input = QLineEdit()
        style_line_edit(self.name_input)
        self.name_input.setPlaceholderText("Entrez votre nom complet")
        form.addWidget(nlab)
        form.addWidget(self.name_input)
        form.addSpacing(6)

        # Email
        elab = QLabel("📧 Adresse e-mail")
        elab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        self.email_input = QLineEdit()
        style_line_edit(self.email_input)
        self.email_input.setPlaceholderText("votre@email.com")
        form.addWidget(elab)
        form.addWidget(self.email_input)
        form.addSpacing(6)

        # Password
        plab = QLabel("🔒 Mot de passe maître")
        plab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        form.addWidget(plab)
        
        prow = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        style_line_edit(self.password_input)
        self.password_input.setPlaceholderText("Créez un mot de passe fort")
        self.toggle_pwd_btn = QPushButton("👁️")
        self.toggle_pwd_btn.setFixedSize(40, 40)
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:8px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_pwd_btn.toggled.connect(lambda c: (
            self.password_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password),
            self.confirm_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password)
        ))
        prow.addWidget(self.password_input)
        prow.addWidget(self.toggle_pwd_btn)
        form.addLayout(prow)

        self.strength_widget = PasswordStrengthWidget()
        self.password_input.textChanged.connect(self.on_password_changed)
        form.addWidget(self.strength_widget)
        
        # Weak password warning
        self.weak_password_container = QFrame()
        self.weak_password_container.setVisible(False)
        self.weak_password_container.setStyleSheet("""
            QFrame {
                background-color: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        weak_layout = QVBoxLayout(self.weak_password_container)
        weak_layout.setContentsMargins(8, 8, 8, 8)
        weak_layout.setSpacing(8)
        
        weak_label = QLabel("⚠️ Mot de passe faible détecté")
        weak_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px; background: transparent;")
        weak_layout.addWidget(weak_label)
        
        weak_btn_layout = QHBoxLayout()
        self.generate_strong_btn = AnimatedButton("🎲 Générer un mot de passe fort")
        self.generate_strong_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Styles.STRONG_COLOR}, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 {Styles.STRONG_COLOR});
            }}
        """)
        self.generate_strong_btn.clicked.connect(self.generate_strong_password)
        weak_btn_layout.addWidget(self.generate_strong_btn)
        weak_btn_layout.addStretch()
        weak_layout.addLayout(weak_btn_layout)
        
        form.addWidget(self.weak_password_container)
        form.addSpacing(6)

        # Confirm password
        clab = QLabel("✅ Confirmer le mot de passe")
        clab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal; background: transparent;")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        style_line_edit(self.confirm_input)
        self.confirm_input.setPlaceholderText("Confirmez votre mot de passe")
        form.addWidget(clab)
        form.addWidget(self.confirm_input)

        layout.addLayout(form)

        btn = AnimatedButton("🎉 Créer mon compte")
        btn.setStyleSheet(Styles.get_button_style(primary=True))
        btn.setMinimumHeight(50)
        btn.clicked.connect(self.on_register)
        layout.addWidget(btn)

        foot = QHBoxLayout()
        foot.setAlignment(Qt.AlignCenter)
        t = QLabel("Déjà un compte?")
        t.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_MUTED))
        link = QLabel("<a href='#' style='color:#60a5fa; text-decoration:none; font-weight:bold;'>Se connecter</a>")
        link.setOpenExternalLinks(False)
        link.linkActivated.connect(lambda: self.switch_to_login.emit())
        foot.addWidget(t)
        foot.addWidget(link)
        layout.addLayout(foot)

    def on_password_changed(self, password):
        """Called when password text changes"""
        self.strength_widget.update_strength(password)
        
        if password:
            strength, _, _ = PasswordStrengthChecker.check_strength(password)
            self.weak_password_container.setVisible(strength == "weak")
        else:
            self.weak_password_container.setVisible(False)
    
    def generate_strong_password(self):
        """Generate a strong password and fill it in"""
        strong_pwd = PasswordStrengthChecker.generate_strong_password(16)
        self.password_input.setText(strong_pwd)
        self.confirm_input.setText(strong_pwd)
        
        self.toggle_pwd_btn.setChecked(True)
        
        QMessageBox.information(
            self, 
            "Mot de passe généré", 
            f"Un mot de passe fort a été généré :\n\n{strong_pwd}\n\n"
            "💡 Conseil : Copiez-le et conservez-le dans un endroit sûr !"
        )

    def on_register(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        pwd = self.password_input.text()
        cpwd = self.confirm_input.text()
        if not name:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir votre nom complet")
            return
        if not email:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir votre adresse e-mail")
            return
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Erreur", "Adresse e-mail invalide")
            return
        if not pwd:
            QMessageBox.warning(self, "Erreur", "Veuillez créer un mot de passe maître")
            return
        if pwd != cpwd:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas")
            return
        
        strength, _, _ = PasswordStrengthChecker.check_strength(pwd)
        if strength == "weak":
            reply = QMessageBox.question(
                self, 
                "⚠️ Mot de passe faible",
                "Votre mot de passe est faible et pourrait être facilement deviné.\n\n"
                "Voulez-vous :\n"
                "• Générer un mot de passe fort automatiquement ?\n"
                "• Ou continuer avec ce mot de passe faible ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.generate_strong_password()
                return
        
        self.register_success.emit(name, email, pwd)
        self.accept()


# ==================== ADD PASSWORD MODAL (SANS "Nom du site") ====================

class AddPasswordModal(QDialog):
    password_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un mot de passe")
        self.setFixedSize(550, 680)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        # Header
        head = QHBoxLayout()
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:30px; background: transparent;")
        title = QLabel("Nouveau Mot de Passe")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY}; background:transparent;")
        head.addWidget(icon)
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        form = QVBoxLayout()
        form.setSpacing(12)

        # Website URL
        lab_url = QLabel("🌐 URL du site web")
        lab_url.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px; background:transparent;")
        self.url_input = QLineEdit()
        self.url_input.setMinimumHeight(48)
        self.url_input.setFont(QFont("Segoe UI", 12))
        self.url_input.setStyleSheet(Styles.get_input_style())
        self.url_input.setPlaceholderText("https://example.com/login")
        form.addWidget(lab_url)
        
        url_row = QHBoxLayout()
        url_row.addWidget(self.url_input)
        
        # Open URL button
        self.open_url_btn = QPushButton("🔗")
        self.open_url_btn.setFixedSize(48, 48)
        self.open_url_btn.setToolTip("Ouvrir le site dans le navigateur")
        self.open_url_btn.setCursor(Qt.PointingHandCursor)
        self.open_url_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(59, 130, 246, 0.15);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 10px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid rgba(59, 130, 246, 0.5);
            }}
        """)
        self.open_url_btn.clicked.connect(self.open_website)
        url_row.addWidget(self.open_url_btn)
        form.addLayout(url_row)

        # Email/Username
        lab2 = QLabel("📧 Email / Identifiant")
        lab2.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px; background:transparent;")
        self.email_input = QLineEdit()
        self.email_input.setMinimumHeight(48)
        self.email_input.setFont(QFont("Segoe UI", 12))
        self.email_input.setStyleSheet(Styles.get_input_style())
        self.email_input.setPlaceholderText("votre@email.com ou nom d'utilisateur")
        form.addWidget(lab2)
        form.addWidget(self.email_input)

        # Password
        lab3 = QLabel("🔒 Mot de passe")
        lab3.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px; background:transparent;")
        row = QHBoxLayout()
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setMinimumHeight(48)
        self.pwd_input.setFont(QFont("Segoe UI", 12))
        self.pwd_input.setStyleSheet(Styles.get_input_style())
        self.pwd_input.setPlaceholderText("Saisissez ou générez un mot de passe")
        self.toggle_pwd_btn = QPushButton("👁️")
        self.toggle_pwd_btn.setFixedSize(48, 48)
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:10px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_pwd_btn.toggled.connect(
            lambda c: self.pwd_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password)
        )
        row.addWidget(self.pwd_input)
        row.addWidget(self.toggle_pwd_btn)
        form.addWidget(lab3)
        form.addLayout(row)

        # Generate password section
        gen = QHBoxLayout()
        self.generate_checkbox = QCheckBox("🎲 Générer un mot de passe sécurisé")
        self.generate_checkbox.setStyleSheet(f"color:{Styles.TEXT_PRIMARY}; font-size:14px; background:transparent;")
        self.generate_checkbox.toggled.connect(self.toggle_password_generation)
        gen.addWidget(self.generate_checkbox)

        self.generate_btn = QPushButton("Générer")
        self.generate_btn.setVisible(False)
        self.generate_btn.setMinimumHeight(36)
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.generate_password)
        self.generate_btn.setStyleSheet(Styles.get_button_style(primary=False))
        gen.addWidget(self.generate_btn)
        gen.addStretch()
        form.addLayout(gen)

        self.strength_widget = PasswordStrengthWidget()
        self.pwd_input.textChanged.connect(self.strength_widget.update_strength)
        form.addWidget(self.strength_widget)
        form.addSpacing(8)

        # Category
        cl = QLabel("📁 Catégorie")
        cl.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px; background:transparent;")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["👤 Personnel", "💼 Travail", "💳 Finance", "🎮 Jeux", "📚 Étude", "📂 Autre"])
        self.category_combo.setMinimumHeight(48)
        self.category_combo.setFont(QFont("Segoe UI", 12))
        self.category_combo.setStyleSheet(Styles.get_input_style())
        form.addWidget(cl)
        form.addWidget(self.category_combo)

        layout.addLayout(form)
        layout.addSpacing(10)

        # Auto-fill instructions
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 8, 8, 8)
        
        info_title = QLabel("💡 Remplissage automatique")
        info_title.setStyleSheet(f"color:{Styles.BLUE_SECONDARY}; font-size:13px; font-weight:bold; background:transparent;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "Après avoir enregistré ce mot de passe, utilisez le bouton 🔗 "
            "pour ouvrir le site et remplir automatiquement vos identifiants."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:11px; background:transparent;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(12)
        cancel = QPushButton("❌ Annuler")
        cancel.setStyleSheet(Styles.get_button_style(primary=False))
        cancel.setMinimumHeight(48)
        cancel.setCursor(Qt.PointingHandCursor)
        save = QPushButton("💾 Enregistrer le mot de passe")
        save.setStyleSheet(Styles.get_button_style(primary=True))
        save.setMinimumHeight(48)
        save.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.on_save)
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def toggle_password_generation(self, checked):
        self.generate_btn.setVisible(checked)
        if checked:
            self.pwd_input.clear()
            self.pwd_input.setReadOnly(True)
            self.pwd_input.setProperty("readonly", True)
            self.pwd_input.style().unpolish(self.pwd_input)
            self.pwd_input.style().polish(self.pwd_input)
            self.generate_password()
        else:
            self.pwd_input.setReadOnly(False)
            self.pwd_input.setProperty("readonly", False)
            self.pwd_input.style().unpolish(self.pwd_input)
            self.pwd_input.style().polish(self.pwd_input)

    def generate_password(self):
        """Generate a strong 16-character password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = ''.join(random.choice(chars) for _ in range(16))
        self.pwd_input.setText(pwd)
        self.strength_widget.update_strength(pwd)

    def open_website(self):
        """Open the website URL in default browser"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "URL manquante", "Veuillez saisir l'URL du site web.")
            return
        
        # Add https:// if no protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            webbrowser.open(url)
            QMessageBox.information(
                self, 
                "Site ouvert", 
                "✅ Le site a été ouvert dans votre navigateur.\n\n"
                "Astuce: Après l'enregistrement, vous pourrez utiliser "
                "le bouton 🔗 sur chaque carte pour ouvrir et remplir automatiquement."
            )
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir l'URL: {str(e)}")

    def on_save(self):
        """Save password - Extract site name from URL automatically"""
        url = self.url_input.text().strip()
        user = self.email_input.text().strip()
        pwd = self.pwd_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir l'URL du site web")
            return
        if not user:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un email/identifiant")
            return
        if not pwd:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un mot de passe")
            return
        
        # Extract site name from URL
        site_name = url
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url if url.startswith(('http://', 'https://')) else f'https://{url}')
            domain = parsed.netloc or parsed.path
            # Remove www. and extract main domain
            if domain.startswith('www.'):
                domain = domain[4:]
            # Take first part before first dot as site name
            site_name = domain.split('.')[0].capitalize() if domain else url
        except:
            site_name = url.split('/')[0].split('.')[0].capitalize()
        
        category_map = {
            "👤 Personnel": "personal",
            "💼 Travail": "work",
            "💳 Finance": "finance",
            "🎮 Jeux": "game",
            "📚 Étude": "study",
            "📂 Autre": "personal"
        }
        
        display_cat = self.category_combo.currentText()
        category = category_map.get(display_cat, "personal")
        
        self.password_added.emit({
            'site_name': site_name,
            'site_url': url,
            'username': user,
            'password': pwd,
            'category': category
        })
        self.accept()


# ==================== VIEW PASSWORD MODAL ====================

class ViewPasswordModal(QDialog):
    def __init__(self, password_data, api_client=None, parent=None):
        super().__init__(parent)
        self.password_data = password_data or {}
        self.api_client = api_client
        self.setWindowTitle(f"Mot de passe - {self.password_data.get('site_name','')}")
        self.setFixedSize(480, 380)
        self.setModal(True)
        self._decrypted_pwd = None
        self._is_visible = True
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); 
                border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Header
        head = QHBoxLayout()
        icon = QLabel(self.password_data.get('site_icon', '🔒'))
        icon.setStyleSheet("font-size:36px; background: transparent;")
        title = QLabel(self.password_data.get('site_name', 'Compte'))
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(20))
        head.addWidget(icon)
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        # Info section
        info = QVBoxLayout()
        info.setSpacing(18)

        # Username
        username_section = QVBoxLayout()
        username_section.setSpacing(6)
        lbl_id = QLabel("📧 Identifiant / Email")
        lbl_id.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED) + "; background: transparent;")

        val_id = QLabel(self.password_data.get('username', ''))
        val_id.setStyleSheet(f"""
            color: {Styles.TEXT_PRIMARY};
            font-size: 14px;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 12px 14px;
        """)
        val_id.setTextInteractionFlags(Qt.TextSelectableByMouse)
        username_section.addWidget(lbl_id)
        username_section.addWidget(val_id)
        info.addLayout(username_section)

        # Password
        password_section = QVBoxLayout()
        password_section.setSpacing(6)

        lbl_pwd = QLabel("🔒 Mot de passe")
        lbl_pwd.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED) + "; background: transparent;")

        pwd_container = QFrame()
        pwd_container.setStyleSheet("""
            QFrame {
                background: rgba(59, 130, 246, 0.08);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 12px;
                padding: 4px;
            }
        """)
        pwd_layout = QHBoxLayout(pwd_container)
        pwd_layout.setContentsMargins(8, 8, 8, 8)
        pwd_layout.setSpacing(10)

        # Try to decrypt right away (if api_client provided)
        encrypted = self.password_data.get('encrypted_password', '') or self.password_data.get('password', '')
        decrypted = None
        if self.api_client and encrypted:
            try:
                decrypted = self.api_client.decrypt_password(encrypted)
            except Exception:
                decrypted = None

        # Fallbacks
        if decrypted:
            self._decrypted_pwd = decrypted
        else:
            self._decrypted_pwd = decrypted or (encrypted if encrypted and len(encrypted) < 128 else "Erreur de déchiffrement")

        self.val_pwd = QLabel(self._decrypted_pwd)
        self.val_pwd.setStyleSheet(f"""
            color: {Styles.TEXT_PRIMARY};
            font-size: 15px;
            font-family: 'Courier New';
            font-weight: 600;
            background: transparent;
            padding: 8px;
            letter-spacing: 1px;
        """)
        self.val_pwd.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.val_pwd.setWordWrap(True)
        pwd_layout.addWidget(self.val_pwd, 1)

        # Toggle button
        self.toggle_btn = QPushButton("👁️")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setToolTip("Masquer/Afficher")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.1);
                border: none;
                border-radius: 10px;
                font-size: 18px;
            }}
            QPushButton:checked {{
                background: rgba(59, 130, 246, 0.3);
            }}
            QPushButton:hover {{
                background: rgba(59, 130, 246, 0.4);
            }}
        """)
        self.toggle_btn.toggled.connect(self._set_visibility)
        pwd_layout.addWidget(self.toggle_btn)

        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(40, 40)
        copy_btn.setToolTip("Copier le mot de passe")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(Styles.get_button_style(primary=False))
        copy_btn.clicked.connect(self.copy_password)
        pwd_layout.addWidget(copy_btn)

        password_section.addWidget(lbl_pwd)
        password_section.addWidget(pwd_container)
        info.addLayout(password_section)

        layout.addLayout(info)

        # Metadata
        meta = QVBoxLayout()
        meta.setSpacing(10)

        if 'category' in self.password_data:
            category_icons = {
                'personal': '👤 Personnel',
                'work': '💼 Travail',
                'finance': '💳 Finance',
                'game': '🎮 Jeux',
                'study': '📚 Étude'
            }
            cat_text = category_icons.get(self.password_data['category'], f"📂 {self.password_data['category'].capitalize()}")
            cat_label = QLabel(f"Catégorie: {cat_text}")
            cat_label.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY) + "; background: transparent;")
            meta.addWidget(cat_label)

        if 'strength' in self.password_data:
            strength = self.password_data['strength']
            strength_colors = {
                'strong': (Styles.STRONG_COLOR, '✅ Fort'),
                'medium': (Styles.MEDIUM_COLOR, '⚠️ Moyen'),
                'weak': (Styles.WEAK_COLOR, '❌ Faible')
            }
            color, text = strength_colors.get(strength, (Styles.TEXT_SECONDARY, strength.capitalize()))
            strength_label = QLabel(f"Force: {text}")
            strength_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;")
            meta.addWidget(strength_label)

        if 'last_updated' in self.password_data:
            date_label = QLabel(f"🕒 Dernière modification: {self.password_data['last_updated']}")
            date_label.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED) + "; background: transparent;")
            meta.addWidget(date_label)

        layout.addLayout(meta)
        layout.addStretch()

        # Close button
        close_btn = AnimatedButton("Fermer")
        close_btn.setStyleSheet(Styles.get_button_style(True))
        close_btn.setMinimumHeight(50)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _set_visibility(self, visible: bool):
        """Show decrypted password when visible True, else show bullets"""
        self._is_visible = visible
        if visible:
            self.val_pwd.setText(self._decrypted_pwd)
        else:
            txt = self._decrypted_pwd or ""
            bullets = '•' * min(len(txt), 20) if txt else "•" * 8
            self.val_pwd.setText(bullets)

    def copy_password(self):
        """Copy decrypted password to clipboard"""
        pwd_to_copy = self._decrypted_pwd
        if not pwd_to_copy:
            pwd_to_copy = self.password_data.get('encrypted_password', '') or self.password_data.get('password', '')
        if pwd_to_copy:
            QApplication.clipboard().setText(pwd_to_copy)
            QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier!")


# ==================== EDIT PASSWORD MODAL ====================

class EditPasswordModal(QDialog):
    password_updated = pyqtSignal(int, str, str)

    def __init__(self, password_data, parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self.setWindowTitle(f"Modifier — {password_data.get('site_name','Compte')}")
        self.setFixedSize(500, 420)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel("✏️ Modifier le mot de passe")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(20))
        layout.addWidget(title)

        lbl_old = QLabel("Ancien mot de passe")
        lbl_old.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY) + "; background: transparent;")
        self.in_old = QLineEdit()
        self.in_old.setEchoMode(QLineEdit.Password)
        style_line_edit(self.in_old)
        layout.addWidget(lbl_old)
        layout.addWidget(self.in_old)

        lbl_new = QLabel("Nouveau mot de passe")
        lbl_new.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY) + "; background: transparent;")
        self.in_new = QLineEdit()
        self.in_new.setEchoMode(QLineEdit.Password)
        style_line_edit(self.in_new)
        layout.addWidget(lbl_new)
        layout.addWidget(self.in_new)

        lbl_rep = QLabel("Répéter le nouveau mot de passe")
        lbl_rep.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY) + "; background: transparent;")
        self.in_rep = QLineEdit()
        self.in_rep.setEchoMode(QLineEdit.Password)
        style_line_edit(self.in_rep)
        layout.addWidget(lbl_rep)
        layout.addWidget(self.in_rep)

        self.strength_widget = PasswordStrengthWidget()
        self.in_new.textChanged.connect(self.strength_widget.update_strength)
        layout.addWidget(self.strength_widget)
        layout.addSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(12)
        cancel = AnimatedButton("Annuler")
        cancel.setMinimumHeight(48)
        cancel.setStyleSheet(Styles.get_button_style(False))
        save = AnimatedButton("💾 Mettre à jour")
        save.setMinimumHeight(48)
        save.setStyleSheet(Styles.get_button_style(True))
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.on_save)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)

    def on_save(self):
        old, new, rep = self.in_old.text(), self.in_new.text(), self.in_rep.text()
        if not old or not new or not rep:
            QMessageBox.warning(self, "Champs manquants", "Veuillez remplir tous les champs.")
            return
        current = self.password_data.get('encrypted_password', '') or self.password_data.get('password', '')
        if old != current:
            QMessageBox.warning(self, "Ancien mot de passe", "L'ancien mot de passe est incorrect.")
            return
        if new != rep:
            QMessageBox.warning(self, "Confirmation", "La confirmation ne correspond pas.")
            return
        if PasswordStrengthChecker.check_strength(new)[0] == "weak":
            if QMessageBox.question(self, "Mot de passe faible",
                                    "Le nouveau mot de passe est faible. Continuer quand même ?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                return
        last_mod = datetime.now().strftime("Maj. %d/%m/%Y %H:%M")
        self.password_updated.emit(self.password_data['id'], new, last_mod)
        QMessageBox.information(self, "Succès", "Mot de passe mis à jour.")
        self.accept()


# ==================== 2FA MODAL ====================

class TwoFactorModal(QDialog):
    code_verified = pyqtSignal()

    def __init__(self, email, sent_code, parent=None):
        super().__init__(parent)
        self.email = email
        self.sent_code = sent_code
        self.setWindowTitle("Vérification en deux étapes")
        self.setFixedSize(400, 250)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {Styles.PRIMARY_BG};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        
        title = QLabel("📱 Code de vérification")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(20))
        layout.addWidget(title)

        info = QLabel(f"Un code à 6 chiffres a été envoyé à {self.email}")
        info.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY) + "; background: transparent;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Entrez le code reçu par email")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignCenter)
        style_line_edit(self.code_input)
        layout.addWidget(self.code_input)

        verify_btn = AnimatedButton("Vérifier")
        verify_btn.setStyleSheet(Styles.get_button_style(primary=True))
        verify_btn.setMinimumHeight(48)
        verify_btn.clicked.connect(self.on_verify_clicked)
        layout.addWidget(verify_btn)

    def on_verify_clicked(self):
        """When verify button is clicked, emit signal to parent"""
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Code manquant", "Veuillez entrer le code reçu")
            return
        if len(code) != 6:
            QMessageBox.warning(self, "Code invalide", "Le code doit contenir 6 chiffres")
            return
        
        self.code_verified.emit()


# ==================== FORGOT PASSWORD DIALOG ====================

class ForgotPasswordDialog(QDialog):
    """Multi-step forgot password: email -> code -> new password"""

    COOLDOWN = 60

    def __init__(self, auth_mgr, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mot de passe oublié")
        self.setModal(True)
        self.setFixedSize(500, 550)

        self.auth = auth_mgr
        self.remaining = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        
        self.current_step = 1
        self.email_for_reset = None

        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); 
                border-radius: 25px;
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(40, 40, 40, 40)
        v.setSpacing(20)

        # Header
        header = QVBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        header.setSpacing(10)
        
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:46px; background: transparent;")
        
        self.title_label = QLabel("Étape 1: Adresse e-mail")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.title_label.setStyleSheet(Styles.get_label_style(20))
        
        header.addWidget(icon)
        header.addWidget(self.title_label)
        v.addLayout(header)

        # Step 1: Email
        self.step1_widget = QWidget()
        s1_layout = QVBoxLayout(self.step1_widget)
        s1_layout.setSpacing(12)
        
        lbl_email = QLabel("📧 Adresse e-mail")
        lbl_email.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        
        self.email = QLineEdit()
        self.email.setMinimumHeight(48)
        self.email.setPlaceholderText("votre@email.com")
        self.email.setStyleSheet(Styles.get_input_style())
        
        self.btn_send_code = AnimatedButton("📨 Envoyer le code")
        self.btn_send_code.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_send_code.setMinimumHeight(48)
        self.btn_send_code.clicked.connect(self._send_code)
        
        s1_layout.addWidget(lbl_email)
        s1_layout.addWidget(self.email)
        s1_layout.addSpacing(10)
        s1_layout.addWidget(self.btn_send_code)
        
        v.addWidget(self.step1_widget)

        # Step 2: Code verification
        self.step2_widget = QWidget()
        self.step2_widget.setVisible(False)
        s2_layout = QVBoxLayout(self.step2_widget)
        s2_layout.setSpacing(12)
        
        lbl_code = QLabel("🔑 Code de vérification")
        lbl_code.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        
        self.code = QLineEdit()
        self.code.setMinimumHeight(48)
        self.code.setPlaceholderText("000000")
        self.code.setMaxLength(6)
        self.code.setAlignment(Qt.AlignCenter)
        self.code.setFont(QFont("Courier New", 18, QFont.Bold))
        self.code.setStyleSheet(Styles.get_input_style())
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.60); font-size: 12px; background: transparent;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.btn_verify_code = AnimatedButton("✅ Vérifier le code")
        self.btn_verify_code.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_verify_code.setMinimumHeight(48)
        self.btn_verify_code.clicked.connect(self._verify_code)
        
        s2_layout.addWidget(lbl_code)
        s2_layout.addWidget(self.code)
        s2_layout.addWidget(self.status_label)
        s2_layout.addSpacing(10)
        s2_layout.addWidget(self.btn_verify_code)
        
        v.addWidget(self.step2_widget)

        # Step 3: New password
        self.step3_widget = QWidget()
        self.step3_widget.setVisible(False)
        s3_layout = QVBoxLayout(self.step3_widget)
        s3_layout.setSpacing(12)
        
        lbl_new1 = QLabel("🔒 Nouveau mot de passe")
        lbl_new1.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        
        self.new1 = QLineEdit()
        self.new1.setMinimumHeight(48)
        self.new1.setPlaceholderText("Créez un mot de passe fort")
        self.new1.setEchoMode(QLineEdit.Password)
        self.new1.setStyleSheet(Styles.get_input_style())
        
        lbl_new2 = QLabel("✅ Confirmer le mot de passe")
        lbl_new2.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        
        self.new2 = QLineEdit()
        self.new2.setMinimumHeight(48)
        self.new2.setPlaceholderText("Confirmez votre mot de passe")
        self.new2.setEchoMode(QLineEdit.Password)
        self.new2.setStyleSheet(Styles.get_input_style())
        
        self.btn_reset_password = AnimatedButton("💾 Réinitialiser le mot de passe")
        self.btn_reset_password.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_reset_password.setMinimumHeight(48)
        self.btn_reset_password.clicked.connect(self._reset_password)
        
        s3_layout.addWidget(lbl_new1)
        s3_layout.addWidget(self.new1)
        s3_layout.addWidget(lbl_new2)
        s3_layout.addWidget(self.new2)
        s3_layout.addSpacing(10)
        s3_layout.addWidget(self.btn_reset_password)
        
        v.addWidget(self.step3_widget)

        v.addStretch()

        # Close button
        self.btn_close = AnimatedButton("Annuler")
        self.btn_close.setStyleSheet(Styles.get_button_style(primary=False))
        self.btn_close.setMinimumHeight(44)
        self.btn_close.clicked.connect(self.reject)
        v.addWidget(self.btn_close)

    def _send_code(self):
        email = self.email.text().strip()
        if not email:
            QMessageBox.warning(self, "Email manquant", "Veuillez saisir votre e-mail.")
            return
        
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Email invalide", "Veuillez saisir une adresse e-mail valide.")
            return
        
        try:
            ok = self.auth.send_reset_code(email)
            if ok:
                self.email_for_reset = email
                QMessageBox.information(self, "Code envoyé", 
                    f"✅ Un code de vérification a été envoyé à:\n{email}\n\n"
                    "Vérifiez votre boîte mail (et les spams).")
                self._go_to_step(2)
                self._start_cooldown()
            else:
                QMessageBox.warning(self, "Email introuvable", 
                    "Aucun compte trouvé avec cet email.\n\n"
                    "Vérifiez l'orthographe ou créez un nouveau compte.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'envoyer le code:\n{str(e)}")

    def _verify_code(self):
        code = self.code.text().strip()
        if not code or len(code) != 6:
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres.")
            return
        
        try:
            if self.auth.verify_reset_code(self.email_for_reset, code):
                QMessageBox.information(self, "Code vérifié", "✅ Code correct! Créez votre nouveau mot de passe.")
                self._go_to_step(3)
            else:
                QMessageBox.warning(self, "Code invalide", 
                    "Le code saisi est invalide ou a expiré.\n\n"
                    "Demandez un nouveau code.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de vérification:\n{str(e)}")

    def _reset_password(self):
        n1 = self.new1.text()
        n2 = self.new2.text()
        code = self.code.text().strip()
        
        if not n1 or not n2:
            QMessageBox.warning(self, "Champs vides", "Veuillez remplir tous les champs.")
            return
        
        if n1 != n2:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        
        if len(n1) < 8:
            QMessageBox.warning(self, "Mot de passe trop court", 
                "Le mot de passe doit contenir au moins 8 caractères.")
            return
        
        try:
            ok = self.auth.update_password_with_code(self.email_for_reset, code, n1)
            if ok:
                QMessageBox.information(
                    self, 
                    "Succès", 
                    "🎉 Votre mot de passe a été réinitialisé avec succès!\n\n"
                    "Vous pouvez maintenant vous connecter avec votre nouveau mot de passe."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "Erreur", 
                    "Une erreur est survenue lors de la réinitialisation.\n\n"
                    "Le code a peut-être expiré. Recommencez le processus.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la réinitialisation:\n{str(e)}")

    def _go_to_step(self, step):
        self.current_step = step
        
        self.step1_widget.setVisible(False)
        self.step2_widget.setVisible(False)
        self.step3_widget.setVisible(False)
        
        if step == 1:
            self.title_label.setText("Étape 1: Adresse e-mail")
            self.step1_widget.setVisible(True)
        elif step == 2:
            self.title_label.setText("Étape 2: Vérification du code")
            self.step2_widget.setVisible(True)
            self.code.setFocus()
        elif step == 3:
            self.title_label.setText("Étape 3: Nouveau mot de passe")
            self.step3_widget.setVisible(True)
            self.new1.setFocus()

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.btn_send_code.setEnabled(True)
            self.status_label.setText("")
        else:
            self.status_label.setText(f"⏱️ Renvoyer le code dans {self.remaining}s")

    def _start_cooldown(self):
        self.remaining = self.COOLDOWN
        self.btn_send_code.setEnabled(False)
        self.timer.start(1000)


# Also add this AnimatedButton class if it doesn't exist in your modals.py:
class AnimatedButton(QPushButton):
    """Button with hover animation"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

# ==================== EDIT PROFILE MODAL (FIXED) ====================

class EditProfileModal(QDialog):
    """Edit user profile - name, email, master password"""
    profile_updated = pyqtSignal(dict)

    def __init__(self, user_data, auth_manager, parent=None):
        super().__init__(parent)
        self.user_data = user_data or {}
        self.auth = auth_manager
        self.setWindowTitle("Modifier le profil")
        self.setFixedSize(520, 700)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 25px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        head = QVBoxLayout()
        head.setAlignment(Qt.AlignCenter)
        head.setSpacing(12)

        avatar = QLabel(self.user_data.get('initials', 'US'))
        avatar.setFixedSize(88, 88)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.PURPLE});
                border-radius: 44px;
                color: white;
                font-weight: bold;
                font-size: 32px;
            }}
        """)
        head.addWidget(avatar)

        title = QLabel("✏️ Modifier le profil")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(20))
        title.setAlignment(Qt.AlignCenter)
        head.addWidget(title)

        layout.addLayout(head)

        # Form
        form = QVBoxLayout()
        form.setSpacing(14)

        # Name
        name_label = QLabel("👤 Nom complet")
        name_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        form.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(self.user_data.get('username') or self.user_data.get('name', ''))
        self.name_input.setPlaceholderText("Votre nom complet")
        self.name_input.setMinimumHeight(48)
        style_line_edit(self.name_input)
        form.addWidget(self.name_input)

        # Email (read-only)
        email_label = QLabel("📧 Adresse e-mail")
        email_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        form.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setText(self.user_data.get('email', ''))
        self.email_input.setReadOnly(True)
        self.email_input.setMinimumHeight(48)
        self.email_input.setStyleSheet(f"""
            {Styles.get_input_style()}
            background-color: rgba(255,255,255,0.03);
            color: {Styles.TEXT_MUTED};
        """)
        form.addWidget(self.email_input)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.06); max-height: 1px;")
        form.addWidget(sep)

        # Current password (required)
        current_label = QLabel("🔒 Mot de passe actuel (requis)")
        current_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size:13px; background: transparent;")
        form.addWidget(current_label)

        current_row = QHBoxLayout()
        self.current_pwd_input = QLineEdit()
        self.current_pwd_input.setEchoMode(QLineEdit.Password)
        self.current_pwd_input.setPlaceholderText("Entrez votre mot de passe actuel")
        self.current_pwd_input.setMinimumHeight(48)
        style_line_edit(self.current_pwd_input)
        current_row.addWidget(self.current_pwd_input)

        self.toggle_current_btn = QPushButton("👁️")
        self.toggle_current_btn.setFixedSize(44, 44)
        self.toggle_current_btn.setCheckable(True)
        self.toggle_current_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:8px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_current_btn.toggled.connect(lambda c: self.current_pwd_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password))
        current_row.addWidget(self.toggle_current_btn)
        form.addLayout(current_row)

        form.addSpacing(8)

        # Change password (optional)
        change_label = QLabel("🔐 Changer le mot de passe (optionnel)")
        change_label.setStyleSheet(f"color: {Styles.BLUE_SECONDARY}; font-size:14px; font-weight:bold; background: transparent;")
        form.addWidget(change_label)

        new_row = QHBoxLayout()
        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setEchoMode(QLineEdit.Password)
        self.new_pwd_input.setPlaceholderText("Laisser vide pour conserver l'actuel")
        self.new_pwd_input.setMinimumHeight(48)
        style_line_edit(self.new_pwd_input)
        new_row.addWidget(self.new_pwd_input)

        self.toggle_new_btn = QPushButton("👁️")
        self.toggle_new_btn.setFixedSize(44, 44)
        self.toggle_new_btn.setCheckable(True)
        self.toggle_new_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:8px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_new_btn.toggled.connect(lambda c: (
            self.new_pwd_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password),
            self.confirm_pwd_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password)
        ))
        new_row.addWidget(self.toggle_new_btn)
        form.addLayout(new_row)

        # Strength indicator
        self.strength_widget = PasswordStrengthWidget()
        self.new_pwd_input.textChanged.connect(self.strength_widget.update_strength)
        form.addWidget(self.strength_widget)

        # Confirm password label
        confirm_label = QLabel("✅ Confirmer le nouveau mot de passe")
        confirm_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size:13px; background: transparent;")
        form.addWidget(confirm_label)
        
        self.confirm_pwd_input = QLineEdit()
        self.confirm_pwd_input.setEchoMode(QLineEdit.Password)
        self.confirm_pwd_input.setPlaceholderText("Confirmez le nouveau mot de passe")
        self.confirm_pwd_input.setMinimumHeight(48)
        style_line_edit(self.confirm_pwd_input)
        form.addWidget(self.confirm_pwd_input)

        layout.addLayout(form)
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = AnimatedButton("❌ Annuler")
        cancel_btn.setStyleSheet(Styles.get_button_style(primary=False))
        cancel_btn.setMinimumHeight(48)
        cancel_btn.clicked.connect(self.reject)
        save_btn = AnimatedButton("💾 Enregistrer les modifications")
        save_btn.setStyleSheet(Styles.get_button_style(primary=True))
        save_btn.setMinimumHeight(48)
        save_btn.clicked.connect(self.on_save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def on_save(self):
        name = self.name_input.text().strip()
        current_pwd = self.current_pwd_input.text()
        new_pwd = self.new_pwd_input.text()
        confirm_pwd = self.confirm_pwd_input.text()

        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom ne peut pas être vide")
            return
        if not current_pwd:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer votre mot de passe actuel pour confirmer")
            return

        # Verify current password via auth manager
        try:
            user = self.auth._user_by_email(self.user_data.get('email'))
            if not user:
                QMessageBox.warning(self, "Erreur", "Utilisateur introuvable")
                return
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur de connexion: {str(e)}")
            return

        if not self.auth._verify_password(current_pwd, user.get('password_hash'), user.get('salt')):
            QMessageBox.warning(self, "Erreur", "Le mot de passe actuel est incorrect")
            return

        # Validate new password if provided
        if new_pwd or confirm_pwd:
            if new_pwd != confirm_pwd:
                QMessageBox.warning(self, "Erreur", "Les nouveaux mots de passe ne correspondent pas")
                return
            if len(new_pwd) < 8:
                QMessageBox.warning(self, "Erreur", "Le nouveau mot de passe doit contenir au moins 8 caractères")
                return
            strength, _, _ = PasswordStrengthChecker.check_strength(new_pwd)
            if strength == "weak":
                reply = QMessageBox.question(
                    self,
                    "⚠️ Mot de passe faible",
                    "Le nouveau mot de passe est faible. Voulez-vous continuer quand même ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

        # Persist changes
        try:
            conn = self.auth._conn()
            cursor = conn.cursor()
            
            # Update name
            cursor.execute("UPDATE users SET username = %s WHERE email = %s", (name, self.user_data.get('email')))
            
            # Update password if provided
            if new_pwd:
                pw_hash, salt = self.auth._hash_password(new_pwd)
                cursor.execute("UPDATE users SET password_hash = %s, salt = %s WHERE email = %s", 
                             (pw_hash, salt, self.user_data.get('email')))
            
            conn.commit()
            cursor.close()
            conn.close()

            # Emit updated user data
            updated = {
                'id': self.user_data.get('id'),
                'username': name,
                'email': self.user_data.get('email'),
                'name': name,
                'initials': (name[:2] or "US").upper()
            }
            self.profile_updated.emit(updated)
            
            success_msg = "✅ Profil mis à jour avec succès!"
            if new_pwd:
                success_msg += "\n\nVotre mot de passe a été modifié."
            
            QMessageBox.information(self, "Succès", success_msg)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour: {str(e)}")
            print(f"❌ Profile update error: {e}")