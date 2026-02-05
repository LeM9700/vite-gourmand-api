# Tests & qualité

## Stratégie
- Tests unitaires (services)
- Tests d’intégration (routes FastAPI)
- Mock des dépendances externes (SMTP)

## Exécuter les tests
```powershell
cd vite-gourmand-api
pytest

# Couverture
pytest --cov=app --cov-report=term-missing
```

## CI
Les workflows GitHub Actions exécutent les tests sur push/PR.
