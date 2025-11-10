# OpenDirecte

**OpenDirecte** est un ENT (Espace Numérique de Travail) open source pour écoles, collèges et lycées. C'est une alternative libre, simple et moderne à EcoleDirecte.

## 🌟 Caractéristiques

- **Open Source** : Licence AGPLv3
- **Monolithique** : Frontend et Backend intégrés sur un seul serveur Flask
- **Moderne** : Interface utilisateur avec TailwindCSS
- **Complet** : Gestion des utilisateurs, groupes, devoirs, notes, messages, calendrier
- **Extensible** : API REST documentée

## 🏗️ Architecture

### Stack Technique

- **Backend** : Flask + SQLAlchemy + Flask-JWT-Extended + Flask-Bcrypt
- **Base de données** : SQLite (par défaut)
- **Frontend** : HTML + TailwindCSS + Vanilla JavaScript
- **Authentification** : JWT (stockage localStorage)

### Structure du projet

```
opendirecte/
├── app.py                    # Application Flask principale
├── config.py                 # Configuration
├── core/                     # Modules core
│   ├── extensions.py         # Extensions Flask
│   ├── models.py            # Modèles de base de données
│   ├── permissions.py       # Gestion des permissions
│   └── utils.py             # Utilitaires
├── api/                      # API REST
│   ├── auth/                # Authentification
│   ├── users/               # Gestion utilisateurs
│   ├── groups/              # Gestion groupes
│   ├── feed/                # Fil d'actualités
│   ├── homeworks/           # Devoirs
│   ├── mail/                # Messagerie
│   ├── calendar/            # Calendrier
│   ├── notes/               # Notes
│   └── attachments/         # Pièces jointes
├── frontend/                 # Interface utilisateur
│   ├── index.html           # Page de connexion
│   ├── dashboard.html       # Tableau de bord
│   ├── homework.html        # Page devoirs
│   ├── messages.html        # Messagerie
│   ├── notes.html           # Notes
│   ├── grades.html          # Notes (vue détaillée)
│   ├── calendar.html        # Calendrier
│   ├── admin.html           # Interface d'administration
│   └── assets/              # CSS, JS
└── requirements.txt          # Dépendances Python
```

## 🚀 Installation

### Prérequis

- Python 3.11+
- pip

### Étapes

1. **Cloner le repository**
```bash
git clone https://github.com/ruikdev/Opendirecte.git
cd Opendirecte
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Lancer l'application**
```bash
python app.py
```

L'application sera accessible sur `http://localhost:5000`

## 👤 Compte par défaut

Un compte administrateur est créé automatiquement au premier lancement :

- **Nom d'utilisateur** : `admin`
- **Mot de passe** : `admin123`

⚠️ **Important** : Changez ce mot de passe en production !

## 📚 API Documentation

### Endpoints disponibles

#### Authentification (`/api/v1/auth`)
- `POST /api/v1/auth/register` - Créer un utilisateur (admin)
- `POST /api/v1/auth/login` - Connexion → JWT
- `GET /api/v1/auth/me` - Utilisateur actuel
- `PUT /api/v1/auth/me` - Modifier profil
- `POST /api/v1/auth/refresh` - Rafraîchir token

#### Utilisateurs (`/api/v1/users`)
- `GET /api/v1/users` - Lister utilisateurs (admin)
- `POST /api/v1/users` - Créer utilisateur (admin)
- `GET /api/v1/users/<id>` - Détails utilisateur
- `PUT /api/v1/users/<id>` - Modifier utilisateur
- `DELETE /api/v1/users/<id>` - Supprimer utilisateur (admin)
- `PUT /api/v1/users/<id>/groups` - Gérer groupes

#### Groupes (`/api/v1/groups`)
- `GET /api/v1/groups` - Lister groupes
- `POST /api/v1/groups` - Créer groupe (admin)
- `GET /api/v1/groups/<id>` - Détails groupe
- `PUT /api/v1/groups/<id>` - Modifier groupe (admin)
- `DELETE /api/v1/groups/<id>` - Supprimer groupe (admin)

#### Fil d'actualités (`/api/v1/feed`)
- `GET /api/v1/feed` - Lister annonces
- `POST /api/v1/feed` - Publier annonce (admin)
- `PUT /api/v1/feed/<id>` - Modifier annonce (admin)
- `DELETE /api/v1/feed/<id>` - Supprimer annonce (admin)

#### Devoirs (`/api/v1/homeworks`)
- `GET /api/v1/homeworks` - Lister devoirs
- `POST /api/v1/homeworks` - Créer devoir (prof/admin)
- `PUT /api/v1/homeworks/<id>` - Modifier devoir
- `DELETE /api/v1/homeworks/<id>` - Supprimer devoir

#### Messagerie (`/api/v1/mail`)
- `GET /api/v1/mail/inbox` - Boîte de réception
- `GET /api/v1/mail/sent` - Messages envoyés
- `POST /api/v1/mail/send` - Envoyer message
- `GET /api/v1/mail/<id>` - Lire message
- `DELETE /api/v1/mail/<id>` - Supprimer message

#### Calendrier (`/api/v1/calendar`)
- `GET /api/v1/calendar` - Lister événements
- `POST /api/v1/calendar/import` - Importer .ics (admin)
- `DELETE /api/v1/calendar/<id>` - Supprimer événement (admin)

#### Notes (`/api/v1/notes`)
- `GET /api/v1/notes` - Lister notes
- `POST /api/v1/notes` - Ajouter note (prof/admin)
- `PUT /api/v1/notes/<id>` - Modifier note
- `DELETE /api/v1/notes/<id>` - Supprimer note

#### Pièces jointes (`/api/v1/attachments`)
- `POST /api/v1/attachments/upload` - Upload fichier
- `GET /api/v1/attachments/<id>` - Télécharger fichier

### Authentification JWT

Toutes les requêtes API (sauf `/auth/login`) nécessitent un token JWT dans le header :

```
Authorization: Bearer <token>
```

Le token JWT contient :
```json
{
  "user_id": 1,
  "role": "prof",
  "groups": ["3A", "club_IA"]
}
```

## 🔐 Rôles et Permissions

### Rôles disponibles
- **eleve** : Élève
- **prof** : Professeur
- **admin** : Administrateur

### Permissions par rôle
- **Élève** : Consulter ses devoirs, notes, messages, calendrier
- **Professeur** : Créer devoirs, notes pour ses groupes
- **Admin** : Accès complet à toutes les fonctionnalités

## 🛠️ Développement

### Variables d'environnement

Créer un fichier `.env` :

```env
FLASK_ENV=development
SECRET_KEY=votre-clé-secrète
JWT_SECRET_KEY=votre-clé-jwt
DATABASE_URL=sqlite:///opendirecte.db
```

### Commandes utiles

```bash
# Lancer en mode développement
python app.py

# Lancer avec Flask CLI
export FLASK_APP=app.py
flask run

# Mode debug
export FLASK_ENV=development
flask run --debug
```

## 📝 Licence

Ce projet est sous licence **AGPLv3**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📧 Contact

Projet maintenu par [@ruikdev](https://github.com/ruikdev)

## 🙏 Remerciements

Merci à tous les contributeurs qui ont participé au développement d'OpenDirecte !

---

**OpenDirecte** - Une alternative libre et open source pour l'éducation 🎓
