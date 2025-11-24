# src/gui/main_window.py
# Main Password Guardian window – Blue UI + 2FA + AES-GCM + Auto-fill + DEBUG

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QMessageBox, QApplication, QPushButton, QDialog, QGridLayout, QLineEdit, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

# UI + components
from src.gui.components.sidebar import Sidebar
from src.gui.components.password_list import PasswordList
from src.gui.components.modals import (
    LoginModal, RegisterModal, AddPasswordModal,
    EditPasswordModal, ViewPasswordModal, TwoFactorModal
)
from src.gui.styles.styles import Styles
from src.gui.autofill import open_and_type_credentials
# Services
from src.backend.api_client import APIClient
from src.auth.auth_manager import AuthManager
from src.security.encryption import encrypt_for_storage, decrypt_any


# ----------------------------- Small helpers -----------------------------
class Quick2FADialog(QDialog):
    code_verified = pyqtSignal()

    def __init__(self, email: str, parent=None):
        super().__init__(parent)
        self.email = email
        self._build()

    def _build(self):
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

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:48px;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        title = QLabel("Vérification de sécurité")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        lay.addWidget(title)

        info = QLabel(f"Code envoyé à :\n{self.email}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:13px;")
        info.setWordWrap(True)
        lay.addWidget(info)

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
        lay.addWidget(self.code_input)

        verify_btn = QPushButton("✅ Vérifier")
        verify_btn.setMinimumHeight(44)
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setStyleSheet(Styles.get_button_style(True))
        verify_btn.clicked.connect(self.code_verified.emit)
        lay.addWidget(verify_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(Styles.get_button_style(False))
        cancel_btn.clicked.connect(self.reject)
        lay.addWidget(cancel_btn)

        self.code_input.setFocus()


class UserProfileWidget(QWidget):
    logout_clicked = pyqtSignal()
    show_statistics = pyqtSignal()
    edit_profile_clicked = pyqtSignal()

    def __init__(self, username: str, initials: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.initials = initials
        self._build()

    def _build(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        avatar = QPushButton(self.initials)
        avatar.setFixedSize(40, 40)
        avatar.setCursor(Qt.PointingHandCursor)
        avatar.clicked.connect(self._menu)
        avatar.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.BLUE_PRIMARY}, stop:1 {Styles.PURPLE});
                border-radius: 20px; color:#fff; font-weight:bold;
            }}
        """)
        row.addWidget(avatar)

        name_btn = QPushButton(self.username)
        name_btn.setCursor(Qt.PointingHandCursor)
        name_btn.clicked.connect(self._menu)
        name_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{Styles.TEXT_PRIMARY};
                          border:none; font-size:14px; }}
            QPushButton:hover {{ color:{Styles.BLUE_SECONDARY}; }}
        """)
        row.addWidget(name_btn)

    def _menu(self):
        m = QMenu(self)
        m.setStyleSheet(f"""
            QMenu {{background:#0f1e36; border:1px solid rgba(255,255,255,0.2);
                    border-radius:10px; padding:10px; }}
            QMenu::item {{padding:8px 14px; border-radius:8px; color:{Styles.TEXT_PRIMARY};}}
            QMenu::item:selected {{background:rgba(59,130,246,0.25); }}
        """)

        head = QAction(f"👋 {self.username}", self)
        head.setEnabled(False)
        m.addAction(head)
        m.addSeparator()

        act_edit = QAction("✏️ Modifier le profil", self)
        act_edit.triggered.connect(self.edit_profile_clicked.emit)
        m.addAction(act_edit)

        act_stats = QAction("📊 Mes statistiques", self)
        act_stats.triggered.connect(self.show_statistics.emit)
        m.addAction(act_stats)

        m.addSeparator()

        act_logout = QAction("🚪 Se déconnecter", self)
        act_logout.triggered.connect(self.logout_clicked.emit)
        m.addAction(act_logout)

        m.exec_(self.mapToGlobal(self.rect().bottomRight()))


# ----------------------------- Main Window -----------------------------
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = APIClient("http://127.0.0.1:5001")
        self.auth = AuthManager()
        # State
        self.current_user = None
        self._all_passwords = []

        # UI
        self._build_ui()
        self._wire_basic_signals()
        self._auth_flow()

    # ---------------- UI / Theme ----------------
    def _build_ui(self):
        self.setWindowTitle("Password Guardian")
        self.setMinimumSize(1280, 780)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0a1628, stop:1 #1a2942);
            }
            QDialog, QMessageBox {
                background-color: #0E1B32;
                color: #E6EFFB;
                border: 1px solid rgba(255,255,255,0.08);
            }
            QMessageBox QPushButton {
                background-color: #2563EB;
                color: white; border-radius:8px; padding:6px 14px;
            }
            QMessageBox QPushButton:hover { background-color: #1D4ED8; }
        """)

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Header
        head = QHBoxLayout()
        icon = QLabel("🛡️")
        icon.setStyleSheet("font-size:32px;")
        title = QLabel("Password Guardian")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        self.user_box = QHBoxLayout()
        uw = QWidget()
        uw.setLayout(self.user_box)
        head.addWidget(icon)
        head.addWidget(title)
        head.addStretch()
        head.addWidget(uw)
        root.addLayout(head)

        # Body (Sidebar + List)
        body = QHBoxLayout()
        self.sidebar = Sidebar()
        body.addWidget(self.sidebar)

        frame = QFrame()
        frame.setStyleSheet("background:transparent;")
        v = QVBoxLayout(frame)
        v.setContentsMargins(0, 0, 0, 0)

        self.password_list = PasswordList()
        v.addWidget(self.password_list)
        body.addWidget(frame, 1)
        root.addLayout(body)

    def _wire_basic_signals(self):
        """Connect sidebar, list and card signals – guard every optional signal."""
        # Sidebar
        if hasattr(self.sidebar, "category_changed"):
            self.sidebar.category_changed.connect(self.on_category_changed)
        if hasattr(self.sidebar, "add_password_clicked"):
            self.sidebar.add_password_clicked.connect(self._show_add_password_modal)

        # PasswordList signals
        if hasattr(self.password_list, "copy_password"):
            self.password_list.copy_password.connect(self.on_copy_password)
        if hasattr(self.password_list, "view_password"):
            self.password_list.view_password.connect(self.on_view_password)
        if hasattr(self.password_list, "edit_password"):
            self.password_list.edit_password.connect(self.on_edit_password)
        if hasattr(self.password_list, "delete_password"):
            self.password_list.delete_password.connect(self.on_delete_password)
        if hasattr(self.password_list, "favorite_password"):
            self.password_list.favorite_password.connect(self.on_favorite_password)
        if hasattr(self.password_list, "restore_password"):
            self.password_list.restore_password.connect(self.on_restore_password)
        
        # Auto-fill signal (NEW)
        if hasattr(self.password_list, "auto_login_clicked"):
            self.password_list.auto_login_clicked.connect(self.on_auto_login_clicked)

        # Optional 2FA request signals (cards may emit before view/copy)
        if hasattr(self.password_list, "request_2fa_for_view"):
            self.password_list.request_2fa_for_view.connect(self._handle_2fa_view)
        if hasattr(self.password_list, "request_2fa_for_copy"):
            self.password_list.request_2fa_for_copy.connect(self._handle_2fa_copy)

    # ---------------- Auth flow ----------------
    def _auth_flow(self):
        dlg = LoginModal(self)
        dlg.login_success.connect(self._on_login_attempt)
        dlg.switch_to_register.connect(self._switch_to_register)
        res = dlg.exec_()
        if res != QDialog.Accepted and not self.current_user:
            QApplication.quit()

    def _switch_to_register(self):
        dlg = RegisterModal(self)
        dlg.register_success.connect(self._on_register_attempt)
        dlg.switch_to_login.connect(self._auth_flow)
        dlg.exec_()

    def _on_login_attempt(self, email: str, password: str):
        result = self.auth.authenticate(email, password)
        if result.get("error"):
            self._show_error_dialog("Erreur de connexion", result["error"])
            return
        if not result.get("2fa_sent", False):
            self._show_error_dialog("Erreur", "Impossible d'envoyer le code 2FA")
            return
        user = result.get("user")
        self._show_2fa_login(user)

    def _show_2fa_login(self, user: dict):
        dlg = TwoFactorModal(user["email"], "<code envoyé>", self)

        def verify():
            code = dlg.code_input.text().strip()
            if not code or len(code) != 6:
                self._show_error_dialog("Code invalide", "Code 6 chiffres requis")
                return
            ok = False
            if hasattr(self.auth, "verify_2fa_email"):
                ok = self.auth.verify_2fa_email(user["email"], code)
            elif hasattr(self.auth, "verify_2fa"):
                ok = self.auth.verify_2fa(user["email"], code)
            if ok:
                dlg.accept()
                self._finalize_login(user)
            else:
                self._show_error_dialog("Erreur", "Code invalide ou expiré")

        try:
            dlg.code_verified.disconnect()
        except Exception:
            pass
        dlg.code_verified.connect(verify)

        if dlg.exec_() != QDialog.Accepted:
            self._auth_flow()

    def _on_register_attempt(self, name, email, password):
        ok, msg, _ = self.auth.register_user(name, email, password)
        if not ok:
            self._show_error_dialog("Inscription", msg)
            return
        QMessageBox.information(self, "Succès", "✅ Vérifiez votre email")
        self._auth_flow()

    def _finalize_login(self, user: dict):
        name = (user.get("username") or user.get("email", "").split("@")[0]).capitalize()
        initials = (name[:2] or "US").upper()

        # Clear user box
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.current_user = {
            "id": user["id"],
            "username": name,
            "email": user["email"],
            "name": name,
            "initials": initials,
        }

        prof = UserProfileWidget(name, initials, self)
        prof.logout_clicked.connect(self.on_logout)
        prof.show_statistics.connect(self._show_statistics_modal)
        prof.edit_profile_clicked.connect(self._show_edit_profile_modal)
        self.user_box.addWidget(prof)

        QTimer.singleShot(0, self.load_passwords)
        QMessageBox.information(self, "Bienvenue", f"✅ Bienvenue {name}!")

    def _show_error_dialog(self, title: str, message: str):
        """Show error message with proper word wrap and sizing"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Styles.PRIMARY_BG};
                color: {Styles.TEXT_PRIMARY};
            }}
            QMessageBox QLabel {{
                color: {Styles.TEXT_PRIMARY};
                min-width: 300px;
                max-width: 500px;
            }}
            QPushButton {{
                {Styles.get_button_style(True)}
                min-width: 80px;
                min-height: 32px;
            }}
        """)
        msg_box.exec_()

    # ---------------- Data loading / filtering ----------------
    def load_passwords(self):
        if not self.current_user:
            return
        
        ok, msg, data = self.api_client.get_passwords(self.current_user["id"])
        self._all_passwords = data if ok else []
        
        visible = [p for p in self._all_passwords if p.get("category") != "trash"]
        self.password_list.load_passwords(visible)

        counts = {k: 0 for k in ["all", "work", "personal", "finance", "game", "study", "favorites", "trash"]}
        counts["all"] = len(visible)
        counts["trash"] = len([p for p in self._all_passwords if p.get("category") == "trash"])
        for p in visible:
            c = p.get("category")
            if c in counts:
                counts[c] += 1
            if p.get("favorite"):
                counts["favorites"] += 1
        
        self.sidebar.update_counts(counts)

    def on_category_changed(self, cat: str):
        base = self._all_passwords
        if cat == "all":
            f = [p for p in base if p.get("category") != "trash"]
        elif cat == "trash":
            f = [p for p in base if p.get("category") == "trash"]
        elif cat == "favorites":
            f = [p for p in base if p.get("favorite") and p.get("category") != "trash"]
        else:
            f = [p for p in base if p.get("category") == cat]
        self.password_list.load_passwords(f)

    # ---------------- 2FA helper for sensitive actions ----------------
    def _confirm_sensitive(self, purpose: str) -> bool:
        """Send a 2FA email and verify."""
        if not self.current_user:
            return False
        email = self.current_user["email"]

        sent = False
        if hasattr(self.auth, "send_2fa_email"):
            sent = self.auth.send_2fa_email(email, purpose)
        if not sent and hasattr(self.auth, "send_2fa_code"):
            sent = self.auth.send_2fa_code(to_email=email, user_id=self.current_user["id"], purpose=purpose)
        if not sent:
            self._show_error_dialog("Erreur", "Impossible d'envoyer le code 2FA")
            return False

        dlg = Quick2FADialog(email, self)
        verified = {"ok": False}

        def _verify():
            code = dlg.code_input.text().strip()
            if not code or len(code) != 6:
                self._show_error_dialog("Code invalide", "Code 6 chiffres requis")
                return
            ok = False
            if hasattr(self.auth, "verify_2fa_email"):
                ok = self.auth.verify_2fa_email(email, code)
            elif hasattr(self.auth, "verify_2fa"):
                ok = self.auth.verify_2fa(email, code)
            if ok:
                verified["ok"] = True
                dlg.accept()
            else:
                self._show_error_dialog("Erreur", "Code invalide ou expiré")

        try:
            dlg.code_verified.disconnect()
        except Exception:
            pass
        dlg.code_verified.connect(_verify)
        dlg.exec_()
        return verified["ok"]

    def _handle_2fa_view(self, payload: dict):
        if not self._confirm_sensitive("visualisation"):
            return
        self.on_view_password(payload)

    def _handle_2fa_copy(self, token_or_dict):
        if not self._confirm_sensitive("copie"):
            return
        self.on_copy_password(token_or_dict)

    def _decrypt_from_backend(self, password_id: int) -> str:
        ok, msg, enc_token = self.api_client.reveal_password(password_id)
        if not ok:
            raise ValueError(msg or "Erreur API")
        if not enc_token:
            raise ValueError("Token manquant")
        return decrypt_any(enc_token)

    # ---------------- CRUD ----------------
    def _show_add_password_modal(self):
        dlg = AddPasswordModal(self)

        def _add(payload: dict):
            enc = encrypt_for_storage(payload.get("password", ""))
            ok, msg, response = self.api_client.add_password(
                user_id=self.current_user["id"],
                site_name=payload["site_name"],
                username=payload["username"],
                encrypted_password=enc,
                category=payload.get("category", "personal"),
                site_url=payload.get("site_url", "")
            )
            
            if ok:
                self.load_passwords()
                QMessageBox.information(self, "Succès", "✅ Mot de passe ajouté avec succès!")
            else:
                self._show_error_dialog("Erreur", msg)

        dlg.password_added.connect(_add)
        dlg.exec_()

    def on_edit_password(self, pid: int):
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            return

        p_prefill = p.copy()
        try:
            pt = self._decrypt_from_backend(pid)
            p_prefill["password"] = pt
            p_prefill["encrypted_password"] = pt
        except Exception as e:
            self._show_error_dialog("Erreur", f"Impossible de décrypter: {str(e)}")
            return

        dlg = EditPasswordModal(p_prefill, self)

        def _upd(_id, new_plain, _lm):
            enc = encrypt_for_storage(new_plain)
            ok, msg = self.api_client.update_password(
                password_id=_id,
                updates={
                    "site_name": p["site_name"],
                    "username": p["username"],
                    "encrypted_password": enc,
                    "category": p.get("category", "personal"),
                    "favorite": p.get("favorite", False),
                }
            )
            if ok:
                self.load_passwords()
                QMessageBox.information(self, "Succès", "✅ Mot de passe mis à jour.")
            else:
                self._show_error_dialog("Erreur", msg)

        dlg.password_updated.connect(_upd)
        dlg.exec_()

    def on_delete_password(self, pid: int):
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            return
        cat = p.get("category", "personal")

        if cat == "trash":
            rep = QMessageBox.question(
                self, "Suppression définitive",
                "⚠️ Supprimer définitivement ? Cette action est irréversible.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if rep != QMessageBox.Yes:
                return
            ok, msg = self.api_client.delete_password(pid)
            if ok:
                self.load_passwords()
                QMessageBox.information(self, "Supprimé", "🗑️ Supprimé définitivement.")
            else:
                self._show_error_dialog("Erreur", msg)
        else:
            rep = QMessageBox.question(
                self, "Corbeille",
                "Déplacer vers la corbeille ? (Auto-suppression après 48h)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if rep != QMessageBox.Yes:
                return
            ok, msg = self.api_client.update_password(
                password_id=pid,
                updates={
                    "site_name": p["site_name"],
                    "username": p["username"],
                    "encrypted_password": p["encrypted_password"],
                    "category": "trash",
                    "favorite": p.get("favorite", False)
                }
            )
            if ok:
                self.load_passwords()
                QMessageBox.information(self, "Corbeille", "♻️ Déplacé vers la corbeille.")
            else:
                self._show_error_dialog("Erreur", msg)

    def on_restore_password(self, pid: int):
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            return
        rep = QMessageBox.question(
            self, "Restaurer", "Restaurer ce mot de passe ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if rep != QMessageBox.Yes:
            return
        ok, msg = self.api_client.update_password(
            password_id=pid,
            updates={
                "site_name": p["site_name"],
                "username": p["username"],
                "encrypted_password": p["encrypted_password"],
                "category": "personal",
                "favorite": p.get("favorite", False)
            }
        )
        if ok:
            self.load_passwords()
            QMessageBox.information(self, "Restauré", "✅ Restauré avec succès.")
        else:
            self._show_error_dialog("Erreur", msg)

    def on_favorite_password(self, pid: int):
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            return
        newfav = not p.get("favorite", False)
        ok, msg = self.api_client.update_password(
            password_id=pid,
            updates={
                "site_name": p["site_name"],
                "username": p["username"],
                "encrypted_password": p["encrypted_password"],
                "category": p.get("category", "personal"),
                "favorite": newfav
            }
        )
        if ok:
            self.load_passwords()
        else:
            self._show_error_dialog("Erreur", msg)

    # ---------------- View / Copy with 2FA ----------------
    def on_view_password(self, payload):
        pid = None
        if isinstance(payload, dict):
            pid = payload.get("id")
        elif isinstance(payload, int):
            pid = payload

        if pid is None:
            self._show_error_dialog("Erreur", "Mot de passe introuvable")
            return

        if not self._confirm_sensitive("visualisation"):
            return
        
        try:
            plain = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur de déchiffrement", str(e))
            return

        p = next((x for x in self._all_passwords if x.get("id") == int(pid)), {}).copy()
        p["encrypted_password"] = plain
        ViewPasswordModal(p, self.api_client, self).exec_()

    def on_copy_password(self, payload):
        pid = None
        if isinstance(payload, dict):
            pid = payload.get("id")
        elif isinstance(payload, int):
            pid = payload

        if pid is None:
            self._show_error_dialog("Erreur", "Mot de passe introuvable")
            return

        if not self._confirm_sensitive("copie"):
            return
        
        try:
            plain = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur de déchiffrement", str(e))
            return

        QApplication.clipboard().setText(plain)
        QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier!")

    # ---------------- AUTO-FILL HANDLER ----------------
    def on_auto_login_clicked(self, payload: dict):
        """Handle auto-login avec CHOIX de méthode"""
        pid = payload.get('id')
        site_url = payload.get('site_url', '')
        username = payload.get('username', '')
        
        if not site_url:
            self._show_error_dialog("URL manquante", "Impossible d'effectuer le remplissage automatique sans URL.")
            return
        
        if not pid:
            self._show_error_dialog("Erreur", "Identifiant du mot de passe manquant.")
            return
        
        # Vérification 2FA
        if not self._confirm_sensitive("remplissage automatique"):
            return
        
        # Déchiffrer le mot de passe
        try:
            plain_password = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur de déchiffrement", f"Impossible de décrypter le mot de passe:\n{str(e)}")
            return
        
        # Proposer le choix de méthode
        choice_dialog = QMessageBox(self)
        choice_dialog.setWindowTitle("Méthode d'auto-remplissage")
        choice_dialog.setText(
            f"🚀 Choisissez la méthode d'auto-remplissage:\n\n"
            f"🌐 Site: {site_url}\n"
            f"👤 Identifiant: {username}"
        )
        choice_dialog.setIcon(QMessageBox.Question)
        
        # Boutons personnalisés
        btn_assisted = choice_dialog.addButton("🤝 Assistée (Recommandé)", QMessageBox.YesRole)
        btn_auto = choice_dialog.addButton("⚡ Automatique", QMessageBox.NoRole)
        btn_simple = choice_dialog.addButton("📋 Copier-Coller", QMessageBox.RejectRole)
        btn_cancel = choice_dialog.addButton("❌ Annuler", QMessageBox.RejectRole)
        
        choice_dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Styles.PRIMARY_BG};
                color: {Styles.TEXT_PRIMARY};
            }}
            QMessageBox QLabel {{
                color: {Styles.TEXT_PRIMARY};
                min-width: 400px;
            }}
            QPushButton {{
                {Styles.get_button_style(True)}
                min-width: 120px;
                min-height: 35px;
                margin: 3px;
            }}
        """)
        
        choice_dialog.exec_()
        clicked = choice_dialog.clickedButton()
        
        if clicked == btn_cancel:
            return
        
        try:
            from src.gui.autofill import (
                open_and_type_credentials,
                open_and_type_credentials_auto,
                simple_copy_paste_method
            )
            
            # Message de préparation
            prep_msg = QMessageBox(self)
            prep_msg.setWindowTitle("Préparation...")
            prep_msg.setIcon(QMessageBox.Information)
            
            if clicked == btn_assisted:
                prep_msg.setText(
                    "🤝 MODE ASSISTÉ\n\n"
                    "Le site va s'ouvrir.\n"
                    "Vous cliquerez sur les champs.\n"
                    "Les données seront collées automatiquement.\n\n"
                    "➡️ Regardez la console pour les instructions!"
                )
            elif clicked == btn_auto:
                prep_msg.setText(
                    "⚡ MODE AUTOMATIQUE\n\n"
                    "Le site va s'ouvrir.\n"
                    "Les champs seront remplis automatiquement.\n\n"
                    "⚠️ Ne touchez pas au clavier pendant 10 secondes!"
                )
            else:  # Simple
                prep_msg.setText(
                    "📋 MODE COPIER-COLLER\n\n"
                    "Le site va s'ouvrir.\n"
                    "Les identifiants seront copiés un par un.\n"
                    "Vous les collerez manuellement.\n\n"
                    "➡️ Regardez la console pour les instructions!"
                )
            
            prep_msg.setStandardButtons(QMessageBox.Ok)
            prep_msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {Styles.PRIMARY_BG};
                    color: {Styles.TEXT_PRIMARY};
                }}
                QMessageBox QLabel {{
                    color: {Styles.TEXT_PRIMARY};
                    min-width: 400px;
                }}
                QPushButton {{
                    {Styles.get_button_style(True)}
                    min-width: 80px;
                    min-height: 32px;
                }}
            """)
            
            prep_msg.exec_()
            
            # Lancer la méthode choisie
            print(f"\n{'='*70}")
            print(f"🚀 LANCEMENT AUTO-FILL")
            print(f"{'='*70}")
            
            if clicked == btn_assisted:
                success = open_and_type_credentials(site_url, username, plain_password, delay=6.0)
            elif clicked == btn_auto:
                success = open_and_type_credentials_auto(site_url, username, plain_password, delay=7.0)
            else:
                simple_copy_paste_method(site_url, username, plain_password)
                success = True
            
            # Message de fin
            if success:
                QMessageBox.information(
                    self,
                    "Auto-remplissage terminé",
                    "✅ Le processus est terminé!\n\n"
                    "Si la connexion n'a pas fonctionné:\n"
                    "• Essayez la méthode 'Assistée'\n"
                    "• Ou utilisez 'Copier-Coller' pour plus de contrôle"
                )
            
        except ImportError as e:
            self._show_error_dialog(
                "Module manquant",
                f"Le module pyautogui n'est pas installé.\n\n"
                f"Installez-le avec:\n"
                f"pip install pyautogui pyperclip\n\n"
                f"Erreur: {str(e)}"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_error_dialog(
                "Erreur d'auto-remplissage",
                f"Une erreur s'est produite:\n\n{str(e)}"
            )

    # ---------------- Stats / Profile / Logout ----------------
    def _show_statistics_modal(self):
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
        """)

        lay = QVBoxLayout(d)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        title = QLabel("📊 Mes statistiques")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        lay.addWidget(title)

        passwords = [p for p in self._all_passwords if p.get('category') != 'trash']
        total = len(passwords)
        strong = sum(1 for p in passwords if p.get('strength') == 'strong')
        medium = sum(1 for p in passwords if p.get('strength') == 'medium')
        weak = sum(1 for p in passwords if p.get('strength') == 'weak')
        favorites = sum(1 for p in passwords if p.get('favorite'))

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)

        def row(lbl, val, col):
            l = QLabel(lbl)
            l.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:15px;")
            v = QLabel(str(val))
            v.setStyleSheet(f"color:{col}; font-size:24px; font-weight:700;")
            return l, v

        r = 0
        for lbl, val, col in [
            ("🗂️ Total", total, Styles.BLUE_PRIMARY),
            ("✅ Forts", strong, Styles.STRONG_COLOR),
            ("⚠️ Moyens", medium, Styles.MEDIUM_COLOR),
            ("❌ Faibles", weak, Styles.WEAK_COLOR),
            ("⭐ Favoris", favorites, Styles.BLUE_SECONDARY),
        ]:
            l, v = row(lbl, val, col)
            grid.addWidget(l, r, 0, alignment=Qt.AlignLeft)
            grid.addWidget(v, r, 1, alignment=Qt.AlignRight)
            r += 1

        lay.addLayout(grid)

        score_wrap = QWidget()
        score_wrap.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }
        """)
        sw = QHBoxLayout(score_wrap)
        sw.setContentsMargins(14, 10, 14, 10)
        score_label = QLabel("🛡️ Score de sécurité")
        score_label.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:14px;")
        sw.addWidget(score_label, alignment=Qt.AlignLeft)
        security_score = int((strong / total) * 100) if total > 0 else 0
        score_color = Styles.STRONG_COLOR if security_score >= 80 else (
            Styles.MEDIUM_COLOR if security_score >= 50 else Styles.WEAK_COLOR
        )
        score_value = QLabel(f"{security_score}%")
        score_value.setStyleSheet(f"color:{score_color}; font-size:26px; font-weight:800;")
        sw.addWidget(score_value, alignment=Qt.AlignRight)
        lay.addWidget(score_wrap)
        lay.addStretch(1)

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(Styles.get_button_style(True))
        close_btn.setMinimumHeight(44)
        close_btn.clicked.connect(d.accept)
        lay.addWidget(close_btn)

        d.exec_()

    def _show_edit_profile_modal(self):
        from src.gui.components.modals import EditProfileModal

        dlg = EditProfileModal(self.current_user, self.auth, self)

        def on_updated(u):
            self.current_user["username"] = u["username"]
            self.current_user["name"] = u["username"]
            self.current_user["initials"] = (u["username"][:2] or "US").upper()
            for i in reversed(range(self.user_box.count())):
                w = self.user_box.itemAt(i).widget()
                if w:
                    w.setParent(None)
            prof = UserProfileWidget(self.current_user["username"], self.current_user["initials"], self)
            prof.logout_clicked.connect(self.on_logout)
            prof.show_statistics.connect(self._show_statistics_modal)
            prof.edit_profile_clicked.connect(self._show_edit_profile_modal)
            self.user_box.addWidget(prof)

        dlg.profile_updated.connect(on_updated)
        dlg.exec_()

    def on_logout(self):
        rep = QMessageBox.question(self, "Déconnection", "Se déconnecter ?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if rep != QMessageBox.Yes:
            return
        self.current_user = None
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._all_passwords = []
        self.password_list.load_passwords([])
        self._auth_flow()