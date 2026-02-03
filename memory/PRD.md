# DIALIBATOU BTP IMMOBILIER - PRD

## Problème Original
Le site DIALIBATOU BTP IMMOBILIER stockait toutes les données (propriétés, lotissements) dans le **localStorage du navigateur**. Conséquence : les fichiers/données ajoutés par l'admin n'étaient visibles que sur SON navigateur, pas pour les visiteurs du site.

## Solution Implémentée
Migration vers une architecture **Backend API + MongoDB** pour stocker les données côté serveur.

---

## Architecture Technique

### Stack
- **Frontend**: React (via CDN) + Tailwind CSS - Fichier HTML unique
- **Backend**: FastAPI (Python)
- **Base de données**: MongoDB
- **Ports**: Frontend :3000, Backend :8001

### Endpoints API
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/properties | Liste des propriétés |
| POST | /api/properties | Ajouter une propriété |
| PUT | /api/properties/{id} | Modifier une propriété |
| DELETE | /api/properties/{id} | Supprimer une propriété |
| GET | /api/lots | Liste des lotissements |
| POST | /api/lots | Ajouter un lotissement |
| PUT | /api/lots/{id} | Modifier un lotissement |
| DELETE | /api/lots/{id} | Supprimer un lotissement |
| POST | /api/reset | Réinitialiser les données |

---

## Fonctionnalités Implémentées

### Core (Complétées)
- [x] API REST pour propriétés (CRUD)
- [x] API REST pour lotissements (CRUD)
- [x] Stockage MongoDB persistant
- [x] Interface admin avec authentification (mot de passe: dialibatou2024)
- [x] Ajout/modification/suppression de propriétés via admin
- [x] Upload d'images (Base64)
- [x] Export/Import JSON des données
- [x] Synchronisation temps réel frontend-backend

### Frontend (Existant)
- [x] Page d'accueil avec recherche
- [x] Catalogue de biens avec filtres
- [x] Page détail propriété
- [x] Page Coopérative d'habitat
- [x] Page Services
- [x] Page Contact avec WhatsApp
- [x] Mode sombre
- [x] Design responsive

---

## Fichiers Clés

```
/app/
├── backend/
│   ├── server.py          # API FastAPI
│   ├── requirements.txt   # Dépendances Python
│   └── .env               # MONGO_URL, DB_NAME
├── frontend/
│   ├── public/
│   │   └── index.html     # Site complet (React via CDN)
│   ├── src/
│   │   └── setupProxy.js  # Proxy API
│   └── .env               # REACT_APP_BACKEND_URL
└── dialibatou-site/
    └── index.html         # Copie synchronisée
```

---

## Données par Défaut
- 12 propriétés immobilières (appartements, villas, terrains, bureaux)
- 8 lotissements coopérative (Bambilor, Thiès, Diass, etc.)

---

## Configuration Production

Pour déployer en production, modifier l'URL de l'API dans `/app/frontend/public/index.html`:
```javascript
window.REACT_APP_BACKEND_URL = 'https://votre-api-url.com';
```

---

## Date
- Implémentation: 3 Février 2026

## Backlog P1/P2
- [ ] P1: Authentification admin sécurisée (JWT)
- [ ] P1: Upload images vers stockage cloud (S3/Cloudinary)
- [ ] P2: Notifications par email lors de nouveau contact
- [ ] P2: Statistiques de visites avancées
- [ ] P2: Gestion multi-utilisateurs admin
