# Gestion de projet (ECF)

## Méthode
- Organisation type **Kanban** (Notion) : backlog → à faire → en cours → en revue → terminé.
- Découpage en **features** (auth, menus, commandes, contact, reviews, admin, emails).

## Suivi
- Outil : Notion (lien dans `docs/00-liens.md`).
- Chaque carte contient : description, critères d’acceptation, priorité, estimation, statut.

## Stratégie Git
- Branches : `main` (stable),  `feature/*` (développement).
- Convention commits : messages courts et actionnables.
- Pull Requests : relecture + validation CI.

## Jalons (exemple)
- M1 : Auth + base API + DB
- M2 : Menus + commandes
- M3 : Back-office + emails
- M4 : Tests + déploiement + dossier ECF
