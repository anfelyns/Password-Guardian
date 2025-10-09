# src/gui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QApplication, QMessageBox, QDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

from gui.components.sidebar import Sidebar
from gui.components.password_list import PasswordList
from gui.components.modals import (
    LoginModal, RegisterModal, AddPasswordModal,
    ViewPasswordModal, EditPasswordModal, TwoFactorModal
)
from gui.styles.styles import Styles

# Backend (MySQL + 2FA + API)
from auth.auth_manager import AuthManager
from backend.api_client import APIClient


# ------------------- User Profile -------------------
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
                    stop:0 #2563eb, stop:1 #7c3aed);
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
                background-color: #0f1e36;
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


# ------------------- Main Window -------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ---- Backend auth (MySQL @ port 1234, no password) ----
        self.auth = AuthManager(
            host='localhost', user='root', password='',
            database='password_guardian', port=1234
        )
        
        # ---- API Client for password operations ----
        self.api = APIClient(base_url='http://localhost:5000')

        self.current_user = None       # dict: id, username, email, name, initials
        self._all_passwords = []       # in-memory demo list
        self.init_ui()
        
        # Check API connection
        if not self.api.check_connection():
            QMessageBox.warning(
                self, 
                "⚠️ API Non Disponible",
                "Le serveur API n'est pas accessible.\n\n"
                "Assurez-vous que le serveur Flask est démarré:\n"
                "python backend_api/app.py\n\n"
                "L'application fonctionnera en mode démo."
            )
        
        self.show_auth_flow()

    # ---------- UI skeleton ----------
    def init_ui(self):
        self.setWindowTitle("SecureVault")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a1628,
                    stop:1 #1a2942
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
        wrap.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
            }
        """)
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
        
        # Shield icon
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size: 32px;")
        left.addWidget(icon)

        # SecureVault branding
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

    # ---------- Auth flow ----------
    def show_auth_flow(self):
        self.show_login_modal()

    def show_login_modal(self):
        dlg = LoginModal(self)
        dlg.login_success.connect(self.start_login_two_factor)  # email/username, password
        dlg.switch_to_register.connect(self.show_register_modal)
        if dlg.exec_() != QDialog.Accepted:
            QApplication.quit()

    def show_register_modal(self):
        dlg = RegisterModal(self)
        dlg.register_success.connect(self.start_register_two_factor)  # name, email, password
        dlg.switch_to_login.connect(self.show_login_modal)
        dlg.exec_()

    # Step 1: Login → send 2FA code
    def start_login_two_factor(self, username_or_email, password):
        ok, user_info, msg, meta = self.auth.authenticate(username_or_email, password)
        if not ok:
            QMessageBox.warning(self, "Erreur", msg)
            return

        if meta.get('requires_2fa'):
            # Step 2: open TwoFactorModal for code
            tf = TwoFactorModal(user_info['email'], "<code envoyé par email>", self)
            # we don't need to show the real code; the user checks email.
            def after_2fa():
                self.finalize_login(user_info)
            tf.code_verified.connect(lambda: self._verify_login_code_and_finalize(user_info, tf))
            tf.exec_()
        else:
            # fallback (should not happen with 2FA forced)
            self.finalize_login(user_info)

    def _verify_login_code_and_finalize(self, user_info, tf_dialog):
        """
        Called when user hits 'verify' in TwoFactorModal.
        We fetch the entered code from the modal and verify with backend.
        """
        # TwoFactorModal exposes self.code_input
        code_entered = tf_dialog.code_input.text().strip()
        ok, msg = self.auth.verify_two_factor(user_info['id'], code_entered, purpose='login', device_label="Desktop App")
        if not ok:
            QMessageBox.warning(self, "2FA", msg)
            return
        QMessageBox.information(self, "2FA", "Vérification réussie !")
        tf_dialog.accept()
        self.finalize_login(user_info)

    # Step 1: Register → weak replacement + send 2FA code
    def start_register_two_factor(self, name, email, password):
        ok, msg, extra = self.auth.register_user(name, email, password)
        if not ok:
            QMessageBox.warning(self, "Inscription", msg)
            return

        # Inform if we replaced a weak password
        if extra.get('replaced_weak') and extra.get('new_password'):
            QMessageBox.information(
                self, "Mot de passe renforcé",
                f"Votre mot de passe était faible.\n\nUn mot de passe fort a été généré :\n\n{extra['new_password']}\n\n"
                "Vous pourrez le modifier ensuite."
            )

        if not extra.get('two_factor_sent'):
            QMessageBox.warning(self, "Inscription", "Impossible d'envoyer le code de vérification par email.")
            return

        # Ask code for email verification (purpose='register')
        tf = TwoFactorModal(email, "<code envoyé par email>", self)

        def after_register_verified():
            # build minimal user_info and log straight in
            user_info = {
                'id': extra.get('user_id'),
                'username': name,
                'email': email
            }
            self.finalize_login(user_info)

        tf.code_verified.connect(lambda: self._verify_register_code_and_finalize(extra.get('user_id'), tf, after_register_verified))
        tf.exec_()

    def _verify_register_code_and_finalize(self, user_id, tf_dialog, on_ok_callback):
        code_entered = tf_dialog.code_input.text().strip()
        ok, msg = self.auth.verify_two_factor(user_id, code_entered, purpose='register')
        if not ok:
            QMessageBox.warning(self, "Vérification email", msg)
            return
        QMessageBox.information(self, "Vérification email", "Adresse vérifiée avec succès !")
        tf_dialog.accept()
        on_ok_callback()

    # Finalize session/UX after successful login or register+verify
    def finalize_login(self, user_info: dict):
        # Prepare header profile
        name = (user_info.get('username') or user_info.get('email', '').split('@')[0] or "User").capitalize()
        initials = (name[:2] or "US").upper()

        # Clear previous widget if any
        for i in reversed(range(self.user_profile_layout.count())):
            w = self.user_profile_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.current_user = {
            'id': user_info.get('id'),
            'username': user_info.get('username') or name,
            'email': user_info.get('email'),
            'name': name,
            'initials': initials
        }

        self.user_profile = UserProfileWidget(self.current_user['name'], self.current_user['initials'], self)
        self.user_profile.logout_clicked.connect(self.on_logout)
        self.user_profile.show_statistics.connect(self.show_statistics_modal)
        self.user_profile_layout.addWidget(self.user_profile)

        self.load_passwords()
        QMessageBox.information(self, "Connexion", f"Bienvenue {self.current_user['name']} !")

    # ---------- Data & filters ----------
    def load_passwords(self):
        """Load passwords from API or use demo data"""
        if not self.current_user:
            return
        
        user_id = self.current_user.get('id')
        
        # Try to load from API
        success, message, passwords = self.api.get_passwords(user_id)
        
        if success and passwords:
            # Transform API data to match UI format
            demo = []
            for p in passwords:
                demo.append({
                    'id': p['id'],
                    'site_name': p['site_name'],
                    'site_icon': self.get_icon_for_site(p['site_name']),
                    'username': p['username'],
                    'encrypted_password': p.get('password_display', '•••••••'),
                    'category': p['category'],
                    'strength': p['strength'],
                    'favorite': bool(p.get('favorite', False)),
                    'last_modified': p.get('last_updated', 'Aujourd\'hui')
                })
            
            self._all_passwords = demo
            self.password_list.load_passwords(demo)
        else:
            # Fallback to demo data
            demo = [
                {'id': 1, 'site_name': 'Gmail',   'site_icon': '📧', 'username': 'john@gmail.com',
                 'encrypted_password': '•••••••', 'category': 'personal', 'strength': 'strong',
                 'favorite': True,  'last_modified': 'Maj. 04/10/2025 20:00'},
                {'id': 2, 'site_name': 'GitHub',  'site_icon': '💻', 'username': 'johndev',
                 'encrypted_password': '•••••••',    'category': 'work',     'strength': 'strong',
                 'favorite': False, 'last_modified': 'Maj. 04/10/2025 20:00'},
                {'id': 3, 'site_name': 'Netflix', 'site_icon': '🎬', 'username': 'john@email.com',
                 'encrypted_password': '•••••••',     'category': 'personal', 'strength': 'medium',
                 'favorite': True,  'last_modified': 'Maj. 04/10/2025 20:00'},
                {'id': 4, 'site_name': 'PayPal',  'site_icon': '💳', 'username': 'john@paypal.com',
                 'encrypted_password': '•••••••',  'category': 'finance',  'strength': 'weak',
                 'favorite': False, 'last_modified': 'Maj. 04/10/2025 20:00'},
            ]
            self._all_passwords = demo
            self.password_list.load_passwords(demo)

        # Update counts
        passwords = self._all_passwords
        counts = {
            'all': len(passwords),
            'work':     sum(1 for p in passwords if p['category'] == 'work'),
            'personal': sum(1 for p in passwords if p['category'] == 'personal'),
            'finance':  sum(1 for p in passwords if p['category'] == 'finance'),
            'favorites':sum(1 for p in passwords if p.get('favorite', False)),
        }
        self.sidebar.update_counts(counts)
    
    def get_icon_for_site(self, site_name):
        """Get emoji icon based on site name"""
        site_lower = site_name.lower()
        icons = {
            'gmail': '📧', 'email': '📧', 'mail': '📧',
            'github': '💻', 'gitlab': '💻', 'code': '💻',
            'netflix': '🎬', 'youtube': '🎬', 'video': '🎬',
            'paypal': '💳', 'bank': '💳', 'card': '💳',
            'facebook': '📘', 'twitter': '🐦', 'instagram': '📷',
            'amazon': '🛒', 'shop': '🛒',
            'game': '🎮', 'steam': '🎮',
        }
        
        for key, icon in icons.items():
            if key in site_lower:
                return icon
        
        return '🔒'  # Default iconencrypted_password': 'SecurePass123!', 'category': 'personal', 'strength': 'strong',
             'favorite': True,  'last_modified': 'Maj. 04/10/2025 20:00'},
            {'id': 2, 'site_name': 'GitHub',  'site_icon': '💻', 'username': 'johndev',
             'encrypted_password': 'GitHub456#',    'category': 'work',     'strength': 'strong',
             'favorite': False, 'last_modified': 'Maj. 04/10/2025 20:00'},
            {'id': 3, 'site_name': 'Netflix', 'site_icon': '🎬', 'username': 'john@email.com',
             'encrypted_password': 'Netflix789',     'category': 'personal', 'strength': 'medium',
             'favorite': True,  'last_modified': 'Maj. 04/10/2025 20:00'},
            {'id': 4, 'site_name': 'PayPal',  'site_icon': '💳', 'username': 'john@paypal.com',
             'encrypted_password': 'PayPal$Secure',  'category': 'finance',  'strength': 'weak',
             'favorite': False, 'last_modified': 'Maj. 04/10/2025 20:00'},
        ]
        self._all_passwords = demo[:]
        
        # Make sure to load into password list
        self.password_list.load_passwords(demo)

        counts = {
            'all': len(demo),
            'work':     sum(1 for p in demo if p['category'] == 'work'),
            'personal': sum(1 for p in demo if p['category'] == 'personal'),
            'finance':  sum(1 for p in demo if p['category'] == 'finance'),
            'favorites':sum(1 for p in demo if p.get('favorite', False)),
        }
        self.sidebar.update_counts(counts)

    def on_category_changed(self, category):
        base = self._all_passwords or self.password_list.passwords
        if category == 'all':
            filtered = base
        elif category == 'favorites':
            filtered = [p for p in base if p.get('favorite')]
        else:
            filtered = [p for p in base if p.get('category') == category]
        self.password_list.load_passwords(filtered)

    # ---------- CRUD actions ----------
    def show_add_password_modal(self):
        dlg = AddPasswordModal(self)
        dlg.password_added.connect(self.on_password_added)
        dlg.exec_()

    def on_password_added(self, data):
        """Handle password addition via API"""
        if not self.current_user:
            return
        
        user_id = self.current_user.get('id')
        
        # Map category names
        category_map = {
            'personnel': 'personal',
            'travail': 'work',
            'finance': 'finance',
            'jeux': 'game',
            'étude': 'study',
            'autre': 'personal'
        }
        
        category = category_map.get(data.get('category', 'personal').lower(), 'personal')
        
        # Add via API
        success, message, response = self.api.add_password(
            user_id=user_id,
            site_name=data['site_name'],
            username=data['username'],
            password=data['password'],
            category=category,
            favorite=data.get('favorite', False)
        )
        
        if success:
            # Check if password was weak
            if response and 'suggestion' in response:
                QMessageBox.warning(
                    self, 
                    "⚠️ Mot de passe faible",
                    f"Votre mot de passe est faible !\n\n"
                    f"Suggestion de mot de passe fort :\n{response['suggestion']}\n\n"
                    f"Voulez-vous l'utiliser à la place ?"
                )
            else:
                QMessageBox.information(self, "Succès", "Mot de passe ajouté avec succès !")
            
            self.load_passwords()
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible d'ajouter le mot de passe:\n{message}")

    def on_copy_password(self, password):
        """Copy password to clipboard - reveal from API if needed"""
        QApplication.clipboard().setText(password)
        QMessageBox.information(self, "Copié", "Mot de passe copié dans le presse-papier !")

    def on_view_password(self, password_data):
        """View password - reveal actual password from API"""
        # If password is hidden (•••••••), reveal it
        if password_data.get('encrypted_password') == '•••••••':
            success, message, real_password = self.api.reveal_password(password_data['id'])
            if success and real_password:
                password_data['encrypted_password'] = real_password
            else:
                QMessageBox.warning(self, "Erreur", f"Impossible de révéler le mot de passe:\n{message}")
                return
        
        dlg = ViewPasswordModal(password_data, self)
        dlg.exec_()

    def on_edit_password(self, password_id: int):
        """Edit password via API"""
        pwd = next((p for p in self.password_list.passwords if p.get('id') == password_id), None)
        if not pwd:
            QMessageBox.warning(self, "Introuvable", "Mot de passe introuvable.")
            return

        # Reveal password before editing
        success, message, real_password = self.api.reveal_password(password_id)
        if success and real_password:
            pwd['encrypted_password'] = real_password
        
        dlg = EditPasswordModal(pwd, self)

        def _apply_update(pid, new_pwd, last_mod):
            # Map category
            category_map = {
                'personnel': 'personal',
                'travail': 'work',
                'finance': 'finance',
                'jeux': 'game',
                'étude': 'study',
                'autre': 'personal'
            }
            
            category = category_map.get(pwd.get('category', 'personal').lower(), 'personal')
            
            # Update via API
            success, msg, response = self.api.update_password(
                password_id=pid,
                site_name=pwd['site_name'],
                username=pwd['username'],
                password=new_pwd,
                category=category,
                favorite=pwd.get('favorite', False)
            )
            
            if success:
                QMessageBox.information(self, "Mis à jour", "Mot de passe mis à jour avec succès !")
                self.load_passwords()
            else:
                QMessageBox.warning(self, "Erreur", f"Impossible de mettre à jour:\n{msg}")

        dlg.password_updated.connect(_apply_update)
        dlg.exec_()

    def on_delete_password(self, password_id):
        """Delete password via API"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Êtes-vous sûr de vouloir supprimer ce mot de passe ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.api.delete_password(password_id)
            
            if success:
                QMessageBox.information(self, "Supprimé", "Mot de passe supprimé avec succès !")
                self.load_passwords()
            else:
                QMessageBox.warning(self, "Erreur", f"Impossible de supprimer:\n{message}")

    def on_favorite_password(self, password_id):
        """Toggle favorite status"""
        pwd = next((p for p in self.password_list.passwords if p.get('id') == password_id), None)
        if not pwd:
            return
        
        # Toggle favorite
        pwd['favorite'] = not pwd.get('favorite', False)
        
        # Update via API
        category_map = {
            'personnel': 'personal',
            'travail': 'work',
            'finance': 'finance',
            'jeux': 'game',
            'étude': 'study',
            'autre': 'personal'
        }
        
        category = category_map.get(pwd.get('category', 'personal').lower(), 'personal')
        
        # Get real password first
        success, msg, real_pwd = self.api.reveal_password(password_id)
        if not success:
            QMessageBox.warning(self, "Erreur", "Impossible de modifier le favori")
            return
        
        success, message, _ = self.api.update_password(
            password_id=password_id,
            site_name=pwd['site_name'],
            username=pwd['username'],
            password=real_pwd,
            category=category,
            favorite=pwd['favorite']
        )
        
        if success:
            QMessageBox.information(self, "Favori", "État favori modifié !")
            self.load_passwords()
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible de modifier:\n{message}")

    # ---------- Stats modal with graph ----------
    def show_statistics_modal(self):
        from PyQt5.QtWidgets import QGridLayout, QSizePolicy
        stats_dialog = QDialog(self)
        stats_dialog.setWindowTitle("📊 Statistiques")
        stats_dialog.setFixedSize(640, 440)
        stats_dialog.setStyleSheet(f"""
            QDialog {{
                background: {Styles.PRIMARY_BG};
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }}
        """)

        layout = QVBoxLayout(stats_dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("📊 Vos Statistiques")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(22))
        layout.addWidget(title)

        passwords = self.password_list.passwords
        total = len(passwords)
        strong = sum(1 for p in passwords if p.get('strength') == 'strong')
        medium = sum(1 for p in passwords if p.get('strength') == 'medium')
        weak = sum(1 for p in passwords if p.get('strength') == 'weak')

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(10)
        items = [("🔐 Total", total), ("✅ Forts", strong), ("⚠️ Moyens", medium), ("❌ Faibles", weak)]
        for i, (lbl, val) in enumerate(items):
            l = QLabel(lbl)
            l.setStyleSheet(Styles.get_label_style(14, Styles.TEXT_SECONDARY))
            v = QLabel(str(val))
            v.setStyleSheet(Styles.get_label_style(18, Styles.BLUE_PRIMARY))
            grid.addWidget(l, 0, i)
            grid.addWidget(v, 1, i)
        layout.addLayout(grid)

        # Graph
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            fig = Figure(figsize=(5.6, 2.6))
            ax = fig.add_subplot(111)
            labels = ["Forts", "Moyens", "Faibles"]
            values = [strong, medium, weak]
            colors = [Styles.STRONG_COLOR, Styles.MEDIUM_COLOR, Styles.WEAK_COLOR]
            ax.bar(labels, values, color=colors)
            ax.set_facecolor("#0f1e36")
            fig.patch.set_facecolor("#0a1628")
            ax.tick_params(axis='x', colors=Styles.TEXT_PRIMARY)
            ax.tick_params(axis='y', colors=Styles.TEXT_SECONDARY)
            for spine in ax.spines.values():
                spine.set_color("#1f2b40")
            ax.set_ylabel("Comptes", color=Styles.TEXT_SECONDARY)
            canvas = FigureCanvas(fig)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(canvas)
        except Exception:
            # Fallback simple bars
            bar_wrap = QWidget()
            bl = QHBoxLayout(bar_wrap)
            bl.setSpacing(12)

            def bar(color, value, label):
                cont = QVBoxLayout()
                cont.setSpacing(6)
                barbg = QFrame()
                barbg.setFixedSize(160, 120)
                barbg.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 10px;")
                barinner = QFrame()
                barinner.setStyleSheet(f"background: {color}; border-radius: 8px;")
                inner = QVBoxLayout(barbg)
                inner.setContentsMargins(6, 6, 6, 6)
                inner.addStretch()
                fill = max(6, int(100 * (value / max(1, total))))
                barinner.setFixedHeight(fill)
                inner.addWidget(barinner)
                lab = QLabel(f"{label} ({value})")
                lab.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_SECONDARY))
                lab.setAlignment(Qt.AlignCenter)
                cont.addWidget(barbg)
                cont.addWidget(lab)
                w = QWidget()
                w.setLayout(cont)
                return w

            bl.addWidget(bar(Styles.STRONG_COLOR, strong, "Forts"))
            bl.addWidget(bar(Styles.MEDIUM_COLOR, medium, "Moyens"))
            bl.addWidget(bar(Styles.WEAK_COLOR, weak, "Faibles"))
            layout.addWidget(bar_wrap)

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(Styles.get_button_style(primary=True))
        close_btn.setMinimumHeight(44)
        close_btn.clicked.connect(stats_dialog.accept)
        layout.addWidget(close_btn)

        stats_dialog.exec_()

    # ---------- Logout ----------
    def on_logout(self):
        if QMessageBox.question(self, "Déconnexion", "Voulez-vous vraiment vous déconnecter ?") == QMessageBox.Yes:
            self.current_user = None
            for i in reversed(range(self.user_profile_layout.count())):
                w = self.user_profile_layout.itemAt(i).widget()
                if w:
                    w.setParent(None)
            self.show_auth_flow()