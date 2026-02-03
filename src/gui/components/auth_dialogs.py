# -*- coding: utf-8 -*-
"""
Auth dialogs (Connexion / Inscription / 2FA / Reset) - Pro UI polish

Used by: src/gui/components/modals.py
"""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QThreadPool
from PyQt5.QtGui import QFont

from src.auth.auth_manager import AuthManager
from src.gui.components.threading_utils import TaskWorker
from src.gui.styles.styles import Styles


_DIALOG_QSS = f"""
QDialog {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {Styles.PRIMARY_BG},
        stop:0.55 {Styles.SECONDARY_BG},
        stop:1 {Styles.ACCENT_BG}
    );
}}
QLabel {{
    color: {Styles.TEXT_PRIMARY};
    background: transparent;
}}
QFrame#card {{
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 22px;
}}
{Styles.get_input_style()}
QPushButton#iconBtn {{
    background-color: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 10px 12px;
}}
QPushButton#iconBtn:hover {{
    background-color: rgba(255,255,255,0.10);
}}
QPushButton#iconBtn:pressed {{
    background-color: rgba(255,255,255,0.14);
}}
QPushButton#linkBtn {{
    background: transparent;
    border: none;
    color: {Styles.BLUE_SECONDARY};
    padding: 4px 8px;
    text-align: center;
}}
QPushButton#linkBtn:hover {{
    color: {Styles.TEXT_PRIMARY};
    text-decoration: underline;
}}
QPushButton#secondaryBtn {{
    background-color: rgba(255, 255, 255, 0.04);
    color: {Styles.TEXT_PRIMARY};
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 10px 14px;
}}
QPushButton#secondaryBtn:hover {{
    background-color: rgba(255,255,255,0.08);
}}
"""


def _apply_dialog_theme(dlg: QDialog) -> None:
    dlg.setStyleSheet(_DIALOG_QSS)


def _h1(text: str) -> QLabel:
    lab = QLabel(text)
    f = QFont()
    f.setPointSize(22)
    f.setBold(True)
    lab.setFont(f)
    lab.setAlignment(Qt.AlignCenter)
    return lab


def _subtitle(text: str) -> QLabel:
    lab = QLabel(text)
    f = QFont()
    f.setPointSize(11)
    lab.setFont(f)
    lab.setAlignment(Qt.AlignCenter)
    lab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
    return lab


def _field_label(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 12px;")
    return lab


class LoginDialog(QDialog):
    """Connexion window (with email 2FA)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Connexion")
        self.setModal(True)
        self.setFixedSize(460, 520)

        _apply_dialog_theme(self)

        self.auth = AuthManager()
        self.user_info = None
        self.threadpool = QThreadPool.globalInstance()

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(22, 22, 22, 22)
        card_l.setSpacing(14)

        icon = QLabel("🔐")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 40px;")
        card_l.addWidget(icon)

        card_l.addWidget(_h1("Connexion"))
        card_l.addWidget(_subtitle("Accédez à votre coffre-fort sécurisé"))

        card_l.addSpacing(6)
        card_l.addWidget(_field_label("Adresse e-mail"))
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("votre@email.com")
        self.email_edit.setMinimumHeight(44)
        card_l.addWidget(self.email_edit)

        card_l.addWidget(_field_label("Mot de passe"))
        pass_row = QHBoxLayout()
        pass_row.setSpacing(10)

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Entrez votre mot de passe")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setMinimumHeight(44)

        self.btn_eye = QPushButton("👁")
        self.btn_eye.setObjectName("iconBtn")
        self.btn_eye.setFixedSize(48, 44)
        self.btn_eye.setCursor(Qt.PointingHandCursor)
        self.btn_eye.clicked.connect(self._toggle_password)

        pass_row.addWidget(self.pass_edit, 1)
        pass_row.addWidget(self.btn_eye)
        card_l.addLayout(pass_row)

        card_l.addSpacing(8)
        self.btn_login = QPushButton("🚀  Se connecter")
        self.btn_login.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_login.setMinimumHeight(48)
        self.btn_login.clicked.connect(self._on_login_clicked)
        card_l.addWidget(self.btn_login)

        links = QHBoxLayout()
        links.setSpacing(6)

        self.btn_forgot = QPushButton("Mot de passe oublié ?")
        self.btn_forgot.setObjectName("linkBtn")
        self.btn_forgot.setCursor(Qt.PointingHandCursor)
        self.btn_forgot.clicked.connect(self._forgot)

        self.btn_reset = QPushButton("Réinitialiser")
        self.btn_reset.setObjectName("linkBtn")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self._forgot)

        links.addStretch(1)
        links.addWidget(self.btn_forgot)
        links.addWidget(self.btn_reset)
        links.addStretch(1)
        card_l.addLayout(links)

        self.btn_create = QPushButton("Créer un compte")
        self.btn_create.setObjectName("secondaryBtn")
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.setMinimumHeight(44)
        self.btn_create.clicked.connect(self._open_register)
        card_l.addWidget(self.btn_create)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("linkBtn")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        card_l.addWidget(self.btn_cancel, alignment=Qt.AlignCenter)

        root.addWidget(card)

    def _toggle_password(self):
        if self.pass_edit.echoMode() == QLineEdit.Password:
            self.pass_edit.setEchoMode(QLineEdit.Normal)
            self.btn_eye.setText("🙈")
        else:
            self.pass_edit.setEchoMode(QLineEdit.Password)
            self.btn_eye.setText("👁")

    def _on_login_clicked(self):
        email = self.email_edit.text().strip()
        pw = self.pass_edit.text()

        if not email:
            QMessageBox.warning(self, "Champ vide", "Veuillez saisir votre email.")
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText("Connexion...")

        worker = TaskWorker(self.auth.authenticate, email, pw)
        worker.signals.finished.connect(self._on_login_result)
        worker.signals.error.connect(self._on_login_error)
        self.threadpool.start(worker)

    def _on_login_result(self, resp: dict):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("🚀  Se connecter")

        if resp.get("error"):
            QMessageBox.critical(self, "Erreur", resp["error"])
            return

        if resp.get("2fa_sent"):
            d = Verify2FADialog(self.auth, email=self.email_edit.text().strip(), parent=self)
            if d.exec_():
                self.user_info = resp.get("user")
                self.accept()
            return

        self.user_info = resp.get("user")
        self.accept()

    def _on_login_error(self, message: str):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("🚀  Se connecter")
        QMessageBox.critical(self, "Erreur", "Échec de connexion:\n" + message)

    def _forgot(self):
        d = ForgotPasswordDialog(self.auth, parent=self)
        d.exec_()

    def _open_register(self):
        d = RegisterDialog(self.auth, parent=self)
        if d.exec_():
            QMessageBox.information(self, "Compte créé", "Votre compte est prêt. Vous pouvez vous connecter.")
            self.email_edit.setText(d.email_value)
            self.pass_edit.setFocus()


class RegisterDialog(QDialog):
    """Create account + verify email code."""

    def __init__(self, auth_mgr: AuthManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SecureVault - Créer un compte")
        self.setModal(True)
        self.setFixedSize(500, 560)

        _apply_dialog_theme(self)

        self.auth = auth_mgr
        self.threadpool = QThreadPool.globalInstance()
        self.email_value = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(22, 22, 22, 22)
        card_l.setSpacing(12)

        icon = QLabel("✨")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 36px;")
        card_l.addWidget(icon)

        card_l.addWidget(_h1("Créer un compte"))
        card_l.addWidget(_subtitle("Un code sera envoyé à votre e-mail"))

        card_l.addSpacing(8)
        card_l.addWidget(_field_label("Nom d'utilisateur"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("Votre nom")
        self.username.setMinimumHeight(44)
        card_l.addWidget(self.username)

        card_l.addWidget(_field_label("Adresse e-mail"))
        self.email = QLineEdit()
        self.email.setPlaceholderText("votre@email.com")
        self.email.setMinimumHeight(44)
        card_l.addWidget(self.email)

        card_l.addWidget(_field_label("Mot de passe"))
        self.p1 = QLineEdit()
        self.p1.setPlaceholderText("Choisissez un mot de passe fort")
        self.p1.setEchoMode(QLineEdit.Password)
        self.p1.setMinimumHeight(44)
        card_l.addWidget(self.p1)

        card_l.addWidget(_field_label("Confirmer le mot de passe"))
        self.p2 = QLineEdit()
        self.p2.setPlaceholderText("Répétez le mot de passe")
        self.p2.setEchoMode(QLineEdit.Password)
        self.p2.setMinimumHeight(44)
        card_l.addWidget(self.p2)

        card_l.addSpacing(8)
        self.btn_create = QPushButton("Créer le compte")
        self.btn_create.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_create.setMinimumHeight(48)
        self.btn_create.clicked.connect(self._create_account)
        card_l.addWidget(self.btn_create)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setObjectName("linkBtn")
        self.btn_cancel.clicked.connect(self.reject)
        card_l.addWidget(self.btn_cancel, alignment=Qt.AlignCenter)

        root.addWidget(card)

    def _create_account(self):
        username = self.username.text().strip()
        email = self.email.text().strip()
        p1 = self.p1.text()
        p2 = self.p2.text()

        if not username or not email or not p1 or not p2:
            QMessageBox.warning(self, "Champs vides", "Tous les champs sont requis.")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        if len(p1) < 8:
            QMessageBox.warning(self, "Trop court", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        self.btn_create.setEnabled(False)
        self.btn_create.setText("Création...")

        worker = TaskWorker(self.auth.register_user, username, email, p1)
        worker.signals.finished.connect(lambda res: self._on_register_done(res, email))
        worker.signals.error.connect(self._on_register_err)
        self.threadpool.start(worker)

    def _on_register_done(self, result, email: str):
        self.btn_create.setEnabled(True)
        self.btn_create.setText("Créer le compte")

        try:
            ok, msg, _payload = result
        except Exception:
            ok, msg = False, "Réponse inattendue"

        if not ok:
            QMessageBox.warning(self, "Erreur", msg)
            return

        QMessageBox.information(self, "Vérification", msg)
        d = VerifyRegistrationDialog(self.auth, email=email, parent=self)
        if d.exec_():
            self.email_value = email
            self.accept()

    def _on_register_err(self, message: str):
        self.btn_create.setEnabled(True)
        self.btn_create.setText("Créer le compte")
        QMessageBox.critical(self, "Erreur", "Création échouée:\n" + message)


class VerifyRegistrationDialog(QDialog):
    """Verify email code after registration."""

    def __init__(self, auth_mgr: AuthManager, email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vérification")
        self.setModal(True)
        self.setFixedSize(420, 300)
        _apply_dialog_theme(self)

        self.auth = auth_mgr
        self.email = email

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 22, 22, 22)
        v.setSpacing(12)

        v.addWidget(_h1("Vérification"))
        info = QLabel(f"Un code a été envoyé à :\n<b>{email}</b>")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        v.addWidget(info)

        v.addWidget(_field_label("Code à 6 chiffres"))
        self.code = QLineEdit()
        self.code.setPlaceholderText("000000")
        self.code.setMaxLength(6)
        self.code.setMinimumHeight(44)
        self.code.setAlignment(Qt.AlignCenter)
        v.addWidget(self.code)

        self.btn_verify = QPushButton("Vérifier")
        self.btn_verify.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_verify.setMinimumHeight(46)
        self.btn_verify.clicked.connect(self._verify)
        v.addWidget(self.btn_verify)

        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("linkBtn")
        btn_close.clicked.connect(self.reject)
        v.addWidget(btn_close, alignment=Qt.AlignCenter)

        root.addWidget(card)

    def _verify(self):
        code = self.code.text().strip()
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres.")
            return
        ok = self.auth.verify_registration_code(self.email, code)
        if ok:
            QMessageBox.information(self, "Succès", "Compte vérifié.")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Code invalide ou expiré.")


class Verify2FADialog(QDialog):
    """2FA dialog (email-based) with 60s resend cooldown."""

    COOLDOWN = 60

    def __init__(self, auth_mgr: AuthManager, email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vérification 2FA")
        self.setModal(True)
        self.setFixedSize(440, 320)

        _apply_dialog_theme(self)

        self.auth = auth_mgr
        self.email = email
        self.threadpool = QThreadPool.globalInstance()

        self.remaining = self.COOLDOWN
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(22, 22, 22, 22)
        v.setSpacing(12)

        v.addWidget(_h1("Vérification"))
        info = QLabel(f"Un code a été envoyé à :\n<b>{email}</b>")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Styles.TEXT_SECONDARY};")
        v.addWidget(info)

        v.addWidget(_field_label("Code à 6 chiffres"))
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("000000")
        self.code_edit.setMaxLength(6)
        self.code_edit.setMinimumHeight(44)
        self.code_edit.setAlignment(Qt.AlignCenter)
        v.addWidget(self.code_edit)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {Styles.TEXT_MUTED};")
        v.addWidget(self.status_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_verify = QPushButton("Vérifier")
        self.btn_verify.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_verify.setMinimumHeight(44)
        self.btn_verify.clicked.connect(self._verify)

        self.btn_resend = QPushButton("Renvoyer")
        self.btn_resend.setObjectName("secondaryBtn")
        self.btn_resend.setMinimumHeight(44)
        self.btn_resend.clicked.connect(self._resend)

        btn_row.addWidget(self.btn_verify, 2)
        btn_row.addWidget(self.btn_resend, 1)
        v.addLayout(btn_row)

        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("linkBtn")
        btn_close.clicked.connect(self.reject)
        v.addWidget(btn_close, alignment=Qt.AlignCenter)

        root.addWidget(card)

        self._start_cooldown()

    def _verify(self):
        code = self.code_edit.text().strip()
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres.")
            return
        try:
            ok = self.auth.verify_2fa_email(self.email, code)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Vérification échouée:\n{e}")
            return
        if ok:
            self.accept()
        else:
            QMessageBox.warning(self, "Incorrect", "Code invalide ou expiré.")

    def _resend(self):
        if not self.btn_resend.isEnabled():
            return
        self.btn_resend.setEnabled(False)
        self.status_lbl.setText("Renvoi en cours…")

        worker = TaskWorker(self.auth.send_2fa_code, self.email, None, "login")
        worker.signals.finished.connect(self._on_resend_done)
        worker.signals.error.connect(self._on_resend_error)
        self.threadpool.start(worker)

    def _on_resend_done(self, ok):
        if ok:
            QMessageBox.information(self, "Envoyé", "Nouveau code envoyé.")
        else:
            QMessageBox.warning(self, "Erreur", "Échec de l'envoi du code.")
        self._start_cooldown()

    def _on_resend_error(self, message: str):
        QMessageBox.critical(self, "Erreur", "Échec de l'envoi du code:\n" + message)
        self._start_cooldown()

    def _start_cooldown(self):
        self.remaining = self.COOLDOWN
        self.btn_resend.setEnabled(False)
        self._update_status()
        self.timer.start(1000)

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.status_lbl.setText("")
            self.btn_resend.setEnabled(True)
            self.btn_resend.setText("Renvoyer")
            return
        self._update_status()

    def _update_status(self):
        self.btn_resend.setText(f"Renvoyer ({self.remaining}s)")
        self.status_lbl.setText("Vous pouvez renvoyer un code après le délai de sécurité.")


class ForgotPasswordDialog(QDialog):
    """Password reset request (email code)."""

    def __init__(self, auth_mgr: AuthManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mot de passe oublié")
        self.setModal(True)
        self.setFixedSize(520, 520)
        _apply_dialog_theme(self)

        self.auth = auth_mgr

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)

        v.addWidget(_h1("Réinitialiser"))
        v.addWidget(_subtitle("Un code sera envoyé à votre e-mail"))

        v.addSpacing(8)
        v.addWidget(_field_label("Adresse e-mail"))
        self.email = QLineEdit()
        self.email.setPlaceholderText("votre@email.com")
        self.email.setMinimumHeight(44)
        v.addWidget(self.email)

        v.addWidget(_field_label("Code de réinitialisation"))
        self.code = QLineEdit()
        self.code.setPlaceholderText("Code (6 chiffres)")
        self.code.setMaxLength(6)
        self.code.setMinimumHeight(44)
        self.code.setAlignment(Qt.AlignCenter)
        v.addWidget(self.code)

        v.addWidget(_field_label("Nouveau mot de passe"))
        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("Nouveau mot de passe")
        self.new_pw.setEchoMode(QLineEdit.Password)
        self.new_pw.setMinimumHeight(44)
        v.addWidget(self.new_pw)

        v.addWidget(_field_label("Confirmer le mot de passe"))
        self.new_pw_confirm = QLineEdit()
        self.new_pw_confirm.setPlaceholderText("Confirmer le mot de passe")
        self.new_pw_confirm.setEchoMode(QLineEdit.Password)
        self.new_pw_confirm.setMinimumHeight(44)
        v.addWidget(self.new_pw_confirm)

        v.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_send = QPushButton("Envoyer le code")
        self.btn_send.setObjectName("secondaryBtn")
        self.btn_send.setMinimumHeight(42)
        self.btn_send.setStyleSheet(Styles.get_button_style(primary=False) + "\nQPushButton{border-radius:18px;}")
        self.btn_send.clicked.connect(self._send_code)

        self.btn_reset = QPushButton("Mettre à jour")
        self.btn_reset.setStyleSheet(Styles.get_button_style(primary=True) + "\nQPushButton{border-radius:18px;}")
        self.btn_reset.setMinimumHeight(42)
        self.btn_reset.clicked.connect(self._reset)

        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("secondaryBtn")
        btn_close.setMinimumHeight(42)
        btn_close.setStyleSheet(Styles.get_button_style(primary=False) + "\nQPushButton{border-radius:18px;}")
        btn_close.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_send, 1)
        btn_row.addWidget(self.btn_reset, 1)
        btn_row.addWidget(btn_close, 1)
        v.addLayout(btn_row)

        root.addWidget(card)

    def _send_code(self):
        email = self.email.text().strip()
        if not email:
            QMessageBox.warning(self, "Champ vide", "Veuillez saisir votre email.")
            return
        ok = self.auth.send_reset_code(email)
        if ok:
            QMessageBox.information(self, "Envoyé", "Code envoyé par e-mail.")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le code. Vérifiez l'adresse e-mail.")

    def _reset(self):
        email = self.email.text().strip()
        code = self.code.text().strip()
        new_pw = self.new_pw.text()
        confirm = self.new_pw_confirm.text()

        if not email or not code or not new_pw or not confirm:
            QMessageBox.warning(self, "Champs vides", "Veuillez compléter tous les champs.")
            return
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Code invalide", "Veuillez saisir un code à 6 chiffres.")
            return
        if new_pw != confirm:
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        if len(new_pw) < 8:
            QMessageBox.warning(self, "Trop court", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        ok = self.auth.update_password_with_code(email, code, new_pw)
        if ok:
            QMessageBox.information(self, "OK", "Mot de passe mis à jour.")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Code invalide/expiré ou erreur.")


__all__ = [
    "LoginDialog",
    "RegisterDialog",
    "VerifyRegistrationDialog",
    "Verify2FADialog",
    "ForgotPasswordDialog",
]
