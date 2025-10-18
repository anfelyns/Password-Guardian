# src/gui/main_window.py – Password Guardian main window

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
                    border-radius:10px; padding:10px;}}
            QMenu::item {{padding:8px 15px; border-radius:8px; color:{Styles.TEXT_PRIMARY};}}
            QMenu::item:selected {{background:rgba(59,130,246,0.25);}}
        """)
        head = QAction(f"👋 {self.username}", self); head.setEnabled(False)
        menu.addAction(head); menu.addSeparator()
        act_stats = QAction("📊 Mes statistiques", self)
        act_stats.triggered.connect(self.show_statistics.emit)
        menu.addAction(act_stats); menu.addSeparator()
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

    # ---------------- UI ----------------
    def _init_ui(self):
        self.setWindowTitle("Password Guardian")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0a1628, stop:1 #1a2942);
            }
        """)
        c = QWidget(); self.setCentralWidget(c)
        main = QVBoxLayout(c); main.setContentsMargins(20,20,20,20)

        # Header
        h = QWidget(); h_lay = QHBoxLayout(h)
        ico = QLabel("🛡️"); ico.setStyleSheet("font-size:32px;")
        title = QLabel("Password Guardian")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color:{Styles.TEXT_PRIMARY};")
        h_lay.addWidget(ico); h_lay.addWidget(title)
        h_lay.addStretch()
        self.user_box = QHBoxLayout(); self.user_widget = QWidget()
        self.user_widget.setLayout(self.user_box); h_lay.addWidget(self.user_widget)
        main.addWidget(h)

        # Content
        body = QHBoxLayout()
        self.sidebar = Sidebar()
        self.sidebar.category_changed.connect(self.on_category_changed)
        self.sidebar.add_password_clicked.connect(self.show_add_password_modal)
        body.addWidget(self.sidebar)

        self.password_list = PasswordList()
        self.password_list.copy_password.connect(self.on_copy_password)
        self.password_list.view_password.connect(self.on_view_password)
        self.password_list.edit_password.connect(self.on_edit_password)
        self.password_list.delete_password.connect(self.on_delete_password)
        self.password_list.favorite_password.connect(self.on_favorite_password)
        if hasattr(self.password_list, "restore_password"):
            self.password_list.restore_password.connect(self.on_restore_password)

        frame = QFrame(); f_lay = QVBoxLayout(frame)
        f_lay.setContentsMargins(0,0,0,0); f_lay.addWidget(self.password_list)
        body.addWidget(frame,1)
        main.addLayout(body)

    # ---------------- Authentication ----------------
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
            QMessageBox.warning(self, "Erreur", result["error"]); return
        if not result.get("2fa_sent"):
            QMessageBox.warning(self, "Erreur", "Impossible d'envoyer le code 2FA"); return
        user = result.get("user"); self._show_2fa(user)

    def _show_2fa(self, user):
        dlg = TwoFactorModal(user["email"], "<code envoyé par email>", self)
        def verify():
            code = dlg.code_input.text().strip()
            if not code or len(code)!=6:
                QMessageBox.warning(self,"Code invalide","Code 6 chiffres requis"); return
            if self.auth.verify_2fa_email(user["email"], code):
                dlg.accept(); self.finalize_login(user)
            else:
                QMessageBox.warning(self,"Erreur","Code invalide ou expiré")
        try: dlg.code_verified.disconnect()
        except: pass
        dlg.code_verified.connect(verify)
        if dlg.exec_()!=QDialog.Accepted: self.show_auth_flow()

    def on_register_attempt(self,name,email,password):
        ok,msg,extra=self.auth.register_user(name,email,password)
        if not ok:
            QMessageBox.warning(self,"Inscription",msg);return
        QMessageBox.information(self,"Succès","✅ Vérifiez votre email pour confirmer le compte")
        self.show_auth_flow()

    def finalize_login(self,user):
        name=(user.get("username") or user.get("email","").split("@")[0]).capitalize()
        initials=(name[:2] or "US").upper()
        for i in reversed(range(self.user_box.count())):
            w=self.user_box.itemAt(i).widget()
            if w: w.setParent(None)
        self.current_user={"id":user["id"],"username":name,"email":user["email"],
                           "name":name,"initials":initials}
        prof=UserProfileWidget(name,initials,self)
        prof.logout_clicked.connect(self.on_logout)
        prof.show_statistics.connect(self.show_statistics_modal)
        self.user_box.addWidget(prof)
        self.load_passwords()
        QMessageBox.information(self,"Bienvenue",
            f"✅ Bienvenue {name}! Vous êtes connecté à Password Guardian.")

    # ---------------- Password actions ----------------
    def load_passwords(self):
        if not self.current_user: return
        ok,msg,pwds=self.api_client.get_passwords(self.current_user["id"])
        self._all_passwords=pwds if ok else []
        self.password_list.load_passwords(self._all_passwords)
        counts={k:0 for k in["all","work","personal","finance","game","study","favorites"]}
        counts["all"]=len(self._all_passwords)
        for p in self._all_passwords:
            c=p.get("category")
            if c in counts: counts[c]+=1
            if p.get("favorite"): counts["favorites"]+=1
        self.sidebar.update_counts(counts)

    def on_category_changed(self,cat):
        base=self._all_passwords
        if cat=="all":f=base
        elif cat=="favorites":f=[p for p in base if p.get("favorite")]
        else:f=[p for p in base if p.get("category")==cat]
        self.password_list.load_passwords(f)

    def show_add_password_modal(self):
        dlg=AddPasswordModal(self)
        dlg.password_added.connect(self.on_password_added)
        dlg.exec_()

    def on_password_added(self,data):
        ok,msg,_=self.api_client.add_password(
            user_id=self.current_user["id"],
            site_name=data["site_name"],username=data["username"],
            password=data["password"],category=data["category"],favorite=False)
        if not ok:
            QMessageBox.warning(self,"Erreur",msg);return
        self.load_passwords()
        QMessageBox.information(self,"Succès","Mot de passe ajouté")

    def on_copy_password(self,pwd):
        QApplication.clipboard().setText(pwd)
        QMessageBox.information(self,"Copié","📋 Mot de passe copié!")

    def on_view_password(self,pdata):
        ViewPasswordModal(pdata,self).exec_()

    def on_edit_password(self,pid):
        pwd=next((p for p in self._all_passwords if p["id"]==pid),None)
        if not pwd: QMessageBox.warning(self,"Erreur","Introuvable"); return
        dlg=EditPasswordModal(pwd,self)
        def upd(pid,new,_):
            ok,msg,_=self.api_client.update_password(pid,pwd["site_name"],pwd["username"],
                new,pwd["category"],pwd.get("favorite",False))
            if ok:
                self.load_passwords()
                QMessageBox.information(self,"Succès","Mis à jour")
            else: QMessageBox.warning(self,"Erreur",msg)
        dlg.password_updated.connect(upd); dlg.exec_()

    def on_delete_password(self,pid:int):
        """
        Delete:
          - if not in 'trash' → move to Corbeille (soft)
          - if in 'trash' → permanent delete immediately
        """
        pwd=next((p for p in (self.password_list.passwords or self._all_passwords)
                  if p.get("id")==pid),None)
        cat=(pwd or {}).get("category","").lower()
        if cat=="trash":
            rep=QMessageBox.question(self,"Suppression définitive",
                "⚠️ Supprimer définitivement cet élément ?",
                QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if rep!=QMessageBox.Yes:return
            ok,msg=self.api_client.delete_password(pid,hard=True)
            if not ok: QMessageBox.warning(self,"Erreur",msg);return
            self.load_passwords()
            QMessageBox.information(self,"Supprimé","🗑️ Supprimé définitivement.")
        else:
            rep=QMessageBox.question(self,"Corbeille",
                "Envoyer à la Corbeille ?\n(Supprimé auto après 48 h)",
                QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
            if rep!=QMessageBox.Yes:return
            ok,msg=self.api_client.delete_password(pid,hard=False)
            if not ok: QMessageBox.warning(self,"Erreur",msg);return
            self.load_passwords()
            QMessageBox.information(self,"Corbeille","♻️ Déplacé dans la Corbeille.")

    def on_restore_password(self,pid,target="personal"):
        ok,msg=self.api_client.restore_password(pid,target)
        if not ok: QMessageBox.warning(self,"Erreur",msg);return
        self.load_passwords()
        QMessageBox.information(self,"Restauré","✅ Récupéré depuis la Corbeille.")

    def on_favorite_password(self,pid):
        p=next((x for x in self._all_passwords if x["id"]==pid),None)
        if not p:return
        fav=not p.get("favorite",False)
        ok,msg,_=self.api_client.update_password(pid,p["site_name"],p["username"],
            p["encrypted_password"],p["category"],fav)
        if ok:self.load_passwords()
        else: QMessageBox.warning(self,"Erreur",msg)

    # ---------------- Stats + Logout ----------------
    def show_statistics_modal(self):
        from PyQt5.QtWidgets import QGridLayout

        # ---- Dialog (force dark background) ----
        d = QDialog(self)
        d.setWindowTitle("📊 Statistiques — Password Guardian")
        d.setFixedSize(720, 520)
        d.setAttribute(Qt.WA_StyledBackground, True)
        d.setStyleSheet(f"""
            QDialog {{
                background: #0b1220;
                color: {Styles.TEXT_PRIMARY};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }}
            QLabel {{
                color: {Styles.TEXT_PRIMARY};
                background: transparent;
            }}
            QPushButton {{
                {Styles.get_button_style(primary=True)}
                min-height: 44px;
            }}
        """)

        layout = QVBoxLayout(d)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ---- Title ----
        title = QLabel("📊  Mes statistiques")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color: {Styles.TEXT_PRIMARY};")
        layout.addWidget(title)

        # ---- Stats grid ----
        passwords = self._all_passwords
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
            ("🗂️  Total", total, Styles.BLUE_PRIMARY),
            ("✅  Forts", strong, Styles.STRONG_COLOR),
            ("⚠️  Moyens", medium, Styles.MEDIUM_COLOR),
            ("❌  Faibles", weak, Styles.WEAK_COLOR),
            ("⭐  Favoris", favorites, Styles.BLUE_SECONDARY),
        ]:
            l, v = row(text, val, col)
            grid.addWidget(l, r, 0, alignment=Qt.AlignLeft)
            grid.addWidget(v, r, 1, alignment=Qt.AlignRight)
            r += 1

        layout.addLayout(grid)

        # ---- Score ----
        score_wrap = QWidget()
        score_wrap.setAttribute(Qt.WA_StyledBackground, True)
        score_wrap.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }
        """)
        swl = QHBoxLayout(score_wrap); swl.setContentsMargins(14, 10, 14, 10)

        score_label = QLabel("🛡️  Score de sécurité")
        score_label.setStyleSheet(f"color: {Styles.TEXT_SECONDARY}; font-size: 14px;")
        swl.addWidget(score_label, alignment=Qt.AlignLeft)

        if total > 0:
            security_score = int((strong / total) * 100)
        else:
            security_score = 0

        if security_score >= 80:
            score_color = Styles.STRONG_COLOR
        elif security_score >= 50:
            score_color = Styles.MEDIUM_COLOR
        else:
            score_color = Styles.WEAK_COLOR

        score_value = QLabel(f"{security_score}%")
        score_value.setStyleSheet(f"color: {score_color}; font-size: 26px; font-weight: 800;")
        swl.addWidget(score_value, alignment=Qt.AlignRight)

        layout.addWidget(score_wrap)

        layout.addStretch(1)

        # ---- Close ----
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(d.accept)
        layout.addWidget(close_btn)

        d.exec_()

    def on_logout(self):
        rep=QMessageBox.question(self,"Déconnexion","Se déconnecter ?",
                                 QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if rep!=QMessageBox.Yes:return
        self.current_user=None
        for i in reversed(range(self.user_box.count())):
            w=self.user_box.itemAt(i).widget()
            if w:w.setParent(None)
        self._all_passwords=[]; self.password_list.load_passwords([])
        self.show_auth_flow()