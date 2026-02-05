# Déploiement (Railway) — Backend

## Cible
- URL : https://vite-gourmand-api-production.up.railway.app

## Principe
- Déploiement automatisé depuis GitHub vers Railway.
- Les variables sensibles sont configurées côté Railway.

## Variables Railway
À configurer sur Railway (équivalents de `.env.example`) :
- `POSTGRES_URL`
- `JWT_SECRET`, `JWT_ALG`, `JWT_EXPIRE_MINUTES`
- `MONGO_URL`, `MONGO_DB`
- `SMTP_*`
- `EMAIL_CONFIRMATION_*`
- `FRONTEND_URL`
- `ENVIRONMENT=production`

## Démarrage
Commande type (selon config Railway) :
- `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## CI GitHub Actions
- Workflows : tests, analyse statique, build.
- Les variables de test non sensibles peuvent être mises en `env:` dans le workflow.
- Les secrets (tokens de déploiement, credentials) doivent rester dans GitHub Secrets / Railway.
