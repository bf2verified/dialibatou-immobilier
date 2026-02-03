# DIALIBATOU BTP IMMOBILIER - PRD

## Problème Original
Le site DIALIBATOU BTP IMMOBILIER stockait toutes les données (propriétés, lotissements) dans le **localStorage du navigateur**. Conséquence : les fichiers/données ajoutés par l'admin n'étaient visibles que sur SON navigateur, pas pour les visiteurs du site.

## Solution Implémentée
1. **Mode Hybride** : Le code supporte maintenant deux modes :
   - **Mode API** : Utilise un backend FastAPI + MongoDB (données persistantes côté serveur)
   - **Mode Local** : Utilise localStorage (mode par défaut pour Vercel/GitHub Pages)

2. **Nouveau Logo** : Logo officiel DIALIBATOU BTP IMMOBILIER remplacé

---

## Architecture Technique

### Stack
- **Frontend**: React (via CDN) + Tailwind CSS - Fichier HTML unique
- **Backend (optionnel)**: FastAPI (Python) + MongoDB
- **Hébergement actuel**: Vercel (site statique)

### Configuration API
Dans le fichier `index.html`, modifier cette ligne :
```javascript
window.REACT_APP_BACKEND_URL = ''; // Vide = mode localStorage
// window.REACT_APP_BACKEND_URL = 'https://votre-api.render.com'; // Mode API
```

### Endpoints API (si backend déployé)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/properties | Liste des propriétés |
| POST | /api/properties | Ajouter une propriété |
| PUT | /api/properties/{id} | Modifier une propriété |
| DELETE | /api/properties/{id} | Supprimer une propriété |
| GET | /api/lots | Liste des lotissements |
| POST/PUT/DELETE | /api/lots/{id} | CRUD lotissements |

---

## Fichiers Modifiés

### index.html (Principal)
- Nouveau logo : Image externe DIALIBATOU
- Hook `useData` : Mode hybride API/localStorage
- Configuration simple de l'URL backend

### Fichiers Backend (pour déploiement futur)
```
/app/backend/
├── server.py          # API FastAPI
├── requirements.txt   # Dépendances
└── .env               # MONGO_URL, DB_NAME
```

---

## Données par Défaut
- 60 propriétés immobilières (appartements, villas, terrains, bureaux)
- 8 lotissements coopérative (Bambilor, Thiès, Diass, etc.)

---

## Déploiement sur GitHub/Vercel

Le fichier `index.html` modifié peut être directement poussé sur GitHub.
Le site fonctionnera en mode localStorage par défaut.

**Pour activer le mode API** :
1. Déployer le backend sur Render/Railway
2. Modifier `REACT_APP_BACKEND_URL` dans index.html
3. Redéployer sur Vercel

---

## Date
- Implémentation: 3 Février 2026

## Complété
- [x] Analyse du problème de persistance
- [x] Implémentation backend FastAPI + MongoDB
- [x] Mode hybride API/localStorage
- [x] Nouveau logo DIALIBATOU officiel
- [x] Tests fonctionnels

## Backlog P1/P2
- [ ] P1: Déployer backend sur Render/Railway pour persistance serveur
- [ ] P1: Stockage images cloud (Cloudinary) au lieu de Base64
- [ ] P2: Authentification admin sécurisée (JWT)
- [ ] P2: Notifications email
