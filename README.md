# Vite & Gourmand — API (FastAPI)

API backend du projet **Vite & Gourmand** (traiteur haut de gamme).

- Dépôt : https://github.com/LeM9700/vite-gourmand-api
- API déployée (Railway) : https://vite-gourmand-api-production.up.railway.app
- Front déployé (Netlify) : https://vitegourmand.netlify.app

## Fonctionnalités (extrait)
- Authentification JWT (utilisateurs / employés / admin)
- Menus + plats + allergènes + stocks
- Commandes (statuts, calcul prix, livraison)
- Contact + modération
- Avis clients
- Emails (confirmation, relance retour matériel)
- Stats admin (PostgreSQL + agrégats MongoDB)

## Prérequis
- Python **3.12+** (recommandé)
- PostgreSQL (dev/prod)
- (Optionnel) MongoDB Atlas pour les endpoints de stats
- PowerShell (Windows) recommandé pour les commandes ci-dessous

## Installation locale (développement)
```powershell
cd vite-gourmand-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) Copier les variables d'environnement
Copy-Item .env.example .env

# 2) Renseigner les valeurs dans .env (ne pas committer)
# - DATABASE_URL
# - JWT_SECRET_KEY
# - MONGODB_URI (si stats)
# - CORS_ORIGINS
# etc.

# 3) Lancer l'API
uvicorn app.main:app --reload
```

API locale : `http://127.0.0.1:8000`  
Swagger : `http://127.0.0.1:8000/docs`

## Base de données (SQL ECF)
Scripts SQL présents dans le repo (utilisés pour le dossier ECF et/ou initialisation) :
- `app/createdb.sql`
- `app/createdata.sql`
- (seed éventuel) voir le dossier `sql/` si applicable dans ton setup

> Remarque : adapter les commandes psql selon ton `DATABASE_URL` et ton environnement.

## Tests
```powershell
pytest

# Couverture
pytest --cov=app --cov-report=term-missing
```

## Documentation (ECF)
Voir le dossier `docs/`.
- `docs/00-liens.md` (liens projet)
- `docs/01-presentation.md` (contexte + périmètre)
- `docs/02-installation.md` (installation + variables)
- `docs/03-securite-rgpd.md`
- `docs/04-deploiement.md`
- `docs/05-diagrammes.md`
- `docs/06-gestion-projet.md`
- `docs/07-tests-qualite.md`
