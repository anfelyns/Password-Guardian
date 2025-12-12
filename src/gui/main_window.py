# -*- coding: utf-8 -*-
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QMessageBox, QApplication, QPushButton, QDialog, QGridLayout, QLineEdit, QMenu, QAction,
    QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime

# UI + components
from src.gui.components.sidebar import Sidebar
from src.gui.components.password_list import PasswordList
from src.gui.components.modals import (
    LoginModal, RegisterModal, AddPasswordModal,
    EditPasswordModal, ViewPasswordModal, TwoFactorModal,
    SettingsDialog
)
from src.gui.components.auth_dialogs import ForgotPasswordDialog
from src.gui.styles.styles import Styles
from src.gui.autofill import (
    autofill_with_selenium,
    open_and_type_credentials,
    simple_copy_paste_method,
    automatic_autofill
)
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
        self.setWindowTitle("Vérification 2FA")
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

        verify_btn = QPushButton("✔ Vérifier")
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
    settings_clicked = pyqtSignal()

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

        head = QAction(f"👤 {self.username}", self)
        head.setEnabled(False)
        m.addAction(head)
        m.addSeparator()

        act_settings = QAction("⚙️ Paramètres", self)
        act_settings.triggered.connect(self.settings_clicked.emit)
        m.addAction(act_settings)

        act_stats = QAction("📈 Mes statistiques", self)
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
        self.api_client = APIClient("http://127.0.0.1:5000")
        self.auth = AuthManager()
        # State
        self.current_user = None
        self._all_passwords = []
        self.current_session_id = None

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
        icon = QLabel("🔑")
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
        """Connect sidebar, list and card signals AES-256 guard every optional signal."""
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
    def _auth_flow(self, prefill_email: str = ""):
        if not self.current_user:
            self.hide()

        dlg = LoginModal(self, default_email=prefill_email, auth_manager=self.auth)
        self._login_dialog = dlg
        dlg.login_success.connect(self._on_login_attempt)
        dlg.switch_to_register.connect(lambda: self._switch_to_register(prefill_email=prefill_email))
        res = dlg.exec_()
        self._login_dialog = None
        if res != QDialog.Accepted and not self.current_user:
            QApplication.quit()

    def _switch_to_register(self, prefill_email: str = ""):
        dlg = RegisterModal(self)
        dlg.register_success.connect(self._on_register_attempt)
        dlg.switch_to_login.connect(lambda: self._auth_flow(prefill_email))
        dlg.exec_()

    def _on_login_attempt(self, email: str, password: str):
        result = self.auth.authenticate(email, password)
        if result.get("error"):
            if self._login_dialog:
                self._login_dialog.show_error_message(result["error"])
            else:
                self._show_error_dialog("Erreur de connexion", result["error"])
            failed = self.auth.get_failed_attempts(email)
            if failed >= 5:
                rep = QMessageBox.question(
                    self,
                    "Trop de tentatives",
                    "Vous avez saisi un mot de passe incorrect plusieurs fois.\n"
                    "Souhaitez-vous réinitialiser votre mot de passe ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if rep == QMessageBox.Yes:
                    self._open_forgot_password(email)
                    return
            QTimer.singleShot(0, lambda: self._auth_flow(prefill_email=email))
            return
        if not result.get("2fa_sent", False):
            msg = "Impossible d'envoyer le code 2FA"
            if self._login_dialog:
                self._login_dialog.show_error_message(msg)
            else:
                self._show_error_dialog("Erreur", msg)
            return
        user = result.get("user")
        if self._login_dialog:
            self._login_dialog.reset_after_success()
            self._close_login_dialog()
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
                self._show_error_dialog("Erreur", "Code invalide ou expiré"
)

        try:
            dlg.code_verified.disconnect()
        except Exception:
            pass
        dlg.code_verified.connect(verify)

        if dlg.exec_() != QDialog.Accepted:
            self._auth_flow()

    def _on_register_attempt(self, name, email, password):
        """Handle registration with email verification"""
        ok, msg, extra = self.auth.register_user(name, email, password)
        
        if not ok:
            self._show_error_dialog("Erreur d'inscription", msg)
            return
        
        # Show success message
        QMessageBox.information(
            self,
            "Inscription réussie",
            f"✅ {msg}\n\n"
            "Un code de vérification a été envoyé à votre email.\n"
            "Veuillez vérifier votre boîte mail (et les spams)."
        )
        
        # Get user_id from extra data
        user_id = extra.get('user_id')
        if not user_id:
            self._show_error_dialog("Erreur", "Impossible de récupérer l'ID utilisateur")
            self._auth_flow()
            return
        
        # Show email verification dialog
        self._show_email_verification(email, user_id)

    def _show_email_verification(self, email: str, user_id: int):
        """Show email verification dialog with resend option"""
        dlg = QDialog(self)
        dlg.setWindowTitle("📧 Vérification de l'email")
        dlg.setFixedSize(480, 380)
        dlg.setModal(True)
        dlg.setAttribute(Qt.WA_StyledBackground, True)
        dlg.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }}
            QLabel {{ color: {Styles.TEXT_PRIMARY}; background: transparent; }}
        """)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Icon
        icon = QLabel("📧")
        icon.setStyleSheet("font-size:56px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Title
        title = QLabel("Vérifiez votre email"
)
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # Info
        info = QLabel(
            f"Un code de vérification a été envoyé à :\n"
            f"{email}\n\n"
            f"Vérifiez votre boîte mail (et les spams)"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{Styles.TEXT_SECONDARY}; font-size:13px;")
        layout.addWidget(info)
        
        # Code input
        code_input = QLineEdit()
        code_input.setPlaceholderText("Code à 6 chiffres")
        code_input.setMaxLength(6)
        code_input.setAlignment(Qt.AlignCenter)
        code_input.setFont(QFont("Courier New", 20, QFont.Bold))
        code_input.setMinimumHeight(56)
        code_input.setStyleSheet(f"""
            QLineEdit {{
                {Styles.get_input_style()}
                padding: 12px;
                font-size: 24px;
                letter-spacing: 10px;
            }}
        """)
        layout.addWidget(code_input)
        
        # Status label
        status_label = QLabel("")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        layout.addWidget(status_label)
        
        # Verify button
        verify_btn = QPushButton("✔ Vérifier")
        verify_btn.setMinimumHeight(48)
        verify_btn.setCursor(Qt.PointingHandCursor)
        verify_btn.setStyleSheet(Styles.get_button_style(True))
        layout.addWidget(verify_btn)
        
        # Resend button
        resend_btn = QPushButton("🔁 Renvoyer le code")
        resend_btn.setMinimumHeight(44)
        resend_btn.setCursor(Qt.PointingHandCursor)
        resend_btn.setStyleSheet(Styles.get_button_style(False))
        layout.addWidget(resend_btn)
        
        # Countdown timer state
        countdown = {"seconds": 60, "active": False}
        timer = QTimer(dlg)
        
        def update_countdown():
            if countdown["seconds"] > 0:
                countdown["seconds"] -= 1
                status_label.setText(f"⏳ Renvoyer disponible dans {countdown['seconds']}s")
                resend_btn.setEnabled(False)
            else:
                timer.stop()
                countdown["active"] = False
                status_label.setText("")
                resend_btn.setEnabled(True)
        
        def start_countdown():
            countdown["seconds"] = 60
            countdown["active"] = True
            resend_btn.setEnabled(False)
            timer.timeout.connect(update_countdown)
            timer.start(1000)
        
        def verify_code():
            code = code_input.text().strip()
            
            if not code or len(code) != 6:
                QMessageBox.warning(dlg, "Code invalide", "Veuillez saisir un code à 6 chiffres")
                return
            
            # Verify the registration code
            ok = self.auth.verify_registration_code(email, code)
            
            if ok:
                dlg.accept()
                QMessageBox.information(
                    self,
                    "Email vérifié",
                    "✅ Votre email a été vérifié avec succès!\n\n"
                    "Vous pouvez maintenant vous connecter."
                )
                self._auth_flow()
            else:
                QMessageBox.warning(
                    dlg,
                    "Code invalide", 
                    "❗ Le code saisi est invalide ou a expiré.\n\n"
                    "Cliquez sur 'Renvoyer le code' pour recevoir un nouveau code."
                )
        
        def resend_code():
            ok = self.auth.resend_verification_code(email)
            
            if ok:
                QMessageBox.information(
                    dlg,
                    "Code renvoyé",
                    f"✅ Un nouveau code a été envoyé à :\n{email}\n\n"
                    "Vérifiez votre boîte mail (et les spams)"
                )
                code_input.clear()
                start_countdown()
            else:
                QMessageBox.warning(
                    dlg,
                    "Erreur",
                    "❌ Impossible de renvoyer le code.\n\n"
                    "L'email est peut-être déjà vérifié."
                )
        
        verify_btn.clicked.connect(verify_code)
        resend_btn.clicked.connect(resend_code)
        code_input.returnPressed.connect(verify_code)
        
        # Start countdown
        start_countdown()
        
        # Focus on input
        code_input.setFocus()
        
        result = dlg.exec_()
        
        if result != QDialog.Accepted:
            QMessageBox.warning(
                self,
                "Vérification annulée",
                "⚠️ Votre email n'a pas été vérifié.\n\n"
                "Vous devrez vérifier votre email pour vous connecter."
            )
            self._auth_flow()

    def _finalize_login(self, user: dict):
        name = (user.get("username") or user.get("email", "").split("@")[0]).capitalize()
        initials = (name[:2] or "US").upper()
        import platform
        device_name = platform.node() or "Appareil"
        system_info = f"{platform.system()} {platform.release()}".strip()

        self.current_user = {
            "id": user["id"],
            "username": name,
            "email": user["email"],
            "name": name,
            "initials": initials,
        }
        self.current_session_id = self.auth.register_session(
            user["id"],
            device_name=device_name,
            system_info=system_info
        )

        self._mount_profile_widget()

        if not self.isVisible():
            QTimer.singleShot(0, self.show)
            QTimer.singleShot(0, self.raise_)
            QTimer.singleShot(0, self.activateWindow)

        QTimer.singleShot(0, self.load_passwords)
        QMessageBox.information(self, "Bienvenue", f"🎉 Bienvenue {name}!")

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
                self._show_error_dialog("Erreur", "Code invalide ou expiré"
)

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
        """
        Get PLAIN PASSWORD from backend
        ⚠️ Backend /reveal endpoint returns PLAIN TEXT (already decrypted)
        """
        ok, msg, plain_password = self.api_client.reveal_password(password_id)
        if not ok:
            raise ValueError(msg or "Erreur API")
        if not plain_password:
            raise ValueError("Mot de passe vide")
        
        # Backend already decrypted it - return as-is
        print(f"✅ Got plain password from backend (length: {len(plain_password)})")
        return plain_password

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
            # Backend returns PLAIN password - no need to decrypt
            plain = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur", str(e))
            return

        p = next((x for x in self._all_passwords if x.get("id") == int(pid)), {}).copy()
        # Set the plain password for display
        p["encrypted_password"] = plain
        p["password"] = plain  # Add this for ViewPasswordModal
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
            # Backend returns PLAIN password - no need to decrypt
            plain = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur", str(e))
            return

        QApplication.clipboard().setText(plain)
        QMessageBox.information(self, "Copié", "📋 Mot de passe copié dans le presse-papier!")

    def on_edit_password(self, pid: int):
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            return

        p_prefill = p.copy()
        try:
            # Backend returns PLAIN password - no need to decrypt
            pt = self._decrypt_from_backend(pid)
            p_prefill["password"] = pt
            p_prefill["encrypted_password"] = pt
        except Exception as e:
            self._show_error_dialog("Erreur", f"Impossible de récupérer le mot de passe: {str(e)}")
            return

        dlg = EditPasswordModal(p_prefill, self)

        def _upd(_id, new_plain, _lm):
            # Don't encrypt here - backend will encrypt it
            ok, msg = self.api_client.update_password(
                password_id=_id,
                updates={
                    "site_name": p["site_name"],
                    "username": p["username"],
                    "password": new_plain,  # Send plain - backend encrypts
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

    def _get_plain_password_for_view(self, password_id: int) -> str:
        """
        Get plain password for viewing.
        For OLD encrypted passwords: returns as-is from DB.
        For NEW hashed passwords: Cannot retrieve - returns error message.
        """
        try:
            # Try to get from temporary storage first (recently added passwords)
            import requests
            response = requests.post(
                f"{self.api_client.base_url}/passwords/{password_id}/get-plain-temp",
                timeout=5
            )
            
            if response.ok:
                data = response.json()
                return data.get('password', '')
            
            # If not in temp storage, try to reveal (for old encrypted passwords)
            response = requests.post(
                f"{self.api_client.base_url}/passwords/{password_id}/reveal",
                timeout=5
            )
            
            if response.ok:
                data = response.json()
                
                if data.get('type') == 'encrypted':
                    # Old format - can be retrieved
                    return data.get('password', '')
                elif data.get('type') == 'hashed':
                    # New format - cannot retrieve
                    return None
                
            return None
            
        except Exception as e:
            print(f"❌ Error getting plain password: {e}")
            return None

    # ---------------- CRUD ----------------
    def _show_add_password_modal(self):
        dlg = AddPasswordModal(self)

        def _add(payload: dict):
            """Handle adding a new password"""
            try:
                # Extract data from payload
                site_name = payload.get("site_name", "")
                site_url = payload.get("site_url", "")
                username = payload.get("username", "")
                plain_password = payload.get("password", "")  # ✔ Now expects 'password' key
                category = payload.get("category", "personal")
                
                # Debug logging
                print(f"\n{'='*60}")
                print(f"➕ Adding Password")
                print(f"{'='*60}")
                print(f"Site Name: {site_name}")
                print(f"Site URL: {site_url}")
                print(f"Username: {username}")
                print(f"Password Length: {len(plain_password)}")
                print(f"Category: {category}")
                print(f"User ID: {self.current_user['id']}")
                print(f"{'='*60}\n")
                
                # Validate all required fields
                if not site_name:
                    QMessageBox.warning(self, "Erreur", "Le nom du site est requis")
                    return
                
                if not username:
                    QMessageBox.warning(self, "Erreur", "L'identifiant est requis")
                    return
                
                if not plain_password:
                    QMessageBox.warning(self, "Erreur", "Le mot de passe est requis")
                    return
                
                if not self.current_user or 'id' not in self.current_user:
                    QMessageBox.warning(self, "Erreur", "Utilisateur non connecté")
                    return
                
                # ✔ Send plain password to backend - backend will hash it
                ok, msg, response = self.api_client.add_password(
                    user_id=self.current_user["id"],
                    site_name=site_name,
                    username=username,
                    encrypted_password=plain_password,  # Backend expects this key name
                    category=category,
                    site_url=site_url
                )
                
                if ok:
                    print(f"✅ Password added successfully: {response}")
                    self.load_passwords()
                    QMessageBox.information(
                        self,
                        "Succès",
                        f"✅ Mot de passe ajouté avec succès!\n\n"
                        f"Site: {site_name}\n"
                        f"Identifiant: {username}"
                    )
                else:
                    print(f"❌ Failed to add password: {msg}")
                    QMessageBox.warning(
                        self, 
                        "Erreur", 
                        f"❌ Impossible d'ajouter le mot de passe:\n\n{msg}"
                    )
                    
            except Exception as e:
                print(f"❌ Exception in _add: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(
                    self, 
                    "Erreur", 
                    f"❌ Une erreur s'est produite:\n\n{str(e)}"
                )

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
        """Delete or trash a password - FIXED VERSION"""
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            self._show_error_dialog("Erreur", "Mot de passe introuvable")
            return
        
        cat = p.get("category", "personal")

        if cat == "trash":
            # Permanent deletion
            rep = QMessageBox.question(
                self, 
                "Suppression définitive",
                "⚠️ Supprimer définitivement ? Cette action est irréversible.",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
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
            # Move to trash
            rep = QMessageBox.question(
                self, 
                "Corbeille",
                "Déplacer vers la corbeille ? (Auto-suppression après 48h)",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            if rep != QMessageBox.Yes:
                return
            
            # FIXED: Don't send encrypted_password when trashing
            # Just update category to 'trash'
            ok, msg = self.api_client.update_password(
                password_id=pid,
                updates={
                    "category": "trash"
                    # Don't include encrypted_password, username, site_name
                }
            )
            
            if ok:
                self.load_passwords()
                QMessageBox.information(self, "Corbeille", "🗑️ Déplacé vers la corbeille.")
            else:
                self._show_error_dialog("Erreur", msg)

    def on_restore_password(self, pid: int):
        """Restore password from trash - FIXED VERSION"""
        p = next((x for x in self._all_passwords if x.get("id") == pid), None)
        if not p:
            self._show_error_dialog("Erreur", "Mot de passe introuvable")
            return
        
        rep = QMessageBox.question(
            self, 
            "Restaurer", 
            "Restaurer ce mot de passe ?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        if rep != QMessageBox.Yes:
            return
        
        # FIXED: Only update category, don't touch password field
        ok, msg = self.api_client.update_password(
            password_id=pid,
            updates={
                "category": "personal"
                # Don't include encrypted_password, username, site_name
            }
        )
        
        if ok:
            self.load_passwords()
            QMessageBox.information(self, "Restauré", "✅ Restauré avec succès.")
        else:
            self._show_error_dialog("Erreur", msg)

    def on_favorite_password(self, pid: int):
        """Toggle favorite status for a password"""
        try:
            print(f"\n🌟 Toggling favorite for password ID={pid}")
            
            # Find the password in local cache
            p = next((x for x in self._all_passwords if x.get("id") == pid), None)
            if not p:
                print(f"   ❌ Password not found in local cache")
                self._show_error_dialog("Erreur", "Mot de passe introuvable")
                return
            
            current_status = p.get("favorite", False)
            print(f"   Current status: {current_status}")
            
            # Call API to toggle
            ok, msg, new_status = self.api_client.toggle_favorite(pid)
            
            if ok:
                print(f"   ✅ Successfully toggled: {current_status} → {new_status}")
                
                # Update local cache
                p["favorite"] = new_status
                
                # Reload to refresh UI
                self.load_passwords()
                
                # Show confirmation
                status_text = "ajouté aux favoris" if new_status else "retiré des favoris"
                QMessageBox.information(
                    self, 
                    "Favoris", 
                    f"✅ {p.get('site_name', 'Mot de passe')} {status_text}!"
                )
            else:
                print(f"   ❌ Failed to toggle: {msg}")
                self._show_error_dialog("Erreur", f"Impossible de modifier les favoris:\n{msg}")
                
        except Exception as e:
            print(f"   ❌ Exception in on_favorite_password: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_dialog("Erreur", f"Une erreur s'est produite:\n{str(e)}")

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
        """
        Handle auto-login with METHOD CHOICE
        FIXED: Uses threading to prevent event loop blocking
        """
        # Extract details
        pid = payload.get('id')
        site_url = payload.get('site_url', '')
        username = payload.get('username', '')
        
        if not site_url:
            self._show_error_dialog("URL manquante", "Impossible d'effectuer le remplissage automatique sans URL.")
            return
        
        if not pid:
            self._show_error_dialog("Erreur", "Identifiant du mot de passe manquant.")
            return
        
        # 2FA verification
        if not self._confirm_sensitive("remplissage automatique"):
            return
        
        # Decrypt password (backend returns plain text)
        try:
            plain_password = self._decrypt_from_backend(int(pid))
        except Exception as e:
            self._show_error_dialog("Erreur", f"Impossible de récupérer le mot de passe:\n{str(e)}")
            return
        
        # Method selection dialog
        choice_dialog = QMessageBox(self)
        choice_dialog.setWindowTitle("Méthode d'auto-remplissage")
        choice_dialog.setText(
            f"🚀 Choisissez la méthode d'auto-remplissage:\n\n"
            f"🌐 Site: {site_url}\n"
            f"👤 Identifiant: {username}"
        )
        choice_dialog.setIcon(QMessageBox.Question)
        
        # Custom buttons
        btn_selenium = choice_dialog.addButton("🤖 Selenium (Best)", QMessageBox.YesRole)
        btn_auto = choice_dialog.addButton("⚡ Auto (Smart)", QMessageBox.ActionRole)
        btn_assisted = choice_dialog.addButton("🤝 Assisted (Safe)", QMessageBox.NoRole)
        btn_simple = choice_dialog.addButton("📋 Copy-Paste", QMessageBox.RejectRole)
        btn_cancel = choice_dialog.addButton("❌ Cancel", QMessageBox.RejectRole)
        
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
        
        # Run in separate thread to avoid blocking Qt event loop
        def run_autofill():
            try:
                from src.gui.autofill import (
                    autofill_with_selenium,
                    open_and_type_credentials,
                    simple_copy_paste_method,
                    automatic_autofill
                )
                
                if clicked == btn_selenium:
                    print("\n🤖 Starting Selenium auto-fill...")
                    success = autofill_with_selenium(site_url, username, plain_password)
                elif clicked == btn_auto:
                    print("\n⚡ Starting smart auto-fill...")
                    success = automatic_autofill(site_url, username, plain_password)
                elif clicked == btn_assisted:
                    print("\n🤝 Starting assisted auto-fill...")
                    success = open_and_type_credentials(site_url, username, plain_password, delay=6.0)
                else:  # Simple
                    print("\n📋 Starting copy-paste method...")
                    success = simple_copy_paste_method(site_url, username, plain_password)
                    
            except ImportError as e:
                print(f"\n❌ Import error: {e}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Preparation message
        prep_msg = QMessageBox(self)
        prep_msg.setWindowTitle("Préparation...")
        prep_msg.setIcon(QMessageBox.Information)
        
        if clicked == btn_selenium:
            prep_msg.setText(
                "🤖 MODE SELENIUM\n\n"
                "Le navigateur va s'ouvrir.\n"
                "Les champs seront remplis automatiquement.\n"
                "Le bouton submit sera cliqué.\n\n"
                "⏰ Attendez 5 secondes..."
            )
        elif clicked == btn_auto:
            prep_msg.setText(
                "⚡ MODE AUTOMATIQUE\n\n"
                "Sélection intelligente de la meilleure méthode.\n"
                "Selenium est privilégié, sinon un script bureau prend le relais.\n\n"
                "🕒 Gardez le navigateur visible et ne touchez pas au clavier."
            )
        elif clicked == btn_assisted:
            prep_msg.setText(
                "🤝 MODE ASSISTÉ\n\n"
                "Le site va s'ouvrir.\n"
                "Cliquez sur les champs quand demandé.\n"
                "Les données seront collées automatiquement.\n\n"
                "👁️ Regardez la console pour les instructions!"
            )
        else:  # Simple
            prep_msg.setText(
                "📋 MODE COPIER-COLLER\n\n"
                "Le site va s'ouvrir.\n"
                "Les identifiants seront copiés un par un.\n"
                "Vous les collerez manuellement.\n\n"
                "👁️ Regardez la console pour les instructions!"
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
        
        # Run in thread
        print(f"\n{'='*70}")
        print(f"🚀 LAUNCHING AUTO-FILL")
        print(f"{'='*70}")
        
        thread = threading.Thread(target=run_autofill, daemon=True)
        thread.start()
        
        # Success message (will appear immediately, actual work happens in thread)
        QTimer.singleShot(1000, lambda: QMessageBox.information(
            self,
            "Auto-fill Started",
            "✅ Auto-fill process started!\n\n"
            "Watch the console and browser.\n\n"
            "If it doesn't work:\n"
            "• Try the 'Assisted' method\n"
            "• Or use 'Copy-Paste' for full control"
        ))
    # ---------------- Stats / Profile / Logout ----------------
    def _show_statistics_modal(self):
        d = QDialog(self)
        d.setWindowTitle("📊 Statistiques intelligentes")
        screen = QApplication.primaryScreen()
        width, height = 1150, 780
        if screen:
            geo = screen.availableGeometry()
            width = min(width, geo.width() - 120)
            height = min(height, geo.height() - 120)
        d.setFixedSize(width, height)
        d.setAttribute(Qt.WA_StyledBackground, True)
        d.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 22px;
            }}
            QLabel {{ color: {Styles.TEXT_PRIMARY}; background: transparent; }}
        """)

        dialog_layout = QVBoxLayout(d)
        dialog_layout.setContentsMargins(32, 28, 32, 24)
        dialog_layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("📊 Aperçu de votre coffre")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        header_info = QLabel(datetime.utcnow().strftime("Mis à jour le %d/%m à %Hh%M"))
        header_info.setStyleSheet(Styles.get_label_style(11, Styles.TEXT_MUTED))
        header.addWidget(header_info, alignment=Qt.AlignRight)
        dialog_layout.addLayout(header)

        passwords = [p for p in self._all_passwords if p.get('category') != 'trash']
        total = len(passwords)
        strong = sum(1 for p in passwords if p.get('strength') == 'strong')
        medium = sum(1 for p in passwords if p.get('strength') == 'medium')
        weak = sum(1 for p in passwords if p.get('strength') == 'weak')
        favorites = sum(1 for p in passwords if p.get('favorite'))
        security_score = int((strong / total) * 100) if total else 0

        # Summary cards
        cards = [
            ("🔐", "Total enregistrés", total, Styles.BLUE_PRIMARY),
            ("✅", "Forts", strong, Styles.STRONG_COLOR),
            ("⚠️", "Moyens", medium, Styles.MEDIUM_COLOR),
            ("❌", "Faibles", weak, Styles.WEAK_COLOR),
            ("⭐", "Favoris", favorites, Styles.BLUE_SECONDARY),
            ("🧹", "Corbeille", sum(1 for p in self._all_passwords if p.get("category") == "trash"), Styles.TEXT_SECONDARY),
        ]
        cards_grid = QGridLayout()
        cards_grid.setSpacing(14)
        for i, (icon, label, value, color) in enumerate(cards):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 16px;
                }
            """)
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(16, 14, 16, 14)
            card_lay.setSpacing(6)
            card_lay.setAlignment(Qt.AlignCenter)
            icon_lbl = QLabel(icon)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("font-size:26px;")
            name_lbl = QLabel(label)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(Styles.get_label_style(15, Styles.TEXT_SECONDARY))
            val = QLabel(str(value))
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet(f"color:{color}; font-size:34px; font-weight:900;")
            card_lay.addWidget(icon_lbl, alignment=Qt.AlignCenter)
            card_lay.addWidget(name_lbl, alignment=Qt.AlignCenter)
            card_lay.addWidget(val, alignment=Qt.AlignCenter)
            cards_grid.addWidget(card, i // 3, i % 3)
        dialog_layout.addLayout(cards_grid)

        main_section = QHBoxLayout()
        main_section.setSpacing(18)
        left_col = QVBoxLayout()
        left_col.setSpacing(18)

        # Security score
        score_card = QFrame()
        score_card.setStyleSheet("""
            QFrame {
                background: rgba(0,0,0,0.25);
                border-radius: 18px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        sc_layout = QHBoxLayout(score_card)
        sc_layout.setContentsMargins(18, 14, 18, 14)
        sc_layout.setSpacing(16)
        score_text = QLabel("Indice global de sécurité")
        score_text.setFont(QFont("Segoe UI", 14, QFont.Bold))
        score_text.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        sc_layout.addWidget(score_text)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(security_score)
        bar.setTextVisible(True)
        bar.setFormat(f"{security_score}%")
        bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 10px;
                background: rgba(255,255,255,0.05);
                padding: 2px;
                color: white;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #22d3ee, stop:1 #3b82f6);
            }
        """)
        sc_layout.addWidget(bar, 1)
        left_col.addWidget(score_card)

        # Category distribution
        dist_frame = QFrame()
        dist_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.04);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        dist_layout = QVBoxLayout(dist_frame)
        dist_layout.setContentsMargins(18, 16, 18, 16)
        dist_layout.setSpacing(10)
        dist_layout.addWidget(QLabel("R?partition par cat?gorie"))
        dist = {}
        for p in passwords:
            key = p.get("category", "personnel")
            dist[key] = dist.get(key, 0) + 1
        if not dist:
            empty = QLabel("Aucune donn?e pour le moment.")
            empty.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED))
            dist_layout.addWidget(empty)
        for key, value in sorted(dist.items(), key=lambda x: -x[1]):
            row = QHBoxLayout()
            lbl = QLabel(key.capitalize())
            lbl.setStyleSheet(Styles.get_label_style(13))
            row.addWidget(lbl, 0)
            perc = int((value / total) * 100) if total else 0
            prog = QProgressBar()
            prog.setRange(0, 100)
            prog.setValue(perc)
            prog.setTextVisible(False)
            prog.setStyleSheet("""
                QProgressBar {
                    border: 1px solid rgba(255,255,255,0.18);
                    border-radius: 9px;
                    background: rgba(0,0,0,0.25);
                    height: 14px;
                }
                QProgressBar::chunk {
                    border-radius: 8px;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #a855f7, stop:1 #6366f1);
                }
            """)
            row.addWidget(prog, 1)
            value_lbl = QLabel(f"{value} ({perc}%)")
            value_lbl.setStyleSheet(Styles.get_label_style(11, Styles.TEXT_SECONDARY))
            row.addWidget(value_lbl, 0)
            dist_layout.addLayout(row)
        left_col.addWidget(dist_frame)

        right_col = QVBoxLayout()
        right_col.setSpacing(18)

        # Recent activity
        recent_frame = QFrame()
        recent_frame.setStyleSheet("""
            QFrame {
                background: rgba(0,0,0,0.3);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        rf_layout = QVBoxLayout(recent_frame)
        rf_layout.setContentsMargins(18, 16, 18, 16)
        rf_layout.setSpacing(8)
        rf_layout.addWidget(QLabel("Activité recente"))
        recent = sorted(passwords, key=lambda x: x.get("last_updated") or x.get("created_at") or "", reverse=True)[:5]
        if not recent:
            lbl = QLabel("Aucune activité recente.")
            lbl.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_MUTED))
            rf_layout.addWidget(lbl)
        else:
            for item in recent:
                text = f"{item.get('site_name','Compte')} ? {item.get('username','')}"
                date = item.get("last_updated") or item.get("created_at") or "N/A"
                row = QLabel(f"{text}\n<small>{date}</small>")
                row.setStyleSheet(Styles.get_label_style(12))
                row.setTextFormat(Qt.RichText)
                rf_layout.addWidget(row)
        right_col.addWidget(recent_frame)

        tip_card = QFrame()
        tip_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.05);
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.04);
            }
        """)
        tip_layout = QVBoxLayout(tip_card)
        tip_layout.setContentsMargins(18, 16, 18, 16)
        tip_layout.setSpacing(6)
        tips = QLabel("Conseil: ajoutez au moins 1 mot de passe par semaine et privil?giez les mots de passe forts pour maximiser votre score.")
        tips.setStyleSheet(Styles.get_label_style(11, Styles.TEXT_MUTED))
        tips.setWordWrap(True)
        tip_layout.addWidget(tips)
        right_col.addWidget(tip_card)

        main_section.addLayout(left_col, 3)
        main_section.addLayout(right_col, 2)
        dialog_layout.addLayout(main_section)
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(Styles.get_button_style(True))
        close_btn.setMinimumHeight(46)
        close_btn.clicked.connect(d.accept)
        dialog_layout.addWidget(close_btn)

        d.exec_()

    def _mount_profile_widget(self):
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)
        prof = UserProfileWidget(self.current_user["username"], self.current_user["initials"], self)
        prof.logout_clicked.connect(self.on_logout)
        prof.show_statistics.connect(self._show_statistics_modal)
        prof.settings_clicked.connect(self._open_settings)
        self.user_box.addWidget(prof)

    def _show_edit_profile_modal(self):
        from src.gui.components.modals import EditProfileModal

        dlg = EditProfileModal(self.current_user, self.auth, self)

        def on_updated(u):
            self.current_user["username"] = u["username"]
            self.current_user["name"] = u["username"]
            self.current_user["initials"] = (u["username"][:2] or "US").upper()
            self._mount_profile_widget()

        dlg.profile_updated.connect(on_updated)
        dlg.exec_()

    def _open_settings(self):
        if not self.current_user:
            return
        dlg = SettingsDialog(self.current_user, self.auth, self)
        dlg.exec_()
        refreshed = self.auth._user_by_email(self.current_user["email"])
        if refreshed:
            self.current_user["username"] = refreshed["username"]
            self.current_user["name"] = refreshed["username"]
            self.current_user["initials"] = (refreshed["username"][:2] or "US").upper()
            self._mount_profile_widget()

    def _open_forgot_password(self, email: str = ""):
        dlg = ForgotPasswordDialog(self.auth, self)
        if email:
            dlg.email.setText(email)
        dlg.exec_()

    def _close_login_dialog(self):
        if getattr(self, "_login_dialog", None):
            try:
                self._login_dialog.accept()
            except Exception:
                pass
            self._login_dialog = None

    def on_logout(self):
        rep = QMessageBox.question(self, "Déconnexion", "Se déconnecter ?",
                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if rep != QMessageBox.Yes:
            return
        if self.current_user and getattr(self, "current_session_id", None):
            self.auth.remove_session(self.current_user["id"], self.current_session_id)
        self.current_session_id = None
        self.current_user = None
        self.hide()
        for i in reversed(range(self.user_box.count())):
            w = self.user_box.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._all_passwords = []
        self.password_list.load_passwords([])
        self._auth_flow()
