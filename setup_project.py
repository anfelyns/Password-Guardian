import os

TREE = [
    "backend_api",
    "src",
    "src/auth",
    "src/backend",
    "src/gui",
    "src/gui/components",
    "src/gui/styles",
]
FILES = [
    "main.py","requirements.txt","start_securevault.py","setup_email.py","setup_project.py",
    "README.md","EMAIL_SETUP_GUIDE.md","COMPLETE_SETUP_GUIDE.md","PROJECT_SUMMARY.md",
    "backend_api/app.py","backend_api/db.py",
    "src/__init__.py",
    "src/auth/__init__.py","src/auth/auth_manager.py",
    "src/backend/__init__.py","src/backend/auth.py","src/backend/api_client.py",
    "src/gui/__init__.py","src/gui/main_window.py",
    "src/gui/components/__init__.py","src/gui/components/sidebar.py","src/gui/components/password_list.py","src/gui/components/modals.py",
    "src/gui/styles/__init__.py","src/gui/styles/styles.py",
]

def touch(p): 
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): open(p,"w",encoding="utf-8").close()

if __name__ == "__main__":
    base = os.path.abspath(os.path.dirname(__file__))
    for d in TREE: os.makedirs(os.path.join(base,d), exist_ok=True)
    for f in FILES: touch(os.path.join(base,f))
    print("Project skeleton ensured.")
