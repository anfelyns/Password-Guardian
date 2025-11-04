
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QApplication, QMessageBox, QDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from gui.components.sidebar import Sidebar
from gui.components.password_list import PasswordList
from gui.components.modals import (
    LoginModal, RegisterModal, AddPasswordModal,
    ViewPasswordModal, EditPasswordModal, TwoFactorModal
)
from gui.styles.styles import Styles
from auth.auth_manager import AuthManager
from backend.api_client import APIClient


class UserProfileWidget(QWidget):
    logout_clicked = pyqtSignal()
    show_statistics = pyqtSignal()

    def __init__(self, username, initials, parent=None):
        super().__init__(parent)
        self.username = username
        self.initials = initials
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.avatar = QPushButton(self.initials)
        self.avatar.setFixedSize(40, 40)
        self.avatar.setCursor(Qt.PointingHandCursor)
        self.avatar.clicked.connect(self.show_user_menu)
        self.avatar.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.PURPLE});
                border-radius: 20px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            }}
        """)
        layout.addWidget(self.avatar)

        self.name_btn = QPushButton(self.username)
        self.name_btn.setCursor(Qt.PointingHandCursor)
        self.name_btn.clicked.connect(self.show_user_menu)
        self.name_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Styles.TEXT_PRIMARY};
                border: none;
                font-size: 14px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{ color: {Styles.BLUE_SECONDARY}; }}
        """)
        layout.addWidget(self.name_btn)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 25px;
                padding: 8px 15px;
            }
        """)

    def show_user_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 15px;
                min-width: 280px;
            }}
            QMenu::item {{
                padding: 12px 20px;
                border-radius: 10px;
                color: {Styles.TEXT_PRIMARY};
                margin: 3px;
                font-size: 14px;
            }}
            QMenu::item:selected {{
                background-color: rgba(59, 130, 246, 0.2);
            }}
            QMenu::separator {{
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                margin: 8px 0;
            }}
        """)

        header = QAction(f"👋 {self.username}", self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        stats_action = QAction("📊 Mes Statistiques", self)
        stats_action.triggered.connect(self.show_statistics.emit)
        menu.addAction(stats_action)

        menu.addSeparator()

        logout_action = QAction("🚪 Se déconnecter", self)
        logout_action.triggered.connect(self.logout_clicked.emit)
        menu.addAction(logout_action)

        menu.exec_(self.mapToGlobal(self.rect().bottomRight()))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.auth = AuthManager(
            host='localhost', 
            user='root', 
            password='inessouai2005_',
            database='password_guardian', 
            port=3306
        )
        self.api_client = APIClient(base_url="http://localhost:5000")

        self.current_user = None
        self._all_passwords = []
        
        self.init_ui()
        
        self.show_auth_flow()

    def init_ui(self):
        self.setWindowTitle("SecureVault")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                );
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(20)

        self.header = self.create_header()
        main.addWidget(self.header)

        content = QHBoxLayout()
        content.setSpacing(30)

        self.sidebar = Sidebar()
        self.sidebar.category_changed.connect(self.on_category_changed)
        self.sidebar.add_password_clicked.connect(self.show_add_password_modal)
        content.addWidget(self.sidebar)

        self.password_list = PasswordList()
        self.setup_password_list_connections()

        wrap = QFrame()
        wrap.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        wlay = QVBoxLayout(wrap)
        wlay.setContentsMargins(0, 0, 0, 0)
        wlay.addWidget(self.password_list)
        content.addWidget(wrap, 1)

        main.addLayout(content)

    def create_header(self):
        header = QWidget()
        lay = QHBoxLayout(header)
        lay.setContentsMargins(0, 0, 0, 0)

        left = QHBoxLayout()
        left.setSpacing(12)
        
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size: 32px;")
        left.addWidget(icon)

        txt = QLabel("SecureVault")
        txt.setFont(QFont("Segoe UI", 24, QFont.Bold))
        txt.setStyleSheet(f"color: {Styles.TEXT_PRIMARY}; background: transparent;")
        left.addWidget(txt)

        lay.addLayout(left)
        lay.addStretch()

        self.user_profile_container = QWidget()
        self.user_profile_layout = QHBoxLayout(self.user_profile_container)
        self.user_profile_layout.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.user_profile_container)
        return header

    def setup_password_list_connections(self):
        self.password_list.copy_password.connect(self.on_copy_password)
        self.password_list.view_password.connect(self.on_view_password)
        self.password_list.edit_password.connect(self.on_edit_password)
        self.password_list.delete_password.connect(self.on_delete_password)
        self.password_list.favorite_password.connect(self.on_favorite_password)

    def show_auth_flow(self):
        """Start the authentication flow"""
        self.login_dialog = LoginModal(self)
        self.login_dialog.login_success.connect(self.on_login_attempt)
        self.login_dialog.switch_to_register.connect(self.on_switch_to_register)
        
        result = self.login_dialog.exec_()
        
        if result != QDialog.Accepted and not self.current_user:
            QApplication.quit()
    
    def on_switch_to_register(self):
        """Handle switch to register"""
        if hasattr(self, 'login_dialog') and self.login_dialog:
            self.login_dialog.close()
        
        self.show_register_modal()

    def show_login_modal(self):
        """Show login dialog"""
        dlg = LoginModal(self)
        dlg.login_success.connect(self.on_login_attempt)
        dlg.switch_to_register.connect(self.show_register_modal)
        
        if dlg.exec_() != QDialog.Accepted:
            QApplication.quit()

    def show_register_modal(self):
        """Show registration dialog"""
        dlg = RegisterModal(self)
        dlg.register_success.connect(self.on_register_attempt)
        dlg.switch_to_login.connect(self.show_login_modal)
        dlg.exec_()

    def on_login_attempt(self, email, password):
        """Handle login attempt"""
        print(f"🔐 Login attempt for: {email}")
        
        result = self.auth.authenticate(email, password)
        
        if result.get('error'):
            QMessageBox.warning(self, "Erreur d'authentification", result['error'])
            self.show_login_modal()
            return
        
        if not result.get('2fa_sent'):
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le code 2FA")
            self.show_login_modal()
            return
        
        user_info = result.get('user')
        if not user_info:
            QMessageBox.warning(self, "Erreur", "Utilisateur non trouvé")
            self.show_login_modal()
            return
        
        print(f"✅ 2FA code sent to {email}")
        self.show_2fa_dialog(user_info)

    def show_register_modal(self):
        """Show registration dialog"""
        dlg = RegisterModal(self)
        dlg.register_success.connect(self.on_register_attempt)
        dlg.switch_to_login.connect(self.on_switch_to_login)
        dlg.exec_()
    
    def on_switch_to_login(self):
        """Handle switch back to login"""
        self.show_auth_flow()

    def on_register_attempt(self, name, email, password):
        """Handle registration attempt"""
        print(f"📝 Registration attempt: {name} ({email})")
        
        success, message, extra = self.auth.register_user(name, email, password)
        
        if not success:
            QMessageBox.warning(self, "Inscription", message)
            self.show_register_modal()
            return
        
        print(f"✅ User registered: {email}")
        QMessageBox.information(
            self,
            "Inscription réussie",
            f"✅ {message}\n\nVeuillez vérifier votre boîte mail pour confirmer votre compte."
        )
        
        self.show_verification_dialog(email, extra.get('user_id'))

    def show_verification_dialog(self, email, user_id):
        """Show email verification dialog"""
        print(f"📧 Showing verification dialog for {email}")
        
        tf = TwoFactorModal(email, "<code envoyé par email>", self)
        
        def custom_verify():
            code = tf.code_input.text().strip()
            
            if not code or len(code) != 6:
                QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres")
                return
            
            print(f"🔐 Verifying registration code: {code}")
            
            if self.auth.verify_registration_code(email, code):
                print(f"✅ Email verified successfully!")
                tf.accept()
                
                QMessageBox.information(
                    self,
                    "Compte vérifié",
                    "✅ Votre compte a été vérifié avec succès!\n\nVous pouvez maintenant vous connecter."
                )
                
                self.show_auth_flow()
            else:
                print(f"❌ Invalid verification code")
                QMessageBox.warning(self, "Code invalide", "Le code saisi est invalide ou a expiré")
        
        try:
            tf.code_verified.disconnect()
        except:
            pass
        
        tf.code_verified.connect(custom_verify)
        
        result = tf.exec_()
        
        if result != QDialog.Accepted:
            print("❌ Verification cancelled")
            self.show_auth_flow()

    def verify_registration_code(self, email, tf_dialog, user_id):
        """Verify registration code"""
        code = tf_dialog.code_input.text().strip()
        
        if not code or len(code) != 6:
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres")
            return
        
        print(f"🔐 Verifying registration code: {code} for {email}")
        
        if self.auth.verify_registration_code(email, code):
            print(f"✅ Email verified successfully!")
            tf_dialog.accept()
        else:
            print(f"❌ Verification failed")
            QMessageBox.warning(self, "Code invalide", "Le code saisi est invalide ou a expiré")

    def show_2fa_dialog(self, user_info):
        """Show 2FA verification dialog"""
        print(f"🔐 Showing 2FA dialog for {user_info['email']}")
        
        tf = TwoFactorModal(user_info['email'], "<code envoyé par email>", self)
        
        original_verify = tf.on_verify_clicked
        
        def custom_verify():
            code = tf.code_input.text().strip()
            
            if not code or len(code) != 6:
                QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres")
                return
            
            print(f"🔐 Verifying 2FA code: {code}")
            
            if self.auth.verify_2fa_email(user_info['email'], code):
                print(f"✅ 2FA verified successfully!")
                
                self.finalize_login(user_info)
            else:
                print(f"❌ Invalid 2FA code")
                QMessageBox.warning(self, "Code invalide", "Le code 2FA saisi est invalide ou a expiré")
        
        try:
            tf.code_verified.disconnect()
        except:
            pass
        
        tf.code_verified.connect(custom_verify)
        
        result = tf.exec_()
        
        print(f"2FA dialog closed with result: {result}")
        
        if result != QDialog.Accepted:
            print("❌ 2FA dialog was cancelled")
            self.show_login_modal()

    def verify_2fa_code(self, user_info, tf_dialog):
        """Verify 2FA code and complete login"""
        code = tf_dialog.code_input.text().strip()
        
        if not code or len(code) != 6:
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres")
            return
        
        print(f"🔐 Verifying 2FA code: {code} for {user_info['email']}")
        
        if self.auth.verify_2fa_email(user_info['email'], code):
            print(f"✅ 2FA verified successfully!")
            
            QTimer.singleShot(100, lambda: self.finalize_login(user_info))
        else:
            print(f"❌ 2FA verification failed")
            QMessageBox.warning(self, "Code invalide", "Le code 2FA saisi est invalide ou a expiré")

    def finalize_login(self, user_info: dict):
        """Complete login and show main interface"""
        print(f"🎉 Finalizing login for user: {user_info}")
        
        name = (user_info.get('username') or user_info.get('email', '').split('@')[0] or "User").capitalize()
        initials = (name[:2] or "US").upper()

        for i in reversed(range(self.user_profile_layout.count())):
            w = self.user_profile_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.current_user = {
            'id': user_info.get('id'),
            'username': user_info.get('username') or name,
            'email': user_info.get('email'),
            'name': name,
            'initials': initials,
        }
        
        print(f"✅ Current user set: {self.current_user}")

        self.user_profile = UserProfileWidget(self.current_user['name'], self.current_user['initials'], self)
        self.user_profile.logout_clicked.connect(self.on_logout)
        self.user_profile.show_statistics.connect(self.show_statistics_modal)
        self.user_profile_layout.addWidget(self.user_profile)
        
        print(f"✅ User profile widget created and added")

        print(f"📥 Loading passwords for user {self.current_user['id']}")
        self.load_passwords()
        
        print(f"✅ Login complete! Welcome {self.current_user['name']}")
        
        QMessageBox.information(
            self, 
            "Connexion réussie", 
            f"✅ Bienvenue {self.current_user['name']} !\n\nVous êtes maintenant connecté à SecureVault."
        )

    def load_passwords(self):
        """Load passwords from database via API"""
        if not self.current_user:
            self._all_passwords = []
            self.password_list.load_passwords([])
            return
        
        print(f"📥 Loading passwords for user: {self.current_user['id']}")
        
        success, message, passwords = self.api_client.get_passwords(self.current_user['id'])
        
        if success and passwords:
            print(f"✅ Loaded {len(passwords)} passwords")
            self._all_passwords = passwords
        else:
            print(f"⚠️ No passwords found: {message}")
            self._all_passwords = []
        
        self.password_list.load_passwords(self._all_passwords)
        
        counts = {
            'all': len(self._all_passwords),
            'work': sum(1 for p in self._all_passwords if p.get('category') == 'work'),
            'personal': sum(1 for p in self._all_passwords if p.get('category') == 'personal'),
            'finance': sum(1 for p in self._all_passwords if p.get('category') == 'finance'),
            'game': sum(1 for p in self._all_passwords if p.get('category') == 'game'),
            'study': sum(1 for p in self._all_passwords if p.get('category') == 'study'),
            'favorites': sum(1 for p in self._all_passwords if p.get('favorite', False)),
        }
        self.sidebar.update_counts(counts)

    def on_category_changed(self, category):
        base = self._all_passwords
        if category == 'all':
            filtered = base
        elif category == 'favorites':
            filtered = [p for p in base if p.get('favorite')]
        else:
            filtered = [p for p in base if p.get('category') == category]
        self.password_list.load_passwords(filtered)

    def show_add_password_modal(self):
        dlg = AddPasswordModal(self)
        dlg.password_added.connect(self.on_password_added)
        dlg.exec_()

    def on_password_added(self, data):
        """Add password via API to database"""
        success, message, result = self.api_client.add_password(
            user_id=self.current_user['id'],
            site_name=data.get('site_name'),
            username=data.get('username'),
            password=data.get('password'),
            category=data.get('category'),
            favorite=False
        )
        
        if not success:
            QMessageBox.warning(self, "Erreur", f"Erreur: {message}")
            return
        
        print(f"✅ Password added successfully: {data.get('site_name')}")
        self.load_passwords()
        self.on_category_changed('all')
        QMessageBox.information(self, "Succès", "✅ Mot de passe enregistré avec succès!")

    def on_copy_password(self, password):
        QApplication.clipboard().setText(password)
        QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier!")

    def on_view_password(self, password_data):
        dlg = ViewPasswordModal(password_data, self)
        dlg.exec_()

    def on_edit_password(self, password_id: int):
        pwd = next((p for p in self.password_list.passwords if p.get('id') == password_id), None)
        if not pwd:
            QMessageBox.warning(self, "Erreur", "Mot de passe introuvable")
            return

        dlg = EditPasswordModal(pwd, self)

        def _apply_update(pid, new_pwd, last_mod):
            success, message, result = self.api_client.update_password(
                password_id=pid,
                site_name=pwd.get('site_name'),
                username=pwd.get('username'),
                password=new_pwd,
                category=pwd.get('category'),
                favorite=pwd.get('favorite', False)
            )
            
            if not success:
                QMessageBox.warning(self, "Erreur", message)
                return
            
            self.load_passwords()
            self.on_category_changed('all')
            QMessageBox.information(self, "Succès", "✅ Mot de passe mis à jour!")

        dlg.password_updated.connect(_apply_update)
        dlg.exec_()

    def on_delete_password(self, password_id):
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "⚠️ Êtes-vous sûr de vouloir supprimer ce mot de passe?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.api_client.delete_password(password_id)
            
            if not success:
                QMessageBox.warning(self, "Erreur", message)
                return
            
            self.load_passwords()
            self.on_category_changed('all')
            QMessageBox.information(self, "Succès", "✅ Mot de passe supprimé!")

    def on_favorite_password(self, password_id):
        pwd = next((p for p in self._all_passwords if p.get('id') == password_id), None)
        if pwd:
            new_favorite = not pwd.get('favorite', False)
            success, message, result = self.api_client.update_password(
                password_id=password_id,
                site_name=pwd.get('site_name'),
                username=pwd.get('username'),
                password=pwd.get('encrypted_password'),
                category=pwd.get('category'),
                favorite=new_favorite
            )
            
            if success:
                self.load_passwords()
                self.on_category_changed('all')

    def show_statistics_modal(self):
        from PyQt5.QtWidgets import QGridLayout
        
        stats_dialog = QDialog(self)
        stats_dialog.setWindowTitle("📊 Statistiques")
        stats_dialog.setFixedSize(700, 500)
        stats_dialog.setStyleSheet(f"""
            QDialog {{
                background: {Styles.PRIMARY_BG};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }}
        """)

        layout = QVBoxLayout(stats_dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("📊 Mes Statistiques")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(22))
        layout.addWidget(title)

        passwords = self._all_passwords
        total = len(passwords)
        strong = sum(1 for p in passwords if p.get('strength') == 'strong')
        medium = sum(1 for p in passwords if p.get('strength') == 'medium')
        weak = sum(1 for p in passwords if p.get('strength') == 'weak')
        favorites = sum(1 for p in passwords if p.get('favorite'))

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        stats_items = [
            ("📝 Total de comptes", total, Styles.BLUE_PRIMARY),
            ("✅ Mots de passe forts", strong, Styles.STRONG_COLOR),
            ("⚠️ Mots de passe moyens", medium, Styles.MEDIUM_COLOR),
            ("❌ Mots de passe faibles", weak, Styles.WEAK_COLOR),
            ("⭐ Comptes favoris", favorites, Styles.BLUE_SECONDARY),
        ]

        for i, (label, value, color) in enumerate(stats_items):
            label_widget = QLabel(label)
            label_widget.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
            
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
            
            grid.addWidget(label_widget, i, 0, alignment=Qt.AlignLeft)
            grid.addWidget(value_widget, i, 1, alignment=Qt.AlignRight)

        layout.addLayout(grid)

        if total > 0:
            security_score = int((strong / total) * 100)
            score_label = QLabel("🛡️ Score de sécurité")
            score_label.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
            layout.addWidget(score_label)

            score_value = QLabel(f"{security_score}%")
            score_color = Styles.STRONG_COLOR if security_score >= 80 else (Styles.MEDIUM_COLOR if security_score >= 50 else Styles.WEAK_COLOR)
            score_value.setStyleSheet(f"color: {score_color}; font-size: 18px; font-weight: bold;")
            layout.addWidget(score_value)

        layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(Styles.get_button_style(primary=True))
        close_btn.setMinimumHeight(44)
        close_btn.clicked.connect(stats_dialog.accept)
        layout.addWidget(close_btn)

        stats_dialog.exec_()

    def on_logout(self):
        reply = QMessageBox.question(
            self,
            "Déconnexion",
            "🚪 Voulez-vous vraiment vous déconnecter?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_user = None
            
            for i in reversed(range(self.user_profile_layout.count())):
                w = self.user_profile_layout.itemAt(i).widget()
                if w:
                    w.setParent(None)
            
            self._all_passwords = []
            self.password_list.load_passwords([])
            
            self.show_auth_flow()