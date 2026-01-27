-- =========================
-- Vite & Gourmand - Seed data
-- =========================

-- USERS (1 user, 1 employee, 1 admin)
INSERT INTO users (firstname, lastname, email, phone, address, password_hash, role, is_active)
VALUES
('Alice', 'Martin', 'alice.user@vitegourmand.test', '0600000001', '12 rue des Fleurs, 33000 Bordeaux', 'HASH_PLACEHOLDER', 'USER', TRUE),
('Emma', 'Durand', 'emma.employee@vitegourmand.test', '0600000002', '5 quai Richelieu, 33000 Bordeaux', 'HASH_PLACEHOLDER', 'EMPLOYEE', TRUE),
('Jose', 'Admin', 'jose.admin@vitegourmand.test', '0600000003', '1 place de la Bourse, 33000 Bordeaux', 'HASH_PLACEHOLDER', 'ADMIN', TRUE);

-- OPENING HOURS (0=lundi ... 6=dimanche)
INSERT INTO opening_hours (day_of_week, open_time, close_time, is_closed)
VALUES
(0, '09:00', '18:00', FALSE),
(1, '09:00', '18:00', FALSE),
(2, '09:00', '18:00', FALSE),
(3, '09:00', '18:00', FALSE),
(4, '09:00', '18:00', FALSE),
(5, '10:00', '16:00', FALSE),
(6, NULL, NULL, TRUE);

-- DISHES
INSERT INTO dishes (name, dish_type, description)
VALUES
('Velouté de potimarron', 'STARTER', 'Crème de potimarron et éclats de noisette.'),
('Tartare de légumes croquants', 'STARTER', 'Légumes de saison, vinaigrette citronnée.'),

('Magret de canard', 'MAIN', 'Magret rôti, sauce miel-balsamique, légumes.'),
('Curry de pois chiches', 'MAIN', 'Curry végétalien, lait de coco, riz basmati.'),

('Bûche chocolat-noisette', 'DESSERT', 'Bûche gourmande chocolat-noisette.'),
('Panna cotta coco', 'DESSERT', 'Panna cotta coco, coulis mangue.');

-- ALLERGENS
INSERT INTO dish_allergens (dish_id, allergen)
VALUES
(1, 'Lait'),
(1, 'Fruits à coque'),
(3, 'Moutarde'),
(5, 'Lait'),
(5, 'Fruits à coque');

-- MENUS
INSERT INTO menus (title, description, theme, regime, min_people, base_price, conditions_text, stock, is_active)
VALUES
('Menu Noël Tradition', 'Un menu festif et généreux pour les fêtes.', 'Noel', 'classique', 4, 180.00, 'Commander au moins 7 jours avant. Conserver au frais.', 5, TRUE),
('Menu Vegan Élégance', 'Un menu vegan raffiné pour tous les convives.', 'classique', 'vegan', 2, 90.00, 'Commander au moins 48h avant. Stock limité.', 8, TRUE);

-- MENU IMAGES (URLs exemples)
INSERT INTO menu_images (menu_id, url, alt_text, sort_order)
VALUES
(1, 'https://picsum.photos/seed/menu-noel-1/800/600', 'Présentation du Menu Noël Tradition', 0),
(1, 'https://picsum.photos/seed/menu-noel-2/800/600', 'Détails du plat principal du menu Noël', 1),
(2, 'https://picsum.photos/seed/menu-vegan/800/600', 'Présentation du Menu Vegan Élégance', 0);

-- MENU <-> DISH LINKS
-- Menu Noël: starter 1, main 3, dessert 5
INSERT INTO menu_dishes (menu_id, dish_id) VALUES
(1, 1),
(1, 3),
(1, 5);

-- Menu Vegan: starter 2, main 4, dessert 6
INSERT INTO menu_dishes (menu_id, dish_id) VALUES
(2, 2),
(2, 4),
(2, 6);

-- SAMPLE ORDER (PLACED) by Alice for Menu Noël
INSERT INTO orders (
  user_id, menu_id, event_address, event_city, event_date, event_time,
  delivery_km, delivery_fee, people_count, menu_price, discount, total_price,
  status, has_loaned_equipment
)
VALUES
(
  1, 1,
  '20 cours de l’Intendance, 33000 Bordeaux', 'Bordeaux', '2027-01-10', '12:30',
  0, 0,
  4, 180.00, 0, 180.00,
  'PLACED', FALSE
);

-- STATUS HISTORY for that order
INSERT INTO order_status_history (order_id, status, changed_by_user_id, note)
VALUES
(1, 'PLACED', 1, 'Commande passée par le client.');


UPDATE users
SET password_hash = '$2b$12$pA61ALPiehJDVL0VDHRlG.8aYr2Yw.1b7r4iqI42FrK38scGKqCiK'
WHERE email IN (
  'alice.user@vitegourmand.test',
  'emma.employee@vitegourmand.test',
  'jose.admin@vitegourmand.test'
);