# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QFrame, QSizePolicy, QFormLayout
)
from PyQt5.QtCore import QTimer, QThreadPool, Qt
from PyQt5.QtGui import QFont

try:
    from src.auth.auth_manager import AuthManager
except ImportError:  # Legacy fallback when src/ not packaged
    from auth.auth_manager import AuthManager
from src.gui.styles.styles import Styles
from src.gui.components.threading_utils import TaskWorker


class LoginDialog(QDialog):
    """Login window -> send 2FA -> verify (email)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion – Password Guardian")
        self.setModal(True)
        self.resize(420, 220)

        self.auth = AuthManager() 
        self.user_info = None
        self.threadpool = QThreadPool.globalInstance()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Mot de passe")
        self.pass_edit.setEchoMode(QLineEdit.Password)

        layout.addWidget(QLabel("Adresse e-mail"))
        layout.addWidget(self.email_edit)
        layout.addWidget(QLabel("Mot de passe"))
        layout.addWidget(self.pass_edit)

        row = QHBoxLayout()
        self.btn_login = QPushButton("Se connecter")
        self.btn_forgot = QPushButton("Mot de passe oublié ?")
        self.btn_cancel = QPushButton("Annuler")
        row.addWidget(self.btn_login)
        row.addWidget(self.btn_forgot)
        row.addWidget(self.btn_cancel)
        layout.addLayout(row)

        self.btn_login.clicked.connect(self._on_login_clicked)
        self.btn_forgot.clicked.connect(self._forgot)
        self.btn_cancel.clicked.connect(self.reject)

    # threaded login
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
        self.btn_login.setText("Se connecter")

        if resp.get("error"):
            QMessageBox.critical(self, "Erreur", resp["error"])
            return

        if resp.get("2fa_sent"):
            d = Verify2FADialog(self.auth, email=self.email_edit.text().strip(), parent=self)
            if d.exec_():
                self.user_info = resp.get("user")
                self.accept()
            return

        # If you ever allow direct login without 2FA:
        self.user_info = resp.get("user")
        self.accept()

    def _on_login_error(self, message: str):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("Se connecter")
        QMessageBox.critical(self, "Erreur", "Échec de connexion:\n" + message)

    def _forgot(self):
        d = ForgotPasswordDialog(self.auth, parent=self)
        d.exec_()


class Verify2FADialog(QDialog):
    """2FA dialog (email-based) with 60s resend cooldown."""
    COOLDOWN = 60

    def __init__(self, auth_mgr: AuthManager, email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vérification 2FA")
        self.setModal(True)
        self.resize(360, 190)

        self.auth = auth_mgr
        self.email = email
        self.threadpool = QThreadPool.globalInstance()

        self.remaining = self.COOLDOWN
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        v.addWidget(QLabel(f"Un code a été envoyé à : {email}"))

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Code à 6 chiffres")
        self.code_edit.setMaxLength(6)
        v.addWidget(self.code_edit)

        self.status_lbl = QLabel("")
        v.addWidget(self.status_lbl)

        row = QHBoxLayout()
        self.btn_verify = QPushButton("Vérifier")
        self.btn_resend = QPushButton("Renvoyer (60s)")
        self.btn_cancel = QPushButton("Fermer")
        row.addWidget(self.btn_verify)
        row.addWidget(self.btn_resend)
        row.addWidget(self.btn_cancel)
        v.addLayout(row)

        self.btn_verify.clicked.connect(self._verify)
        self.btn_resend.clicked.connect(self._resend)
        self.btn_cancel.clicked.connect(self.reject)

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

    # cooldown utils
    def _start_cooldown(self):
        self.remaining = self.COOLDOWN
        self.btn_resend.setEnabled(False)
        self._update_status()
        self.timer.start(1000)

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.btn_resend.setEnabled(True)
            self.status_lbl.setText("Vous pouvez renvoyer un code.")
            self.btn_resend.setText("Renvoyer le code")
        else:
            self._update_status()

    def _update_status(self):
        self.status_lbl.setText(f"Renvoyer disponible dans {self.remaining}s…")
        self.btn_resend.setText(f"Renvoyer ({self.remaining}s)")


class ForgotPasswordDialog(QDialog):
    """Send reset code → verify → set new password (all email-based)."""
    COOLDOWN = 60

    def __init__(self, auth_mgr: AuthManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mot de passe oublié")
        self.setModal(True)
        self.setFixedSize(700, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Styles.PRIMARY_BG}, stop:1 {Styles.SECONDARY_BG});
                border-radius: 28px;
                border: 1px solid rgba(255,255,255,0.08);
            }}
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                background: transparent;
            }}
        """)

        self.auth = auth_mgr
        self.remaining = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        def _style_field(widget):
            widget.setMinimumHeight(48)
            widget.setFont(QFont("Segoe UI", 12))
            widget.setStyleSheet(Styles.get_input_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 32)
        layout.setSpacing(18)

        header = QVBoxLayout()
        header.setAlignment(Qt.AlignCenter)
        icon = QLabel("🔐")
        icon.setStyleSheet("font-size:48px;")
        title = QLabel("Réinitialisation sécurisée")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(Styles.get_label_style(20))
        subtitle = QLabel("Recevez un code unique puis définissez un nouveau mot de passe.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(Styles.get_label_style(13, Styles.TEXT_SECONDARY))
        header.addWidget(icon)
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.04);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 20)
        card_layout.setSpacing(14)

        self.email = QLineEdit()
        self.email.setPlaceholderText("email@domaine.com")
        _style_field(self.email)
        self.code = QLineEdit()
        self.code.setPlaceholderText("Code reçu (6 chiffres)")
        self.code.setMaxLength(6)
        self.code.setAlignment(Qt.AlignCenter)
        self.code.setFont(QFont("Courier New", 18, QFont.Bold))
        _style_field(self.code)
        self.new1 = QLineEdit()
        self.new1.setPlaceholderText("Nouveau mot de passe")
        self.new1.setEchoMode(QLineEdit.Password)
        _style_field(self.new1)
        self.new2 = QLineEdit()
        self.new2.setPlaceholderText("Confirmer le mot de passe")
        self.new2.setEchoMode(QLineEdit.Password)
        _style_field(self.new2)

        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(18)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        def add_row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(Styles.get_label_style(12, Styles.TEXT_SECONDARY))
            form_layout.addRow(lbl, widget)

        add_row("Adresse e-mail", self.email)
        add_row("Code de réinitialisation", self.code)
        add_row("Nouveau mot de passe", self.new1)
        add_row("Confirmation du mot de passe", self.new2)
        card_layout.addLayout(form_layout)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size:12px;")
        card_layout.addWidget(self.status)
        layout.addWidget(card)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(0, 0, 0, 0)
        self.btn_send = QPushButton("Envoyer le code")
        self.btn_send.setMinimumHeight(46)
        self.btn_send.setStyleSheet(Styles.get_button_style(primary=True))
        self.btn_verify = QPushButton("Changer le mot de passe")
        self.btn_verify.setMinimumHeight(46)
        self.btn_verify.setStyleSheet(Styles.get_button_style(primary=False))
        self.btn_close = QPushButton("Fermer")
        self.btn_close.setMinimumHeight(46)
        self.btn_close.setStyleSheet(Styles.get_button_style(primary=False))
        for btn in (self.btn_send, self.btn_verify, self.btn_close):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row.addWidget(btn)
        layout.addLayout(row)

        self.btn_send.clicked.connect(self._send_code)
        self.btn_verify.clicked.connect(self._change_password)
        self.btn_close.clicked.connect(self.reject)

    def _send_code(self):
        email = self.email.text().strip()
        if not email:
            QMessageBox.warning(self, "Email manquant", "Veuillez saisir votre e-mail.")
            return
        ok = self.auth.send_reset_code(email)
        if ok:
            QMessageBox.information(self, "Envoyé", "Code envoyé par e-mail.")
            self.status.setText("Code envoyé. Vérifiez votre boîte mail.")
            key = getattr(self.auth, "_key", lambda x: x)(email)
            pending = getattr(self.auth, "pending_reset", {}).get(key)
            if pending:
                self.status.setText(f"Code envoyé (aussi affiché ici pour vérification) : {pending.get('code')}")
            self._start_cooldown()
        else:
            # Provide developer fallback if email not sent but code generated
            key = getattr(self.auth, "_key", lambda x: x)(email)
            pending = getattr(self.auth, "pending_reset", {}).get(key)
            if pending:
                QMessageBox.warning(
                    self,
                    "Email non envoyé",
                    f"Aucun e-mail n'a pu être envoyé mais un code est disponible : {pending.get('code')}\n"
                    "Utilisez ce code pour réinitialiser votre mot de passe."
                )
                self.status.setText(f"Code temporaire : {pending.get('code')}")
                self._start_cooldown()
            else:
                QMessageBox.warning(self, "Introuvable", "Aucun compte avec cet e-mail.")

    def _change_password(self):
        email = self.email.text().strip()
        code = self.code.text().strip()
        n1 = self.new1.text()
        n2 = self.new2.text()

        if not (email and code and n1 and n2):
            QMessageBox.warning(self, "Champs vides", "Tous les champs sont requis.")
            return
        if n1 != n2:
            QMessageBox.warning(self, "Non identiques", "Les mots de passe ne correspondent pas.")
            return
        if len(n1) < 8:
            QMessageBox.warning(self, "Trop court", "Le mot de passe doit contenir au moins 8 caractères.")
            return

        ok = self.auth.update_password_with_code(email, code, n1)
        if ok:
            QMessageBox.information(self, "Succès", "Mot de passe mis à jour. Vous pouvez vous connecter.")
            self.accept()
        else:
            QMessageBox.warning(self, "Échec", "Code invalide/expiré ou erreur.")

    def _start_cooldown(self):
        self.remaining = self.COOLDOWN
        self.btn_send.setEnabled(False)
        self._update_status()
        self.timer.start(1000)

    def _tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.btn_send.setEnabled(True)
            self.status.setText("Vous pouvez renvoyer un code.")
            self.btn_send.setText("Envoyer le code")
        else:
            self._update_status()

    def _update_status(self):
        self.status.setText(f"Renvoyer disponible dans {self.remaining}s…")
        self.btn_send.setText(f"Envoyer ({self.remaining}s)")
