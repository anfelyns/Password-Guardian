# ==========================================================
# SecureVault - GUI Modals (Login, Register, Forgot, Add, Edit, View, 2FA)
# ==========================================================

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFormLayout, QCheckBox, QComboBox, QWidget, QFrame, QMessageBox,
    QApplication, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont
import random, string, re
from datetime import datetime
# ---------- Login ----------
class LoginModal(QDialog):
    login_success = pyqtSignal(str, str)
    switch_to_register = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Connexion")
        self.setFixedSize(450, 570)
        self.setModal(True)
        
        # Fix black background issue
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.WindowCloseButtonHint |
            Qt.WindowTitleHint
        )
        
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles
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
        icon.setStyleSheet("font-size:46px;")
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
        lbl.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
        self.email_input = QLineEdit()
        style_line_edit(self.email_input)
        self.email_input.setPlaceholderText("votre@email.com")
        form.addWidget(lbl)
        form.addWidget(self.email_input)
        form.addSpacing(6)

        # Mot de passe
        lbl2 = QLabel("🔒 Mot de passe")
        lbl2.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
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

        # Error message (initially hidden)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
        self.error_label.setWordWrap(True)
        form.addWidget(self.error_label)

        layout.addLayout(form)

        login_btn = AnimatedButton("🚀 Se connecter")
        login_btn.setStyleSheet(Styles.get_button_style(primary=True))
        login_btn.setMinimumHeight(50)
        login_btn.clicked.connect(self.on_login)
        layout.addWidget(login_btn)

        # Forgot password link
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
        
        # Clear previous errors
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
            self.error_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: bold;")
            self.error_label.setText("✅ Mot de passe réinitialisé. Connectez-vous avec votre nouveau mot de passe.")


# ---------- Register ----------
class RegisterModal(QDialog):
    register_success = pyqtSignal(str, str, str)
    switch_to_login = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Inscription")
        self.setFixedSize(500, 680)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles
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
        icon.setStyleSheet("font-size:46px;")
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

        # Nom complet
        nlab = QLabel("👤 Nom complet")
        nlab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
        self.name_input = QLineEdit()
        style_line_edit(self.name_input)
        self.name_input.setPlaceholderText("Entrez votre nom complet")
        form.addWidget(nlab)
        form.addWidget(self.name_input)
        form.addSpacing(6)

        # Email
        elab = QLabel("📧 Adresse e-mail")
        elab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
        self.email_input = QLineEdit()
        style_line_edit(self.email_input)
        self.email_input.setPlaceholderText("votre@email.com")
        form.addWidget(elab)
        form.addWidget(self.email_input)
        form.addSpacing(6)

        # Mot de passe
        plab = QLabel("🔒 Mot de passe maître")
        plab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
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
        
        # Generate strong password suggestion for weak passwords
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
        weak_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
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

        # Confirmer mot de passe
        clab = QLabel("✅ Confirmer le mot de passe")
        clab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px; font-weight: normal;")
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
        
        # Show/hide weak password warning
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
        
        # Show the password temporarily
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
        
        # Check password strength
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


# ---------- Add Password ----------
class AddPasswordModal(QDialog):
    password_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un mot de passe")
        self.setFixedSize(500, 650)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        head = QHBoxLayout()
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:30px;")
        title = QLabel("Nouveau Mot de Passe")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(22))
        head.addWidget(icon)
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        form = QVBoxLayout()
        form.setSpacing(12)

        lab = QLabel("🌐 Nom du site")
        lab.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        self.site_input = QLineEdit()
        style_line_edit(self.site_input)
        self.site_input.setPlaceholderText("ex: google.com, github.com...")
        form.addWidget(lab)
        form.addWidget(self.site_input)

        lab2 = QLabel("📧 Email / Identifiant")
        lab2.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        self.email_input = QLineEdit()
        style_line_edit(self.email_input)
        self.email_input.setPlaceholderText("votre@email.com ou nom d'utilisateur")
        form.addWidget(lab2)
        form.addWidget(self.email_input)

        lab3 = QLabel("🔒 Mot de passe")
        lab3.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        row = QHBoxLayout()
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        style_line_edit(self.pwd_input)
        self.pwd_input.setPlaceholderText("Saisissez ou générez un mot de passe")
        self.toggle_pwd_btn = QPushButton("👁️")
        self.toggle_pwd_btn.setFixedSize(40, 40)
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.setStyleSheet("""
            QPushButton { background-color: rgba(255,255,255,0.1); border:none; border-radius:8px; }
            QPushButton:checked { background-color: rgba(59,130,246,0.3); }
        """)
        self.toggle_pwd_btn.toggled.connect(
            lambda c: self.pwd_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password)
        )
        row.addWidget(self.pwd_input)
        row.addWidget(self.toggle_pwd_btn)
        form.addWidget(lab3)
        form.addLayout(row)

        gen = QHBoxLayout()
        self.generate_checkbox = QCheckBox("🎲 Générer un mot de passe sécurisé")
        self.generate_checkbox.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_PRIMARY))
        self.generate_checkbox.toggled.connect(self.toggle_password_generation)
        gen.addWidget(self.generate_checkbox)

        self.generate_btn = AnimatedButton("Générer")
        self.generate_btn.setVisible(False)
        self.generate_btn.clicked.connect(self.generate_password)
        self.generate_btn.setStyleSheet(Styles.get_button_style(primary=False))
        gen.addWidget(self.generate_btn)
        gen.addStretch()
        form.addLayout(gen)

        self.strength_widget = PasswordStrengthWidget()
        self.pwd_input.textChanged.connect(self.strength_widget.update_strength)
        form.addWidget(self.strength_widget)
        form.addSpacing(8)

        cl = QLabel("📁 Catégorie")
        cl.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["👤 Personnel", "💼 Travail", "💳 Finance", "🎮 Jeux", "📚 Étude", "📁 Autre"])
        self.category_combo.setMinimumHeight(44)
        self.category_combo.setFont(QFont("Segoe UI", 12))
        self.category_combo.setStyleSheet(Styles.get_input_style())
        form.addWidget(cl)
        form.addWidget(self.category_combo)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        cancel = AnimatedButton("❌ Annuler")
        cancel.setStyleSheet(Styles.get_button_style(primary=False))
        cancel.setMinimumHeight(48)
        save = AnimatedButton("💾 Enregistrer le mot de passe")
        save.setStyleSheet(Styles.get_button_style(primary=True))
        save.setMinimumHeight(48)
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
        pwd = PasswordStrengthChecker.generate_strong_password()
        self.pwd_input.setText(pwd)
        self.strength_widget.update_strength(pwd)

    def on_save(self):
        """Save password with proper category mapping"""
        site = self.site_input.text().strip()
        user = self.email_input.text().strip()
        pwd = self.pwd_input.text().strip()
        
        if not site:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un nom de site")
            return
        if not user:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un email/identifiant")
            return
        if not pwd:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un mot de passe")
            return
        
        # Map French display names to English category keys
        category_map = {
            "👤 Personnel": "personal",
            "💼 Travail": "work",
            "💳 Finance": "finance",
            "🎮 Jeux": "game",
            "📚 Étude": "study",
            "📁 Autre": "personal"
        }
        
        display_cat = self.category_combo.currentText()
        category = category_map.get(display_cat, "personal")
        
        self.password_added.emit({
            'site_name': site,
            'username': user,
            'password': pwd,
            'category': category
        })
        self.accept()


# ---------- View, Edit, TwoFactor ----------
class ViewPasswordModal(QDialog):
    def __init__(self, password_data, parent=None):
        super().__init__(parent)
        self.password_data = password_data
        self.setWindowTitle(f"Mot de passe - {password_data['site_name']}")
        self.setFixedSize(400, 300)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        from gui.styles.styles import Styles
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        head = QHBoxLayout()
        icon = QLabel(self.password_data.get('site_icon', '🔑'))
        icon.setStyleSheet("font-size:22px;")
        title = QLabel(self.password_data['site_name'])
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(18))
        head.addWidget(icon)
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        info = QVBoxLayout()
        info.setSpacing(12)

        l1 = QVBoxLayout()
        lbl_id = QLabel("📧 Identifiant")
        lbl_id.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED))
        val_id = QLabel(self.password_data['username'])
        val_id.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
        l1.addWidget(lbl_id)
        l1.addWidget(val_id)
        info.addLayout(l1)

        l2 = QVBoxLayout()
        lbl_pwd = QLabel("🔒 Mot de passe")
        lbl_pwd.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED))
        row = QHBoxLayout()
        val_pwd = QLabel(self.password_data.get('encrypted_password', 'Non disponible'))
        val_pwd.setStyleSheet("""
            color:#60a5fa; font-family:'Courier New'; font-size:16px; font-weight:bold; letter-spacing:2px;
            background-color: rgba(255,255,255,0.05); border-radius:8px; padding:10px;
        """)
        copy = AnimatedButton("📋")
        copy.setFixedSize(40, 40)
        copy.setStyleSheet(Styles.get_button_style(False))
        copy.clicked.connect(self.copy_password)
        row.addWidget(val_pwd, 1)
        row.addWidget(copy)
        l2.addWidget(lbl_pwd)
        l2.addLayout(row)
        info.addLayout(l2)

        layout.addLayout(info)
        layout.addStretch()
        close = AnimatedButton("Fermer")
        close.setStyleSheet(Styles.get_button_style(True))
        close.setMinimumHeight(44)
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def copy_password(self):
        QApplication.clipboard().setText(self.password_data.get('encrypted_password', ''))
        QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier !")


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
        from gui.styles.styles import Styles
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
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
        lbl_old.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY))
        self.in_old = QLineEdit()
        self.in_old.setEchoMode(QLineEdit.Password)
        style_line_edit(self.in_old)
        layout.addWidget(lbl_old)
        layout.addWidget(self.in_old)

        lbl_new = QLabel("Nouveau mot de passe")
        lbl_new.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY))
        self.in_new = QLineEdit()
        self.in_new.setEchoMode(QLineEdit.Password)
        style_line_edit(self.in_new)
        layout.addWidget(lbl_new)
        layout.addWidget(self.in_new)

        lbl_rep = QLabel("Répéter le nouveau mot de passe")
        lbl_rep.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY))
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
        from gui.styles.styles import Styles
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
        info.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY))
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
        
        # Emit signal - parent will verify the code
        self.code_verified.emit()
# src/gui/components/modals.py - COMPLET avec toutes les corrections

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QFrame, QProgressBar, QMessageBox, QCheckBox, QApplication, QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont
import random, string, re
from datetime import datetime


# ---------- Helper: style QLineEdit "pilule" ----------
def style_line_edit(le):
    from gui.styles.styles import Styles
    le.setFrame(False)
    le.setMinimumHeight(44)
    le.setFont(QFont("Segoe UI", 12))
    le.setTextMargins(12, 0, 12, 0)
    le.setProperty("readonly", False)
    le.setStyleSheet(Styles.get_input_style())


# ---------- UI helpers ----------
class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, e):
        self._fade_to(0.92); super().enterEvent(e)

    def leaveEvent(self, e):
        self._fade_to(1.0); super().leaveEvent(e)

    def _fade_to(self, val):
        self._anim.stop()
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(val)
        self._anim.start()


class PasswordStrengthChecker:
    @staticmethod
    def check_strength(password):
        score, fb = 0, []
        if len(password) < 8: fb.append("Au moins 8 caractères requis")
        else: score += 1
        if len(password) >= 12: score += 1
        if re.search(r"[a-z]", password): score += 1
        else: fb.append("Ajoutez des lettres minuscules")
        if re.search(r"[A-Z]", password): score += 1
        else: fb.append("Ajoutez des lettres majuscules")
        if re.search(r"\d", password): score += 1
        else: fb.append("Ajoutez des chiffres")
        if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=;]', password): score += 1
        else: fb.append("Ajoutez des caractères spéciaux")

        lvl = "weak" if score <= 2 else ("medium" if score <= 4 else "strong")
        return lvl, score, fb

    @staticmethod
    def generate_strong_password(length=16):
        lower, upper, digits, special = string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#$%^&*()_+-=[]{}|;:,.<>?"
        pwd = [random.choice(lower), random.choice(upper), random.choice(digits), random.choice(special)]
        allc = lower + upper + digits + special
        pwd += random.choices(allc, k=max(4, length)-4)
        random.shuffle(pwd)
        return "".join(pwd)


class PasswordStrengthWidget(QFrame):
    """Widget compact avec barre + label + suggestions, hauteur fixe."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(80)
        self._init_ui()

    def _init_ui(self):
        from gui.styles.styles import Styles
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(6)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(255,255,255,0.10); border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background-color: {Styles.WEAK_COLOR}; border-radius: 4px; }}
        """)
        lay.addWidget(self.progress)

        self.strength_label = QLabel("")
        self.strength_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(self.strength_label)

        self.feedback_label = QLabel("")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(self.feedback_label)

    def update_strength(self, password):
        from gui.styles.styles import Styles
        if not password:
            self.progress.setValue(0)
            self.strength_label.setText("")
            self.feedback_label.setText("")
            return

        strength, score, fb = PasswordStrengthChecker.check_strength(password)
        self.progress.setValue(int((score/6)*100))

        if strength == "weak":
            color, text = Styles.WEAK_COLOR, "❌ Mot de passe faible"
        elif strength == "medium":
            color, text = Styles.MEDIUM_COLOR, "⚠️ Mot de passe moyen"
        else:
            color, text = Styles.STRONG_COLOR, "✅ Mot de passe fort"

        self.progress.setStyleSheet(f"""
            QProgressBar {{ background-color: rgba(255,255,255,0.10); border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
        """)

        self.strength_label.setText(text)
        self.strength_label.setStyleSheet(f"color:{color}; font-weight:bold; font-size:12px;")
        self.feedback_label.setText(("Suggestions: " + ", ".join(fb)) if fb else "✨ Excellent mot de passe !")
        self.feedback_label.setStyleSheet("color: rgba(255,255,255,0.70); font-size:11px;")


# ---------- Forgot Password Dialog (Multi-step) ----------
class ForgotPasswordDialog(QDialog):
    """Multi-step forgot password: email -> code -> new password"""

    COOLDOWN = 60

    def __init__(self, auth_mgr, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mot de passe oublié")
        self.setModal(True)
        self.setFixedSize(450, 450)

        self.auth = auth_mgr
        self.remaining = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        
        self.current_step = 1
        self.email_for_reset = None

        from gui.styles.styles import Styles
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.1); border-radius: 25px;
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
        icon.setStyleSheet("font-size:46px;")
        
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
        lbl_email.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px;")
        
        self.email = QLineEdit()
        style_line_edit(self.email)
        self.email.setPlaceholderText("votre@email.com")
        
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
        
        lbl_code = QLabel("📱 Code de vérification")
        lbl_code.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px;")
        
        self.code = QLineEdit()
        style_line_edit(self.code)
        self.code.setPlaceholderText("Entrez le code à 6 chiffres")
        self.code.setMaxLength(6)
        self.code.setAlignment(Qt.AlignCenter)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.60); font-size: 12px;")
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
        lbl_new1.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px;")
        
        self.new1 = QLineEdit()
        style_line_edit(self.new1)
        self.new1.setPlaceholderText("Créez un mot de passe fort")
        self.new1.setEchoMode(QLineEdit.Password)
        
        lbl_new2 = QLabel("✅ Confirmer le mot de passe")
        lbl_new2.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px;")
        
        self.new2 = QLineEdit()
        style_line_edit(self.new2)
        self.new2.setPlaceholderText("Confirmez votre mot de passe")
        self.new2.setEchoMode(QLineEdit.Password)
        
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
        
        ok = self.auth.send_reset_code(email)
        if ok:
            self.email_for_reset = email
            QMessageBox.information(self, "Code envoyé", "Un code de vérification a été envoyé à votre adresse email.")
            self._go_to_step(2)
            self._start_cooldown()
        else:
            QMessageBox.warning(self, "Email introuvable", "Aucun compte trouvé avec cet email.")

    def _verify_code(self):
        code = self.code.text().strip()
        if not code or len(code) != 6:
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres.")
            return
        
        if self.auth.verify_reset_code(self.email_for_reset, code):
            self._go_to_step(3)
        else:
            QMessageBox.warning(self, "Code invalide", "Le code saisi est invalide ou a expiré.")

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
            QMessageBox.warning(self, "Mot de passe trop court", "Le mot de passe doit contenir au moins 8 caractères.")
            return
        
        ok = self.auth.update_password_with_code(self.email_for_reset, code, n1)
        if ok:
            QMessageBox.information(
                self, 
                "Succès", 
                "✅ Votre mot de passe a été réinitialisé avec succès!\n\n"
                "Vous pouvez maintenant vous connecter avec votre nouveau mot de passe."
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Une erreur est survenue lors de la réinitialisation.")

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
        elif step == 3:
            self.title_label.setText("Étape 3: Nouveau mot de passe")
            self.step3_widget.setVisible(True)

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.btn_send_code.setEnabled(True)
            self.status_label.setText("")
        else:
            self.status_label.setText(f"⏱️ Renvoyer le code disponible dans {self.remaining}s")

    def _start_cooldown(self):
        self.remaining = self.COOLDOWN
        self.btn_send_code.setEnabled(False)
        self.timer.start(1000)

