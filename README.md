# Vite & Gourmand — API (FastAPI)

API backend du projet **Vite & Gourmand** (traiteur haut de gamme).

- Dépôt : https://github.com/LeM9700/vite-gourmand-api
- API déployée (Railway) : https://vite-gourmand-api-production.up.railway.app
- Front déployé (Netlify) : https://www.vitegourmand.netlify.app

## Fonctionnalités (extrait)
- Authentification JWT (utilisateurs / employés / admin)
- Menus + plats + allergènes + stocks
- Commandes (statuts, calcul prix, livraison)
- Contact + modération
- Avis clients
- Emails (confirmation, relance retour matériel)

## Prérequis
- Python 3.11+ recommandé
- PostgreSQL (prod) / SQLite (tests)

## Installation locale (développement)
```powershell
cd vite-gourmand-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) Copier les variables d'environnement
Copy-Item .env.example .env

# 2) Renseigner les valeurs (.env)

# 3) Lancer l'API
uvicorn app.main:app --reload
```

API : `http://127.0.0.1:8000`

## Base de données (SQL ECF)
Les scripts SQL demandés pour le dossier ECF sont dans :
- `sql/schema.sql`
- `sql/seed.sql`

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
