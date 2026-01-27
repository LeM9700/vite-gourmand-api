-- Script SQL pour créer le compte administrateur José
-- ⚠️ IMPORTANT : Ce script doit être exécuté UNE SEULE FOIS lors du setup initial
-- Le mot de passe par défaut est "Jose2024Admin!" (à changer immédiatement après la première connexion)

-- Génération du hash bcrypt pour le mot de passe "Jose2024Admin!"
-- Hash généré avec bcrypt workfactor 12 : $2b$12$5ZOPqLYT8Yp0eMHCFwJkpOE2.vJ3xXdN8Gv6r0HVJy3Kl1MnOpQrW

INSERT INTO users (
    firstname, 
    lastname, 
    email, 
    phone, 
    address, 
    password_hash, 
    role, 
    is_active, 
    created_at, 
    updated_at
)
VALUES (
    'José',
    'Administrateur',
    'jose@vite-et-gourmand.fr',
    '+33 6 12 34 56 78',
    '123 Avenue des Champs-Élysées, 75008 Paris, France',
    '$2b$12$5ZOPqLYT8Yp0eMHCFwJkpOE2.vJ3xXdN8Gv6r0HVJy3Kl1MnOpQrW',  -- Mot de passe: Jose2024Admin!
    'ADMIN',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;  -- Évite les doublons si le script est exécuté plusieurs fois

-- Vérification
SELECT 
    id,
    firstname,
    lastname,
    email,
    role,
    is_active,
    created_at
FROM users
WHERE email = 'jose@vite-et-gourmand.fr';

-- ✅ Après l'exécution de ce script :
-- 1. José peut se connecter avec :
--    - Email : jose@vite-et-gourmand.fr
--    - Mot de passe : Jose2024Admin!
--
-- 2. José DOIT changer son mot de passe immédiatement via l'endpoint PATCH /auth/me
--
-- 3. Ce compte ADMIN a tous les privilèges :
--    - Créer/désactiver des employés
--    - Accéder aux statistiques
--    - Effectuer toutes les opérations de gestion
--
-- 🚨 SÉCURITÉ :
-- - Le mot de passe par défaut est temporaire
-- - Ne JAMAIS commiter ce fichier avec le vrai mot de passe final
-- - Utiliser des mots de passe forts en production (min 12 caractères, majuscules, minuscules, chiffres, symboles)
