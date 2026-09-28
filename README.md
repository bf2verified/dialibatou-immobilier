# 🏠 DIALIBATOU BTP IMMOBILIER

Site web officiel de l'agence immobilière **DIALIBATOU BTP IMMOBILIER** (Dakar, Sénégal).

![DIALIBATOU](https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800)

## ✨ Fonctionnalités

- Page d'accueil (hero, statistiques, biens en vedette) avec **recherche fonctionnelle** (transaction / type / quartier)
- Catalogue de biens : filtres avancés, tri (nouveautés, prix, popularité), chips de filtres actifs, vue grille/carte
- Pages détail : galerie photos/vidéos au clavier, **biens similaires**, bouton Partager (lien profond), barre Appeler/WhatsApp sur mobile
- Pages Services, Contact (formulaire → base PostgreSQL, pré-rempli depuis un bien), Coopérative (8 lotissements)
- Espace **Administration** sécurisé (JWT) : CRUD propriétés/lots, messages, statistiques
- Upload de photos/vidéos **côté serveur** (plus de base64 ni de `QuotaExceededError`)
- **URL partageables** (`#/biens`, `#/bien/12`) + bouton « précédent » du navigateur
- Accessibilité : lien d'évitement, navigation clavier, `aria-*`, focus visible, contrastes
- Performance : `lazy loading`, repli d'image, squelettes de chargement, preconnect CDN
- Design responsive, mode sombre, favoris — **60 propriétés réalistes** à Dakar

## 🛠 Stack

| Couche | Technologie |
|---|---|
| Frontend | `index.html` (React 18 + Tailwind via CDN) + `api.js` (client REST) |
| Backend | **FastAPI** + SQLAlchemy (`dialibatou-backend/`) |
| Base de données | **PostgreSQL locale** (`dialibatou_db`, consultable via pgAdmin) |
| Auth | bcrypt + JWT (`POST /api/auth/login`) |
| Tests | `backend_test.py` (requêtes REST, seuil ≥ 90 %) |
| Déploiement | Vercel (statique) — le backend tourne en local/serveur séparé |

## 🚀 Démarrage

### Démarrage rapide (Windows)

```powershell
.\demarrer.ps1      # seed + API (8001) + site (5500) + tests automatiques
.\arreter.ps1       # arrete les processus
```

### Démarrage pas à pas

#### 1. Base de données (pgAdmin)

```sql
-- La base dialibatou_db est deja creee. Pour la recreer sur un autre poste :
CREATE ROLE dialibatou WITH LOGIN PASSWORD '<mot_de_passe>';   -- 01_create_role.sql
CREATE DATABASE dialibatou_db OWNER dialibatou;               -- 02_create_db.sql
```

### 2. Backend FastAPI

```bash
cd dialibatou-backend
python -m venv venv
venv\Scripts\activate           # Windows (source venv/bin/activate ailleurs)
pip install -r requirements.txt
copy .env.example .env          # Adapter DATABASE_URL si besoin (deja pre-rempli)
python seed.py                  # 60 proprietes + 8 lots + 1 admin (bcrypt)
uvicorn main:app --reload --port 8001
```

- Swagger UI : <http://localhost:8001/docs>
- Santé : <http://localhost:8001/api/health> → `{"status":"ok"}`

### 3. Frontend

```bash
# A la racine du depot (dossier contenant index.html + api.js)
python -m http.server 5500
# Ouvrir http://localhost:5500
```

L'URL du backend se configure **une seule fois** (voir `api.js`) :

```html
<script>window.DIALIBATOU_API_URL='https://api.mondomaine.com';</script>
<!-- avant <script src="api.js"></script> ; defaut : http://localhost:8001 -->
```

## 🧪 Tests

```bash
# Backend lance sur le port 8001, puis a la racine :
python backend_test.py
# > Success Rate: >= 90%, aucun probleme CRITICAL
```

Tests couverts : health, login JWT, propriétés (≥ 13, structure), lots, CRUD + 401
sans JWT, vues, messages (POST/GET/PUT/DELETE), upload image (multipart + accès
public + refus sans JWT).

## 🔐 Comptes & sécurité

- Compte admin : identifiant `admin`, mot de passe défini par vous dans
  `ADMIN_PASSWORD` (`dialibatou-backend/.env`, **non versionné**), stocké **hashé bcrypt** en base
- Le mot de passe n'existe **plus dans le code JavaScript** du site
- Pour régénérer un mot de passe : `python -c "import secrets;print(secrets.token_urlsafe(15))"`
  puis mettez-le dans `.env` et relancez `python seed.py --force` (ou `seed.py` après suppression de l'admin)
- CORS borné via `ALLOWED_ORIGINS` ; uploads limités à 5 Mo (image) / 50 Mo (vidéo)
- **Anti-spam** sur le formulaire : 5 messages/heure/IP et 3/heure/email (fenêtre glissante), réponse **429** claire côté navigateur — réglages dans `RATE_LIMIT_*` du `.env`
- ⚠️ En production : changez `JWT_SECRET`, `ADMIN_PASSWORD` **et** le mot de passe du rôle
  SQL `dialibatou` (présent en clair dans `01_create_role.sql`, à supprimer du dépôt).

## 📁 Structure

```
dialibatou-immobilier/
├── index.html            # Application React (design identique a l'original)
├── api.js                # Client API (API_URL, mediaUrl, JWT)
├── backend_test.py       # Tests d'integration (>= 90%)
├── seed_data.json        # donnees extraites (60 proprietes, 8 lots)
├── AUDIT_REPORT.md       # Rapport d'audit + bugs corriges
├── dialibatou-backend/   # Backend FastAPI + PostgreSQL (voir README_BACKEND.md)
├── frontend/ , backend/  # Anciennes versions (MongoDB / hybride) — archivees
└── vercel.json           # Deploiement statique
```

## 📄 Licence

© 2024 DIALIBATOU BTP IMMOBILIER. Tous droits réservés.

👨‍💻 Développé par **BF2BTRADING - Solutions digitales pour l'Afrique**
