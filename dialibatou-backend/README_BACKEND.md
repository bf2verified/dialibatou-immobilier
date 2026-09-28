# 🐍 Backend DIALIBATOU — FastAPI + PostgreSQL

API REST du site **DIALIBATOU BTP IMMOBILIER**. Elle remplace l'ancien stockage
`localStorage` (et l'ancien backend MongoDB) par une base **PostgreSQL locale**
consultable via **pgAdmin**.

## Prérequis

- PostgreSQL local installé + service démarré (ex. `postgresql-x64-18`, port **5432**)
- pgAdmin pour visualiser la base
- Python **3.11+** (testé sur 3.14)

## Démarrage complet

```bash
# 1) Creer la base dialibatou_db (dans pgAdmin ou psql) :
#    CREATE DATABASE dialibatou_db;

# 2) Environnement Python
cd dialibatou-backend
python -m venv venv
venv\Scripts\activate          # Windows (source venv/bin/activate sous Linux/Mac)
pip install -r requirements.txt

# 3) Configuration
copy .env.example .env         # Puis editer DATABASE_URL (mot de passe postgres)

# 4) Tables + donnees par defaut (60 proprietes, 8 lots, 1 admin)
python seed.py

# 5) Lancer l'API
uvicorn main:app --reload --port 8001
```

- **Swagger UI** : http://localhost:8001/docs
- **Santé** : http://localhost:8001/api/health → `{"status":"ok"}`
- **Fichiers uploadés** : http://localhost:8001/uploads/images/...

## Endpoints

| Méthode | URL | Accès | Description |
|---|---|---|---|
| GET | `/api/health` | public | Sante de l'API |
| GET | `/api/properties` | public | Liste des proprietes |
| GET | `/api/properties/{id}` | public | Une propriete |
| POST | `/api/properties` | 🔒 JWT | Creer une propriete |
| PUT | `/api/properties/{id}` | 🔒 JWT | Modifier |
| DELETE | `/api/properties/{id}` | 🔒 JWT | Supprimer |
| POST | `/api/properties/{id}/view` | public | Incrementer les vues |
| GET | `/api/lots` | public | Liste des lots |
| POST/PUT/DELETE | `/api/lots[/{id}]` | 🔒 JWT | CRUD lots |
| POST | `/api/messages` | public | Formulaire de contact (anti-spam 429) |
| GET | `/api/messages` | 🔒 JWT | Boîte de reception admin |
| PUT/DELETE | `/api/messages/{id}` | 🔒 JWT | Lu/non-lu, supprimer |
| POST | `/api/upload/image` | 🔒 JWT | Image (max 5 Mo) |
| POST | `/api/upload/video` | 🔒 JWT | Video (max 50 Mo) |
| POST | `/api/auth/login` | public | Connexion admin → JWT |

## Anti-spam (formulaire de contact)

`POST /api/messages` est protégé par une limitation à fenêtre glissante d'1 heure :

| Variable | Défaut | Rôle |
|---|---|---|
| `RATE_LIMIT_ENABLED` | `true` | `false` = désactive la limite (pratique en dev) |
| `MESSAGES_PER_HOUR_IP` | `5` | Messages maximum par adresse IP / heure |
| `MESSAGES_PER_HOUR_EMAIL` | `3` | Messages maximum par email / heure |

Au-delà, l'API répond **429 Too Many Requests** avec l'en-tête `Retry-After: 3600`, et
le frontend affiche un message clair (« Vous avez déjà envoyé plusieurs messages
récemment ») au lieu d'un échec silencieux.

> La limite est **en mémoire** : elle est remise à zéro au redémarrage de l'API
> (suffisant pour un site local / mono-instance). Pour une architecture multi-instances,
> remplacer par un compteur Redis.

## Authentification

```bash
# Le mot de passe est celui defini dans dialibatou-backend/.env (ADMIN_PASSWORD)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<VOTRE_MOT_DE_PASSE>"}'
# -> {"access_token":"...", "token_type":"bearer", "username":"admin"}
```

Ensuite, sur les routes 🔒 : `-H "Authorization: Bearer <access_token>"`.
Dans Swagger : bouton **Authorize** 🔒 en haut de `/docs`.

Le mot de passe est stocké **hashé bcrypt** dans la table `admins`
(identifiants pilotés par `ADMIN_USERNAME` / `ADMIN_PASSWORD` dans `.env`).

## Uploads

Les fichiers sont écrits sur disque (`uploads/images/<uuid>.jpg`,
`uploads/videos/<uuid>.mp4`) et **jamais** encodés en base64 en base.
L'API renvoie une URL relative (`/uploads/...`) que le frontend prefixe avec
`API_URL`.

## Tests

```bash
# Backend lance sur le port 8001, puis :
python backend_test.py          # a la racine du depot
```

## Variables d'environnement (`.env`)

Voir `.env.example` : `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`,
`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ALLOWED_ORIGINS`.

## Structure

```
dialibatou-backend/
├── main.py            # Point d'entree FastAPI (CORS, routers, /uploads statique)
├── database.py        # Connexion PostgreSQL (SQLAlchemy + psycopg)
├── models.py          # Modeles : Property, Lot, Message, PropertyView, Admin
├── schemas.py         # Schemas Pydantic (validation stricte, anti-base64)
├── routers/
│   ├── auth.py        # Login bcrypt + JWT + dependency get_current_user
│   ├── properties.py  # CRUD /api/properties + /view
│   ├── lots.py        # CRUD /api/lots
│   ├── messages.py    # /api/messages (public + admin)
│   └── uploads.py     # /api/upload/image|video (5 Mo / 50 Mo)
├── seed.py            # 60 proprietes + 8 lots + 1 admin
├── seed_data.json     # donnees extraites du site
├── uploads/{images,videos}/
├── .env.example
├── requirements.txt
└── README_BACKEND.md
```
