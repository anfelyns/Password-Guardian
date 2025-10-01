\# Configuration Base de Données - Password Guardian



\## 🗄️ Configuration MySQL XAMPP

\- \*\*Host:\*\* `localhost`

\- \*\*Port:\*\* `1234`

\- \*\*User:\*\* `root`

\- \*\*Password:\*\* `""` (vide)

\- \*\*Database:\*\* `password\_guardian`



\## 📊 Tables Créées

\- `users` - Gestion des utilisateurs

\- `passwords` - Stockage des mots de passe chiffrés

\- `sessions` - Gestion des sessions utilisateur

\- `activity\_logs` - Journal d'activité



\## 🚀 Utilisation

Le `MySQLDatabaseManager` dans `src/database/database\_manager.py` fournit toutes les opérations CRUD nécessaires.

