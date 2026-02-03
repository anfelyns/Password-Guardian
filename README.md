# Password Guardian

A desktop password manager with a Flask API backend and a PyQt5 desktop UI.
It stores credentials securely, supports categories and favorites, and includes
auditing, import/export, and multi‑factor authentication options.

## Features
- Secure vault with encrypted passwords (server‑side encryption)
- Desktop UI with sidebar, search, cards, and modals
- Categories (built‑in + custom), favorites, and trash
- Password strength scoring + statistics dashboard
- Add, edit, reveal, copy, and autofill actions
- Import / export flows
- Email verification codes and 2FA flows
- Audit log (journal) and device/session management

## Tech Stack
- Backend: Flask REST API
- Frontend: PyQt5
- Database: MySQL (default) or SQLite (local)

## Quick Start
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python start_PasswordGuardian.py
```
If you do not have `start_PasswordGuardian.py`, use:
```bash
python start_securevault.py
```

## Environment Configuration
Create a `.env` file (do not commit it):
```
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_NAME=Password Guardian
SMTP_FROM_EMAIL=
```
This enables email verification codes and password reset.

## Backend Notes
The backend runs on localhost and serves the API used by the desktop app.
Make sure the database is configured and reachable. If you use SQLite, ensure
the database file is writable in the project directory.

## Common Tasks
- Run the UI: `python start_PasswordGuardian.py`
- Run API only: `python backend_api/app.py`
- Reset local DB: remove the local database file

## Troubleshooting
- If email verification fails, check SMTP settings in `.env`.
- If tables are missing, run migrations or recreate the local DB.
- If the UI shows encoding issues, ensure files are saved in UTF‑8.

## License
Private project. Add a license if you plan to distribute.
