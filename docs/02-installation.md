# Installation & exécution (Backend)

## Prérequis
- Python 3.11+
- Accès à une base PostgreSQL (prod) ou utilisation SQLite pour les tests

## Variables d’environnement
Le backend charge sa configuration via `.env` (Pydantic Settings).

- Template : `.env.example`
- Fichier local : `.env` (non versionné)

Variables minimales :
- `POSTGRES_URL`
- `JWT_SECRET`, `JWT_ALG`, `JWT_EXPIRE_MINUTES`
- `MONGO_URL`, `MONGO_DB`
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM`
- `EMAIL_CONFIRMATION_EXPIRE_HOURS`, `EMAIL_CONFIRMATION_SECRET`
- `FRONTEND_URL`

## Lancer en dev
```powershell
cd vite-gourmand-api
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

## Scripts SQL (ECF)
- Schéma : `sql/schema.sql`
- Jeu de données : `sql/seed.sql`
