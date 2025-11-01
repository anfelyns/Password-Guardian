# src/gui/main_window.py - FIXED IMPORTS

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QApplication, QMessageBox, QDialog, QMenu, QAction,
    QLineEdit, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# ✅ FIXED: Changed all imports to use src. prefix
from src.gui.components.sidebar import Sidebar
from src.gui.components.password_list import PasswordList
from src.gui.components.modals import (
    LoginModal, RegisterModal, AddPasswordModal,
    ViewPasswordModal, EditPasswordModal, TwoFactorModal
)
from src.gui.styles.styles import Styles
from src.auth.auth_manager import AuthManager
from src.backend.api_client import APIClient


class Quick2FADialog(QDialog):
    """Quick 2FA dialog for sensitive operations"""
    code_verified = pyqtSignal()
    
    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.email = email
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🔐 Vérification 2FA")
        self.setFixedSize(420, 300)
        self.setModal(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }}
            QLabel {{ color: {Styles.TEXT_PRIMARY}; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)
        
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size: 48px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("Vérification de sécurité")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {Styles.TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QLabel(f"Code envoyé à:\n{self.email}")
        info.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 13px;")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code à 6 chiffres")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.setFont(QFont("Courier New", 18, QFont.Bold))
        self.code_input.setStyleSheet(f"""
            QLineEdit {{
                {Styles.get_input_style()}
                padding: 12px;
                font-size: 20px;
                letter-spacing: 8px;
            }}
        """)
        self.code_input.returnPressed.connect(self.code_verified.emit)
        layout.addWidget(self.code_input)
        
        verify_btn = QPushButton("✅ Vérifier")
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setMinimumHeight(48)
        verify_btn.clicked.connect(self.code_verified.emit)
        verify_btn.setStyleSheet(Styles.get_button_style(primary=True))
        layout.addWidget(verify_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(Styles.get_button_style(primary=False))
        layout.addWidget(cancel_btn)
        
        self.code_input.setFocus()


class UserProfileWidget(QWidget):
    logout_clicked = pyqtSignal()
    show_statistics = pyqtSignal()
    edit_profile_clicked = pyqtSignal()  # ✅ NEW

    def __init__(self, username, initials, parent=None):
        super().__init__(parent)
        self.username = username
        self.initials = initials
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.avatar = QPushButton(self.initials)
        self.avatar.setFixedSize(40, 40)
        self.avatar.setCursor(Qt.PointingHandCursor)
        self.avatar.clicked.connect(self._menu)
        self.avatar.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.PURPLE});
                border-radius: 20px; color:white; font-weight:bold;
            }}
        """)
        lay.addWidget(self.avatar)

        self.name_btn = QPushButton(self.username)
        self.name_btn.setCursor(Qt.PointingHandCursor)
        self.name_btn.clicked.connect(self._menu)
        self.name_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{Styles.TEXT_PRIMARY};
                          border:none; font-size:14px; }}
            QPushButton:hover {{ color:{Styles.BLUE_SECONDARY}; }}
        """)
        lay.addWidget(self.name_btn)

    def _menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{background:#0f1e36; border:1px solid rgba(255,255,255,0.2);
                    border-radius:10px; padding:10px; }}
            QMenu::item {{padding:8px 15px; border-radius:8px; color:{Styles.TEXT_PRIMARY};}}
            QMenu::item:selected {{background:rgba(59,130,246,0.25); }}
        """)
        
        # Header
        head = QAction(f"👋 {self.username}", self)
        head.setEnabled(False)
        menu.addAction(head)
        menu.addSeparator()
        
        # ✅ NEW: Edit Profile
        act_edit = QAction("✏️ Modifier le profil", self)
        act_edit.triggered.connect(self.edit_profile_clicked.emit)
        menu.addAction(act_edit)
        
        # Statistics
        act_stats = QAction("📊 Mes statistiques", self)
        act_stats.triggered.connect(self.show_statistics.emit)
        menu.addAction(act_stats)
        
        menu.addSeparator()
        
        # Logout
        act_logout = QAction("🚪 Se déconnecter", self)
        act_logout.triggered.connect(self.logout_clicked.emit)
        menu.addAction(act_logout)
        
        menu.exec_(self.mapToGlobal(self.rect().bottomRight()))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth = AuthManager(
            host="localhost", user="root", password="inessouai2005_",
            database="password_guardian", port=3306
        )
        self.api_client = APIClient("http://localhost:5000")
        self.current_user = None
        self._all_passwords = []
        self._init_ui()
        self.show_auth_flow()

    def _init_ui(self):
        self.setWindowTitle("Password Guardian")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0a1628, stop:1 #1a2942);
            }
        """)
        c = QWidget()
        self.setCentralWidget(c)
        main = QVBoxLayout(c)
        main.setContentsMargins(20, 20, 20, 20)

        # Header
        h = QWidget()
        h_lay = QHBoxLayout(h)
        ico = QLabel("🛡️")
        ico.setStyleSheet("font-size:32px;")
        title = QLabel("Password Guardian")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        h_lay.addWidget(ico)
        h_lay.addWidget(title)
        h_lay.addStretch()
        
        self.user_box = QHBoxLayout()
        self.user_widget = QWidget()
        self.user_widget.setLayout(self.user_box)
        h_lay.addWidget(self.user_widget)
        main.addWidget(h)

        # Body
        body = QHBoxLayout()
        self.sidebar = Sidebar()
        self.sidebar.category_changed.connect(self.on_category_changed)
        self.sidebar.add_password_clicked.connect(self.show_add_password_modal)
        body.addWidget(self.sidebar)

        self.password_list = PasswordList()
        # NEW: Connect 2FA signals
        self.password_list.request_2fa_for_copy.connect(self.handle_2fa_copy_request)
        self.password_list.request_2fa_for_view.connect(self.handle_2fa_view_request)
        # Other signals
        self.password_list.edit_password.connect(self.on_edit_password)
        self.password_list.delete_password.connect(self.on_delete_password)
        self.password_list.favorite_password.connect(self.on_favorite_password)
        if hasattr(self.password_list, 'restore_password'):
            self.password_list.restore_password.connect(self.on_restore_password)

        frame = QFrame()
        f_lay = QVBoxLayout(frame)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.addWidget(self.password_list)
        body.addWidget(frame, 1)
        main.addLayout(body)

    # ==================== AUTHENTICATION ====================
    
    def show_auth_flow(self):
        dlg = LoginModal(self)
        dlg.login_success.connect(self.on_login_attempt)
        dlg.switch_to_register.connect(self._switch_to_register)
        res = dlg.exec_()
        if res != QDialog.Accepted and not self.current_user:
            QApplication.quit()

    def _switch_to_register(self):
        dlg = RegisterModal(self)
        dlg.register_success.connect(self.on_register_attempt)
        dlg.switch_to_login.connect(self.show_auth_flow)
        dlg.exec_()

    def on_login_attempt(self, email, password):
        print(f"🔐 Login attempt: {email}")
        result = self.auth.authenticate(email, password)
        if result.get("error"):
            QMessageBox.warning(self, "Erreur", result["error"])
            return
        if not result.get("2fa_sent"):
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le code 2FA")
            return
        user = result.get("user")
        self._show_2fa(user)

    def _show_2fa(self, user):
        dlg = TwoFactorModal(user["email"], "<code envoyé>", self)
        
        def verify():
            code = dlg.code_input.text().strip()
            if not code or len(code) != 6:
                QMessageBox.warning(self, "Code invalide", "Code 6 chiffres requis")
                return
            if self.auth.verify_2fa_email(user["email"], code):
                dlg.accept()
                self.finalize_login(user)
            else:
                QMessageBox.warning(self, "Erreur", "Code invalide ou expiré")
        
        try:
            dlg.code_verified.disconnect()
        except:
            pass
        dlg.code_verified.connect(verify)
        
        if dlg.exec_() != QDialog.Accepted:
            self.show_auth_flow()

    def on_register_attempt(self, name, email, password):
        ok, msg, extra = self.auth.register_user(name, email, password)
        if not ok:
            QMessageBox.warning(self, "Inscription", msg)
            return
        QMessageBox.information(self, "Succès", "✅ Vérifiez votre email")
        self.show_auth_flow()

    def finalize_login(self, user):
        name = (user.get("username") or user.get("email", "").split("@")[0]).capitalize()
        initials = (name[:2] or "US").upper()
        
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)
        
        self.current_user = {
            "id": user["id"],
            "username": name,
            "email": user["email"],
            "name": name,
            "initials": initials
        }
        
        prof = UserProfileWidget(name, initials, self)
        prof.logout_clicked.connect(self.on_logout)
        prof.show_statistics.connect(self.show_statistics_modal)
        prof.edit_profile_clicked.connect(self.show_edit_profile_modal)  # ✅ NEW
        self.user_box.addWidget(prof)
        
        self.load_passwords()
        QMessageBox.information(self, "Bienvenue", f"✅ Bienvenue {name}!")

    # ==================== 2FA HANDLERS ====================
    
    def handle_2fa_copy_request(self, encrypted_password):
        """Handle copy with 2FA"""
        if not self.current_user:
            QMessageBox.warning(self, "Erreur", "Non connecté")
            return
        
        email = self.current_user["email"]
        user_id = self.current_user.get("id")
        
        # Send 2FA code
        code_sent = self.auth.send_2fa_code(
            to_email=email,
            user_id=user_id,
            purpose="sensitive_action"
        )
        
        if not code_sent:
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le code 2FA")
            return
        
        # Show 2FA dialog
        dlg = Quick2FADialog(email, self)
        
        def on_verify():
            code = dlg.code_input.text().strip()
            if not code or len(code) != 6:
                QMessageBox.warning(self, "Code invalide", "Code 6 chiffres requis")
                return
            
            if self.auth.verify_2fa(email, code):
                dlg.accept()
                # Decrypt and copy
                try:
                    decrypted = self.api_client.decrypt_password(encrypted_password)
                    if decrypted:
                        QApplication.clipboard().setText(decrypted)
                        QMessageBox.information(self, "Copié", "📋 Mot de passe copié!")
                    else:
                        QMessageBox.warning(self, "Erreur", "Déchiffrement échoué")
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Déchiffrement: {str(e)}")
            else:
                QMessageBox.warning(self, "Erreur", "Code invalide ou expiré")
        
        try:
            dlg.code_verified.disconnect()
        except:
            pass
        dlg.code_verified.connect(on_verify)
        dlg.exec_()

    def handle_2fa_view_request(self, password_data):
        """Handle view with 2FA - FIXED to show decrypted password"""
        if not self.current_user:
            QMessageBox.warning(self, "Erreur", "Non connecté")
            return
        
        email = self.current_user["email"]
        user_id = self.current_user.get("id")
        
        # Send 2FA code
        code_sent = self.auth.send_2fa_code(
            to_email=email,
            user_id=user_id,
            purpose="sensitive_action"
        )
        
        if not code_sent:
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer code")
            return
        
        # Show 2FA dialog
        dlg = Quick2FADialog(email, self)
        
        def on_verify():
            code = dlg.code_input.text().strip()
            if not code or len(code) != 6:
                QMessageBox.warning(self, "Code invalide", "Code 6 chiffres requis")
                return
            
            if self.auth.verify_2fa(email, code):
                dlg.accept()
                # Decrypt password before showing
                try:
                    encrypted = password_data.get('encrypted_password', '')
                    if not encrypted:
                        QMessageBox.warning(self, "Erreur", "Mot de passe introuvable")
                        return
                        
                    print(f"🔐 Déchiffrement du mot de passe...")
                    
                    # Pass both password_data AND api_client to ViewPasswordModal
                    ViewPasswordModal(
                        password_data=password_data,
                        api_client=self.api_client,  # Let modal handle decryption
                        parent=self
                    ).exec_()
                        
                except Exception as e:
                    print(f"❌ Erreur de déchiffrement: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.warning(self, "Erreur", f"Déchiffrement: {str(e)}")
            else:
                QMessageBox.warning(self, "Erreur", "Code 2FA invalide")
        
        try:
            dlg.code_verified.disconnect()
        except:
            pass
    
        dlg.code_verified.connect(on_verify)
        dlg.exec_()

    # ==================== PASSWORD MANAGEMENT ====================
    
    def load_passwords(self):
        if not self.current_user:
            return
        
        ok, msg, pwds = self.api_client.get_passwords(self.current_user["id"])
        self._all_passwords = pwds if ok else []
        
        # Filter out trash for default view
        visible_pwds = [p for p in self._all_passwords if p.get('category') != 'trash']
        self.password_list.load_passwords(visible_pwds)
        
        # Update counts
        counts = {k: 0 for k in ["all", "work", "personal", "finance", "game", "study", "favorites", "trash"]}
        counts["all"] = len([p for p in self._all_passwords if p.get('category') != 'trash'])
        counts["trash"] = len([p for p in self._all_passwords if p.get('category') == 'trash'])
        
        for p in self._all_passwords:
            c = p.get("category")
            if c != 'trash' and c in counts:
                counts[c] += 1
            if p.get("favorite") and c != 'trash':
                counts["favorites"] += 1
        
        self.sidebar.update_counts(counts)

    def on_category_changed(self, cat):
        base = self._all_passwords
        if cat == "all":
            f = [p for p in base if p.get('category') != 'trash']
        elif cat == "trash":
            f = [p for p in base if p.get('category') == 'trash']
        elif cat == "favorites":
            f = [p for p in base if p.get("favorite") and p.get('category') != 'trash']
        else:
            f = [p for p in base if p.get("category") == cat]
        self.password_list.load_passwords(f)

    def show_add_password_modal(self):
        dlg = AddPasswordModal(self)
        dlg.password_added.connect(self.on_password_added)
        dlg.exec_()

    def on_password_added(self, data):
        ok, msg, _ = self.api_client.add_password(
            user_id=self.current_user["id"],
            site_name=data["site_name"],
            username=data["username"],
            password=data["password"],
            category=data["category"],
            favorite=False
        )
        if not ok:
            QMessageBox.warning(self, "Erreur", msg)
            return
        self.load_passwords()
        QMessageBox.information(self, "Succès", "Mot de passe ajouté")

    def on_edit_password(self, pid):
        pwd = next((p for p in self._all_passwords if p["id"] == pid), None)
        if not pwd:
            QMessageBox.warning(self, "Erreur", "Introuvable")
            return
        
        # Decrypt password first
        try:
            encrypted = pwd.get('encrypted_password', '')
            decrypted = self.api_client.decrypt_password(encrypted)
            if decrypted:
                pwd_copy = pwd.copy()
                pwd_copy['encrypted_password'] = decrypted
                pwd_copy['password'] = decrypted
            else:
                pwd_copy = pwd
        except:
            pwd_copy = pwd
        
        dlg = EditPasswordModal(pwd_copy, self)
        
        def upd(pid, new_password, _):
            # Encrypt new password before saving
            try:
                encrypted_new = self.api_client.encrypt_password(new_password)
                ok, msg, _ = self.api_client.update_password(
                    pid, pwd["site_name"], pwd["username"],
                    encrypted_new, pwd["category"], pwd.get("favorite", False)
                )
                if ok:
                    self.load_passwords()
                    QMessageBox.information(self, "Succès", "Mis à jour")
                else:
                    QMessageBox.warning(self, "Erreur", msg)
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Encryption: {str(e)}")
        
        dlg.password_updated.connect(upd)
        dlg.exec_()

    def on_delete_password(self, pid: int):
        """Delete with trash system"""
        pwd = next((p for p in self._all_passwords if p.get("id") == pid), None)
        if not pwd:
            return
        
        cat = pwd.get("category", "").lower()
        
        if cat == "trash":
            # Permanent delete
            rep = QMessageBox.question(
                self, "Suppression définitive",
                "⚠️ Supprimer définitivement?\nCette action est irréversible.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if rep != QMessageBox.Yes:
                return
            
            ok, msg = self.api_client.delete_password(pid, hard=True)
            if not ok:
                QMessageBox.warning(self, "Erreur", msg)
                return
            
            self.load_passwords()
            QMessageBox.information(self, "Supprimé", "🗑️ Supprimé définitivement")
        else:
            # Move to trash
            rep = QMessageBox.question(
                self, "Corbeille",
                "Déplacer vers la corbeille?\n(Suppression auto après 48h)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if rep != QMessageBox.Yes:
                return
            
            ok, msg, _ = self.api_client.update_password(
                pid, pwd["site_name"], pwd["username"],
                pwd["encrypted_password"], "trash", pwd.get("favorite", False)
            )
            if not ok:
                QMessageBox.warning(self, "Erreur", msg)
                return
            
            self.load_passwords()
            QMessageBox.information(self, "Corbeille", "♻️ Déplacé vers la corbeille")

    def on_restore_password(self, pid):
        """Restore from trash"""
        rep = QMessageBox.question(
            self, "Restaurer",
            "Restaurer ce mot de passe?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if rep != QMessageBox.Yes:
            return
        
        pwd = next((p for p in self._all_passwords if p.get("id") == pid), None)
        if not pwd:
            return
        
        ok, msg, _ = self.api_client.update_password(
            pid, pwd["site_name"], pwd["username"],
            pwd["encrypted_password"], "personal", pwd.get("favorite", False)
        )
        if not ok:
            QMessageBox.warning(self, "Erreur", msg)
            return
        
        self.load_passwords()
        QMessageBox.information(self, "Restauré", "✅ Restauré avec succès")

    def on_favorite_password(self, pid):
        p = next((x for x in self._all_passwords if x["id"] == pid), None)
        if not p:
            return
        
        fav = not p.get("favorite", False)
        ok, msg, _ = self.api_client.update_password(
            pid, p["site_name"], p["username"],
            p["encrypted_password"], p["category"], fav
        )
        if ok:
            self.load_passwords()
        else:
            QMessageBox.warning(self, "Erreur", msg)

    # ==================== STATISTICS & LOGOUT ====================
    
    def show_statistics_modal(self):
        d = QDialog(self)
        d.setWindowTitle("📊 Statistiques")
        d.setFixedSize(720, 520)
        d.setAttribute(Qt.WA_StyledBackground, True)
        d.setStyleSheet(f"""
            QDialog {{
                background: {Styles.PRIMARY_BG};
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }}
            QLabel {{ color: {Styles.TEXT_PRIMARY}; background: transparent; }}
            QPushButton {{ {Styles.get_button_style(primary=True)} min-height: 44px; }}
        """)

        layout = QVBoxLayout(d)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("📊 Mes statistiques")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        layout.addWidget(title)

        passwords = [p for p in self._all_passwords if p.get('category') != 'trash']
        total = len(passwords)
        strong = sum(1 for p in passwords if p.get('strength') == 'strong')
        medium = sum(1 for p in passwords if p.get('strength') == 'medium')
        weak = sum(1 for p in passwords if p.get('strength') == 'weak')
        favorites = sum(1 for p in passwords if p.get('favorite'))

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)

        def row(label_text, value_text, color):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 15px;")
            val = QLabel(str(value_text))
            val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 700;")
            return lbl, val

        r = 0
        for text, val, col in [
            ("🗂️ Total", total, Styles.BLUE_PRIMARY),
            ("✅ Forts", strong, Styles.STRONG_COLOR),
            ("⚠️ Moyens", medium, Styles.MEDIUM_COLOR),
            ("❌ Faibles", weak, Styles.WEAK_COLOR),
            ("⭐ Favoris", favorites, Styles.BLUE_SECONDARY),
        ]:
            l, v = row(text, val, col)
            grid.addWidget(l, r, 0, alignment=Qt.AlignLeft)
            grid.addWidget(v, r, 1, alignment=Qt.AlignRight)
            r += 1

        layout.addLayout(grid)

        score_wrap = QWidget()
        score_wrap.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }
        """)
        swl = QHBoxLayout(score_wrap)
        swl.setContentsMargins(14, 10, 14, 10)

        score_label = QLabel("🛡️ Score de sécurité")
        score_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        swl.addWidget(score_label, alignment=Qt.AlignLeft)

        security_score = int((strong / total) * 100) if total > 0 else 0
        score_color = Styles.STRONG_COLOR if security_score >= 80 else (
            Styles.MEDIUM_COLOR if security_score >= 50 else Styles.WEAK_COLOR
        )

        score_value = QLabel(f"{security_score}%")
        score_value.setStyleSheet(f"color: {score_color}; font-size: 26px; font-weight: 800;")
        swl.addWidget(score_value, alignment=Qt.AlignRight)

        layout.addWidget(score_wrap)
        layout.addStretch(1)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(d.accept)
        layout.addWidget(close_btn)

        d.exec_()

    def on_logout(self):
        rep = QMessageBox.question(
            self, "Déconnexion", "Se déconnecter?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        
        self.current_user = None
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)
        
        self._all_passwords = []
        self.password_list.load_passwords([])
        self.show_auth_flow()

    # New: show edit profile modal + handlers
    def show_edit_profile_modal(self):
        """Show edit profile dialog"""
        from src.gui.components.modals import EditProfileModal
        
        dlg = EditProfileModal(self.current_user, self.auth, self)
        
        def on_profile_updated(updated_data):
            # Update current user
            self.current_user['username'] = updated_data['username']
            self.current_user['name'] = updated_data['username']
            self.current_user['initials'] = (updated_data['username'][:2] or "US").upper()
            
            # Refresh profile widget
            for i in reversed(range(self.user_box.count())):
                w = self.user_box.itemAt(i).widget()
                if w:
                    w.setParent(None)
            
            prof = UserProfileWidget(
                self.current_user['username'], 
                self.current_user['initials'], 
                self
            )
            prof.logout_clicked.connect(self.on_logout)
            prof.show_statistics.connect(self.show_statistics_modal)
            prof.edit_profile_clicked.connect(self.show_edit_profile_modal)
            self.user_box.addWidget(prof)
        
        dlg.profile_updated.connect(on_profile_updated)
        dlg.exec_()

    def on_view_password(self, password_data):
        """View password with decryption"""
        from src.gui.components.modals import ViewPasswordModal

        # If ViewPasswordModal was updated to accept api_client, pass it, otherwise pass only parent
        try:
            dlg = ViewPasswordModal(password_data, self.api_client, self)
        except TypeError:
            dlg = ViewPasswordModal(password_data, self)
        dlg.exec_()

    def setup_password_list_connections(self):
        """Setup all password list signal connections"""
        # ⭐ IMPORTANT: Connect copy_password to the decryption handler
        self.password_list.copy_password.connect(self.on_copy_password)
        self.password_list.view_password.connect(self.on_view_password)
        self.password_list.edit_password.connect(self.on_edit_password)
        self.password_list.delete_password.connect(self.on_delete_password)
        self.password_list.favorite_password.connect(self.on_favorite_password)

    def on_copy_password(self, encrypted_password):
        """Decrypt and copy password to clipboard"""
        try:
            print(f"🔓 Déchiffrement du mot de passe...")
            decrypted = self.api_client.decrypt_password(encrypted_password)
            
            if decrypted and not decrypted.startswith('[DECRYPT_ERROR'):
                QApplication.clipboard().setText(decrypted)
                print(f"✅ Mot de passe déchiffré et copié: {decrypted[:3]}***")
                QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier!")
            else:
                print(f"❌ Erreur de déchiffrement: {decrypted}")
                QMessageBox.warning(self, "Erreur", "❌ Impossible de déchiffrer le mot de passe")
        except Exception as e:
            print(f"❌ Erreur lors du déchiffrement: {e}")
            QMessageBox.warning(self, "Erreur", f"❌ Erreur: {str(e)}")

    def on_view_password(self, password_data):
        """View password with decryption"""
        from src.gui.components.modals import ViewPasswordModal

        # If ViewPasswordModal accepts api_client, pass it; else fallback to parent-only
        try:
            dlg = ViewPasswordModal(password_data, self.api_client, self)
        except TypeError:
            dlg = ViewPasswordModal(password_data, self)
        dlg.exec_()