# 📋 RAPPORT D'AUDIT — DIALIBATOU BTP IMMOBILIER

**Date** : 28/09/2026
**Périmètre** : `index.html` (1631 lignes / 160 Ko), `backend_test.py`, `backend/server.py`, `frontend/`, `vercel.json`, `README.md`, `.gitignore`
**Contexte** : Migration de la persistance `localStorage` → PostgreSQL local + FastAPI

---

## 1. ÉTAT DES LIEUX : 3 ARCHITECTURES INCOHÉRENTES DÉPÔT

| Fichier | Réalité | Problème |
|---|---|---|
| `index.html` (racine) | Version **déployée sur Vercel** (`vercel.json` → `outputDirectory: "."`) | 100 % `localStorage`, **aucune** appel API |
| `frontend/public/index.html` | Version antérieure avec mode hybride API (`window.REACT_APP_BACKEND_URL`) | **Pas déployée**, fallback localStorage maintenu |
| `backend/server.py` | Backend FastAPI + **MongoDB** (pymongo), port 8001 | ❌ Pas PostgreSQL, pas de JWT, pas de `/api/messages`, pas de tracking vues, `/api/upload` renvoie du **base64** |
| `memory/PRD.md` | Documentation de la solution hybride MongoDB (03/02/2026) | Backlog P1/P2 jamais traité (déploiement backend, cloud storage, JWT) |

**Cause racine de la panne** : le backend (MongoDB) n'est pas celui demandé ET le frontend déployé ne lui parle jamais.

---

## 2. BUGS CRITIQUES

### BUG #1 — Les photos/vidéos ajoutées via l'admin ne s'affichent pas ✅ CONFIRMÉ
- **`handlePhotoUpload`** (`index.html` L1176) : `FileReader.readAsDataURL` → chaque photo devient une *data URL* base64 de plusieurs Mo dans `f.im`.
- **`saveData`** (L99) : `localStorage.setItem(...)` **sans `try/catch`** → dès ~5 Mo de quota dépassé, `QuotaExceededError` est levée **AVANT** `setProperties` (L134→135 dans `updateProps`) → rien n'est persisté, rien n'est mis en état, erreur silencieuse en console, l'admin croit que l'enregistrement a marché.
- **Aucune limite de taille pour les images** (contrairement aux vidéos) ; aucun contrôle `reader.onerror` → `uploading` reste bloqué à `true` en cas d'échec.
- **Pas de persistance serveur** : `props = data.properties || P` (L1604) → les visiteurs n'affichent que les 60 biens par défaut `P` ; les biens ajoutés par l'admin n'existent que dans SON navigateur.
- **Vidéos** : 50 Mo en base64 dans le localStorage = `QuotaExceededError` **garanti** (limite ~5-10 Mo).

### BUG #2 — Aucune persistance (Supabase expiré / localStorage) ✅ CONFIRMÉ
Aucune donnée métier n'est stockée côté serveur. Tout meurt au nettoyage du cache, au changement de navigateur ou d'ordinateur.

### BUG #3 — `backend_test.py` teste une API que le frontend n'utilise pas ✅ CONFIRMÉ
- Attend **13 propriétés** (L108-115) alors que le seed en contient **60** → issue HIGH → rapport en échec.
- Aucun test `/api/messages`, `/api/auth/login`, `/api/upload/image`, `/api/properties/{id}/view`.
- Aucun JWT alors que les CRUD seront protégés → le test de création recevrait **401**.
- Le test de santé est compatible (`GET /api/health` → 200 + `{"status": "ok"}`).


---

## 3. AUTRES BUGS ET RÉGRESSIONS DÉTECTÉS

| # | Bug | Localisation | Sévérité |
|---|---|---|---|
| B5 | **Mot de passe admin en clair dans le JS public** (`CO.adminPwd`) visible par tout visiteur (view-source) + bypass total : `sessionStorage.setItem('dialibatou_admin','true')` suffisait à ouvrir l'admin | L77, L1106, L1119 | 🔴 CRITIQUE |
| B6 | **`props.sort(...)` mute le React state en place** dans `StatsTab` → réordonne définitivement le tableau `P` (module-level) pour toute la session | L1520 | 🔴 |
| B7 | Messages de contact : écrits dans `localStorage` + ouverture WhatsApp. `CO.emailjsKey` **n'existe pas** → EmailJS jamais utilisé → l'admin ne voit **jamais** les messages des visiteurs alors que le site affiche "message envoyé" | L833-848, L1454 | 🔴 |
| B8 | Vues : `getViews/addView` en localStorage → statistiques **par navigateur**, double comptage `(p.vi||0)+getViews(id)`, jamais synchronisé avec une DB | L247-248, L525, L654 | 🟠 |
| B9 | `PropForm`/`LotForm` **définis dans le corps du composant `Admin`** → nouvelle référence de composant à chaque render → React démonte/remonte le formulaire → perte potentielle de saisie | L1169, L1293 | 🟠 |
| B10 | Sync inter-onglets par `dispatchEvent(new StorageEvent(...))` synthétique — hack non standard (fiable sur Chrome, fragile ailleurs) | L137, L142 | 🟡 |
| B11 | Héros : `<option>Achat</option>` alors que les biens utilisent `"Vente"` ; les 3 filtres du héros ne sont pas liés au state (le bouton Rechercher ne fait que naviguer) | L461 | 🟡 |
| B12 | Page détail sans deep-link : au reload, `sel=null` → écran "Non trouvé" | L659 | 🟡 |
| B13 | Import/Export JSON : n'importe ni messages ni vues ; l'export inclut les base64 (fichier monstrueux) | L1134-1151 | 🟡 |
| B14 | `StatsTab` : division par zéro si `props.length===0` → `width:NaN%` | L1552 | 🟡 |
| B15 | IDs hétérogènes : frontend génère `'p'+Date.now()` (**string**) vs schéma SQL `SERIAL` (**int**) → incohérence API | L1123 | 🟠 |
| B16 | `.gitignore` corrompu (lignes `-e` répétées, reste d'une commande `sed`) → risque de committer un `.env` | `.gitignore` | 🟠 (corrigé) |
| B17 | `backend/requirements.txt` = dump de 123 paquets (pandas, boto3, openai…), pas un vrai fichier de dépendances | — | 🟡 |
| B18 | `README.md` obsolète ("20 propriétés", aucune documentation backend) | — | 🟡 |
| B19 | Ancien backend MongoDB : CORS `allow_origins=["*"]` + `allow_credentials=True` (combinaison invalide/risquée), aucune validation de taille/type sur l'upload | `backend/server.py` L13-19, L247 | 🟠 |
| B20 | `Contact` : état `loading` géré mais le formulaire n'est pas bloqué pendant l'envoi | L824-849 | 🟡 |


---

## 4. PROBLÈMES DE PERFORMANCE

- **1631 lignes / 160 Ko dans un seul fichier HTML** : transpilation JSX **en client** via Babel Standalone à chaque chargement (lourd sur mobile), React + Tailwind en CDN non versionnés.
- Data URLs base64 dans le state React → `JSON.parse`/`JSON.stringify` lents et mémoire gaspillée.
- Images sans `loading="lazy"`.
- Aucun état *loading* dans `useData` → flash des données par défaut avant remplacement.
- Tableau `P` de 60 propriétés inline dans le bundle (acceptable en fallback, mais à ne jamais croiser avec les données DB).

---

## 5. INCOHÉRENCES `backend_test.py` ↔ FRONTEND ↔ BACKEND

1. Le frontend déployé n'appelle **aucune** API → les tests ne testent rien de ce qui est en production.
2. Comptage fixe de 13 propriétés au lieu d'un seuil dynamique (`>= 13` + validation de structure).
3. Absence de JWT → CRUD inutilisable avec le nouveau backend sécurisé.
4. Absence des nouveaux endpoints : `/api/messages`, `/api/auth/login`, `/api/upload/image`, `/api/upload/video`, `/api/properties/{id}/view`.
5. `backend/server.py` (référence historique) renvoie des **ids string** (`p173...`) alors que le schéma PostgreSQL demandé utilise `SERIAL` (int).

---

## 6. SÉCURITÉ

1. 🔴 Mot de passe admin en clair dans le JS public (B5) + flag `sessionStorage` contournable.
2. 🔴 Mot de passe à hasher (**bcrypt**) et stocké en table `admins`, vérifié côté serveur via `POST /api/auth/login` → JWT.
3. 🟠 CORS du backend à restreindre (localhost:5500, URLs Vercel) au lieu de `*`.
4. 🟠 Validation Pydantic stricte sur tous les inputs (prix ≥ 0, champs obligatoires, longueurs).
5. 🟠 Uploads : limiter à **5 Mo/image** et **50 Mo/vidéo**, valider extension + MIME, stocker sous nom `{uuid}.{ext}` (jamais le nom client).
6. 🟠 `.gitignore` corrompu (corrigé dans cette phase) → risque de fuite de `.env`.
7. 🟡 Pas de limitation de débit sur `/api/messages` (spam possible) — ✅ **corrigé** : 5 msg/h/IP et 3 msg/h/email, réponse 429 + `Retry-After` (voir §12).

---

## 7. CORRECTIONS APPORTÉES DANS CETTE PHASE (Phase 0)

- ✅ `index.backup.html` créé (copie intégrale de `index.html`, 160 631 octets).
- ✅ `.gitignore` réécrit (ignorait mal `*.env`, contenait des lignes corrompues `-e`) : `.env` exclu sauf `.env.example`, `venv/`, `__pycache__/`, uploads binaires.
- 📝 Le reste des corrections fait l'objet des Phases 1 à 6 du plan de migration validé.

---

## 8. PLAN DE CORRECTION (résumé)

| Phase | Action | Bugs traités |
|---|---|---|
| 1 | Backend FastAPI + PostgreSQL `dialibatou-backend/` (routers, JWT, uploads disque, seed) | #2, #3, B5, B7, B8, B15, B19 |
| 2 | Création DB `dialibatou_db` + tables + seed (60 propriétés, 8 lots, 1 admin) | #2 |
| 3 | Refactor `index.html` + `api.js` : API-first, multipart upload, contact via API, vues via API | #1, B7, B8, B9, B11, B12, B14, B20 |
| 4 | Sécurité : bcrypt, JWT, CORS, Pydantic strict, limites upload | B5, B19 |
| 5 | `backend_test.py` : comptage dynamique, JWT, nouveaux endpoints | #3 |

---

## 9. STATUT DES CORRECTIONS (apres migration)

| Bug | Correction appliquée | Statut |
|---|---|---|
| #1 Photos/vidéos non affichées | Upload **multipart** vers `/api/upload/image|video` → fichier sur disque (`uploads/<uuid>.ext`), URL relative en base, limite 5/50 Mo, plus aucun `readAsDataURL` | ✅ |
| #2 Persistance | Toute la donnee metier (properties, lots, messages, vues) est en **PostgreSQL** via `api.js` ; localStorage garde uniquement mode sombre / favoris / derniere page | ✅ |
| #3 backend_test.py | Reecrit : comptage **dynamique >= 13**, login JWT, messages, upload, vues, test 401 sans JWT, seuil **>= 90%**, message clair si :8001 muet | ✅ |
| B5 Mot de passe en clair | `CO.adminPwd` supprime ; login `POST /api/auth/login` + **bcrypt** en table `admins` + JWT sessionStorage ; bypass `dialibatou_admin` supprime | ✅ |
| B6 sort() mutatif | `[...props].sort(...)` (copie) dans `StatsTab` | ✅ |
| B7 Messages perdus | Contact → `POST /api/messages` (repli WhatsApp si API KO, avec console.warn) ; `MessagesTab` lit l'API | ✅ |
| B8 Vues locales | `POST /api/properties/{id}/view` ; `getViews/addView` supprimes ; compteur `vi` global en base | ✅ |
| B9 PropForm/LotForm remontes | Deplaces au **niveau module** (reference stable, aucun remount) — script `move_forms.py` | ✅ |
| B10 StorageEvent synthetique | Supprime avec le hook localStorage (la synchro inter-onglets n'est plus necessaire : l'API fait foi) | ✅ |
| B11 Héros "Achat" | Corrige en `<option>Vente</option>` (les filtres restent decoratifs, comme avant — design preserve) | ✅ |
| B12 Detail perdu au reload | Persistance `dialibatou_page` / `dialibatou_sel` / `dialibatou_locality` + rehydratation depuis l'API (retour accueil propre si bien supprime) | ✅ |
| B13 Import/Export | Export sans base64 (URLs) ; import via **POST en boucle** (ids ignores) | ✅ |
| B14 Division par zero | Garde `props.length? ... : '0%'` | ✅ |
| B15 IDs heterogenes | Ids **entiers SERIAL** cote API ; le frontend n'utilise plus `id:'p'+Date.now()` | ✅ |
| B16 .gitignore corrompu | Reecrit (`.env` ignore sauf `.env.example`, venv, uploads) | ✅ |
| B17 requirements.txt | Nouveau `dialibatou-backend/requirements.txt` minimal et epure (l'ancien `backend/requirements.txt` est archive tel quel) | ✅ |
| B18 README obsolete | Reecrit (60 proprietes, instructions pgAdmin/uvicorn/tests, config API_URL) | ✅ |
| B19 CORS/upload anciens | CORS borne par `ALLOWED_ORIGINS` ; validation MIME + taille + uuid sur les uploads (l'ancien `backend/server.py` MongoDB est remplace) | ✅ |
| B20 Bouton contact | Support `disabled` sur `Btn` + `disabled={loading}` pendant l'envoi | ✅ |
| EmailJS inutilise | Script CDN retire (aucune reference restante) | ✅ |

### Corrections supplementaires apportees
- `getImages()` prefixe les URL relatives `/uploads/...` avec `API_URL` (mediaUrl) — y compris la galerie video (3 endroits).
- Bouton admin « Réinitialiser » devient « Recharger PostgreSQL » (`data.refresh()`), plus de `resetData()` localStorage.
- L'import JSON n'ecrase plus la base : il **ajoute** chaque enregistrement via l'API (comportement documente).
- `extract_seed_data.py` : utilitaire pour regenerer `seed_data.json` depuis `index.html`.

### Non traite (volontairement, hors perimetre/pour valider ensemble)
- Découpage de `index.html` (1631 lignes) en modules React : recommande, mais modify le pipeline de deploiement (CDN + Babel) — a decider avec vous.
- ~~Limitation de débit sur `/api/messages` (anti-spam)~~ → ✅ fait, voir §12.
- L'ancien couple `backend/` (MongoDB) + `frontend/` reste dans le depot comme archive (non modifie).


---

## 10. VALIDATION FINALE (résultats réels)

**Environnement** : PostgreSQL 18.6 (localhost:5432) · Python 3.14.2 · FastAPI 0.141 ·
SQLAlchemy 2.1 · psycopg 3.3 · pydantic 2.13

| Critère d'acceptation | Résultat |
|---|---|
| Base `dialibatou_db` créée + tables visibles dans pgAdmin | ✅ 5 tables : `admins`, `lots`, `messages`, `properties`, `property_views` |
| Seed | ✅ 60 propriétés, 8 lots, 1 admin (hash bcrypt `$2b$12$…`) |
| `uvicorn main:app --port 8001` sans erreur | ✅ `/api/health` → `{"status":"ok","service":"DIALIBATOU BTP API"}` |
| Swagger UI | ✅ http://localhost:8001/docs (200) — 11 endpoints documentés |
| Site chargé avec les données de la DB | ✅ http://localhost:5500 (200, `api.js` chargé, config `DIALIBATOU_API_URL` présente) |
| Admin : propriété + 3 photos → visibles publiquement | ✅ uploads multipart → `/uploads/images/<uuid>.png`, propriété visible **sans JWT** par les visiteurs, 3 images servies en `image/png` |
| Lotissement | ✅ 8 lots seedés + CRUD `/api/lots`Operationnel |
| Message de contact → visible dans l'admin | ✅ `POST /api/messages` (public) → `GET /api/messages` (admin) |
| Persistance après rechargement / changement d'onglet | ✅ tout est en PostgreSQL ; localStorage = mode sombre, favoris, dernière page |
| `python backend_test.py` | ✅ **18/18 — 100,0 %** (seuil 90 %) |
| Vérification bout-en-bout complémentaire | ✅ **19/19** (JWT, 401 sans token, upload 5 Mo, vues, CORS, nettoyage) |
| Aucun `QuotaExceededError` | ✅ plus aucun `localStorage` métier ni base64 (validé par esbuild + E2E) |

**Bugs trouvés et corrigés pendant la validation** (ajoutés à la liste) :

| # | Bug | Correction |
|---|---|---|
| B21 | `run_upload_test` attendait toujours 200 : le cas « upload sans JWT » échouait à tort (94,4 % au lieu de 100 %) | paramètre `expected_status` |
| B22 | `backend_test.py` plantait (`UnicodeEncodeError`) si la sortie était redirigée (encodage cp1252) | `sys.stdout.reconfigure(encoding="utf-8")` |
| B23 | `data.lots` pouvait valoir `null` (chargement/API en panne) → `Cooperative` plantait sur `lots.reduce` | `data.lots || LOTS_INIT` dans `App` |

**Scripts de démarrage ajoutés** : `demarrer.ps1` (seed + API + site + tests en un clic)
et `arreter.ps1` (arrêt des processus 8001/5500).


---

## 11. AMÉLIORATIONS UI/UX APPLIQUÉES (post-migration)

Design, couleurs et navigation d'origine **inchangés** : uniquement de l Ergonomie,
de l'accessibilité, de la performance et de la conversion.

### Fondations
| Amélioration | Détail |
|---|---|
| Favicon + couleur de barre mobile | SVG inline (data URI) aux couleurs de la marque, `<meta name="theme-color">` |
| Preconnect CDN | `images.unsplash.com`, `img.youtube.com`, `fonts.gstatic.com` : jusqu'à ~30 % de LCP en moins |
| Lien d'évitement | « Aller au contenu principal » (clavier) + `<main id="main" tabIndex={-1}>` |
| Focus visible | Anneau doré `:focus-visible` sur toute la page (accessibilité clavier) |
| Bandeau « backend injoignable » | L'état `apiDown` existait mais n'était pas affiché : bandeau sticky avec **Réessayer** et fermeture |
| Squelettes de chargement | Classe `.skel` + `LoadingBar` en haut de l'accueil et du catalogue |
| Images robustes | Nouveau composant `Img` : `loading="lazy"`, `decoding="async"`, repli automatique sur l'image par défaut si un fichier est introuvable |

### Navigation & URL
| Amélioration | Détail |
|---|---|
| **Deep-linking par URL** | `#/accueil`, `#/biens`, `#/cooperative`, `#/services`, `#/contact`, `#/bien/<id>` — liens partageables + bouton « précédent » du navigateur qui fonctionne |
| Menu mobile | Ajout du lien WhatsApp, `aria-expanded`/`aria-controls`, fermeture par **Échap** |
| Navigation active | `aria-current="page"` sur l'onglet courant (desktop + mobile) |

### Accueil & catalogue
| Amélioration | Détail |
|---|---|
| **Filtres du héros fonctionnels** | Ils n'étaient que décoratifs : ils transmettent maintenant transaction / type / quartier à la page Biens (`HERO_FILTERS`) |
| Tri « Nouveautés » | Basé sur la vraie colonne `created_at` de PostgreSQL |
| Chips de filtres actifs | Chaque critère appliqué est visible et supprimable en un clic + « Tout effacer » |
| Reset complet | « Réinitialiser » efface aussi le tri (incohérence corrigée) |
| État vide utile | Message expliquant + 2 actions (élargir / parler à un conseiller) au lieu d'un vide |
| Compteur de résultats `aria-live` | Annoncé aux lecteurs d'écran |
| Pagination & vues | `aria-label`, `aria-current`, `aria-pressed` sur grille/carte |

### Fiche bien
| Amélioration | Détail |
|---|---|
| **Biens similaires** | 3 biens scorés (même quartier > même type > même transaction) : prolongement du temps passé et navigation interne |
| **Bouton Partager** | Copie le lien profond `#/bien/<id>` avec retour visuel « Lien copié ! » |
| **Barre d'action mobile** | Appeler / WhatsApp toujours accessibles en bas d'écran (`safe-area-inset` iOS) |
| Galerie clavier | ← → pour changer de média, **Échap** pour fermer, `role="dialog"` + `aria-modal` + aide invisible pour lecteurs d'écran |
| Image principale | Chargée en `eager` (c'est l'élément LCP de la page) |

### Formulaire de contact
| Amélioration | Détail |
|---|---|
| Pré-remplissage depuis une fiche | « Je suis intéressé par le bien … (réf. X) » pré-rempli : moins de saisie, plus de leads |
| Message d'erreur honnête | Si l'API est injoignable, on dit clairement que le message **n'a pas** été enregistré (avant : « Message envoyé ! » trompeur) |
| Distinction des modes d'envoi | Écran vert « Message envoyé » (base) vs ambre « WhatsApp ouvert » (repli) + bouton « Envoyer un autre message » |
| Compteur de caractères | `maxLength` aligné sur la validation serveur (5000), alerte rouge au-delà de 4500 |
| Accessibilité | `label htmlFor` + `id` sur les 5 champs, `role="alert"`, `aria-live`, mention RGPD |

### Administration
| Amélioration | Détail |
|---|---|
| Modales accessibles | `role="dialog"`, `aria-modal`, libellé, fermeture par **Échap** |

### Vérification
Compilation JSX validée par **esbuild** (212 ko, 0 erreur) et `node --check api.js` ;
`python backend_test.py` toujours à **100 %** (18/18) ; site servi sur
http://localhost:5500 avec toutes les fonctionnalités ci-dessus confirmées côté serveur.


---

## 12. PROTECTION ANTI-SPAM (formulaire de contact)

Dernier risque identifié lors de l'audit : `/api/messages` était ouvert **sans limite** —
un robot pouvait inonder la boîte de réception (table `messages`).

### Implémentation (`dialibatou-backend/routers/messages.py`)

Limitation à **fenêtre glissante d'1 heure**, appliquée côté serveur :

| Clé | Limite | Configurable via |
|---|---|---|
| Adresse IP | 5 messages / h | `MESSAGES_PER_HOUR_IP` |
| Email | 3 messages / h | `MESSAGES_PER_HOUR_EMAIL` |
| Activation | — | `RATE_LIMIT_ENABLED` (`false` en dev) |

Au-delà : **HTTP 429** + en-tête `Retry-After: 3600`, message explicite en français.

### Côté navigateur

Le formulaire distingue désormais les cas et ne ment plus sur l'état de l'envoi :

- **422** → « certains champs ont été refusés par le serveur »
- **429** → « vous avez déjà envoyé plusieurs messages récemment »
- **réseau/API KO** → « votre message n'a **PAS** été enregistré » + repli WhatsApp

### Test performed

```
envoi 1..5 -> 200
envoi 6    -> 429  Retry-After=3600   ✅
```
Messages de test supprimés, compteurs réinitialisés, `backend_test.py` toujours à **100 %**.

### Limite connue

Le compteur est **en mémoire** (adapté au mono-instance / site local). En cas de
plusieurs instances derrière un load balancer, il faudra un compteur Redis.

| 6 | README + livrables + validation bout en bout | B17, B18 |
