# Sécurité & RGPD (synthèse)

## Sécurité applicative
- **Authentification** : JWT (durée limitée) + rôles (USER/EMPLOYEE/ADMIN).
- **Mots de passe** : hash (bcrypt) — jamais stockés en clair.
- **Secrets** : stockés en variables d’environnement (`.env` en local, secrets Railway/GitHub Actions en CI/CD).
- **Validation** : validation des payloads via schémas Pydantic + règles métier.
- **CORS** : restreint en production aux domaines Netlify.
- **Journalisation** : logs applicatifs (utile pour audit / diagnostic).

## Risques & mitigations (exemples)
- Injection SQL : ORM SQLAlchemy + paramètres (éviter concat string).
- Brute force / credential stuffing : limitation à prévoir (rate limiting) + monitoring.
- Compromission secrets : rotation + ne jamais committer `.env`.

## RGPD (principes)
- Minimisation : collecter uniquement les données nécessaires (contact, adresse, email, etc.).
- Durées de conservation : à définir (ex. suppression/anonymisation après X mois).
- Droits : accès/suppression/modification sur demande.
- Sécurité : chiffrement TLS en transit (HTTPS), accès DB restreint.
