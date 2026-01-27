import sqlite3
import os

def init_database():
    """Initialise la base de données SQLite avec le schéma et les données de test"""
    
    # Chemin vers la base de données
    db_path = "vite_gourmand.db"
    
    # Supprimer l'ancienne base si elle existe
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Ancienne base de données supprimée")
    
    # Créer la nouvelle base
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📋 Création du schéma SQLite...")
    
    # Schema SQLite adapté
    schema_sql = """
    -- =========================
    -- Vite & Gourmand - SQLite schema
    -- =========================

    CREATE TABLE IF NOT EXISTS users (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      firstname       VARCHAR(100) NOT NULL,
      lastname        VARCHAR(100) NOT NULL,
      email           VARCHAR(255) NOT NULL UNIQUE,
      phone           VARCHAR(30)  NOT NULL,
      address         TEXT         NOT NULL,
      password_hash   TEXT         NOT NULL,
      role            TEXT         NOT NULL DEFAULT 'USER' CHECK (role IN ('USER','EMPLOYEE','ADMIN')),
      is_active       BOOLEAN      NOT NULL DEFAULT 1,
      created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS password_reset_tokens (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token_hash  TEXT NOT NULL,
      expires_at  DATETIME NOT NULL,
      used_at     DATETIME NULL,
      created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menus (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      title           VARCHAR(150) NOT NULL,
      description     TEXT NOT NULL,
      theme           VARCHAR(50) NOT NULL,
      regime          VARCHAR(50) NOT NULL,
      min_people      INTEGER NOT NULL CHECK (min_people > 0),
      base_price      DECIMAL(10,2) NOT NULL CHECK (base_price >= 0),
      conditions_text TEXT NOT NULL,
      stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
      is_active       BOOLEAN NOT NULL DEFAULT 1,
      created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menu_images (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      menu_id     INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
      url         TEXT NOT NULL,
      alt_text    VARCHAR(255) NOT NULL,
      sort_order  INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS dishes (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      name        VARCHAR(150) NOT NULL,
      dish_type   TEXT NOT NULL CHECK (dish_type IN ('STARTER','MAIN','DESSERT')),
      description TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dish_allergens (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      dish_id   INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
      allergen  VARCHAR(80) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS menu_dishes (
      menu_id INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
      dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE RESTRICT,
      PRIMARY KEY (menu_id, dish_id)
    );

    CREATE TABLE IF NOT EXISTS opening_hours (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
      open_time   TIME NULL,
      close_time  TIME NULL,
      is_closed   BOOLEAN NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS orders (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      menu_id       INTEGER NOT NULL REFERENCES menus(id) ON DELETE RESTRICT,
      event_address TEXT NOT NULL,
      event_city    VARCHAR(120) NOT NULL,
      event_date    DATE NOT NULL,
      event_time    TIME NOT NULL,
      delivery_km   DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (delivery_km >= 0),
      delivery_fee  DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),
      people_count  INTEGER NOT NULL CHECK (people_count > 0),
      menu_price    DECIMAL(10,2) NOT NULL CHECK (menu_price >= 0),
      discount      DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
      total_price   DECIMAL(10,2) NOT NULL CHECK (total_price >= 0),
      status        TEXT NOT NULL DEFAULT 'PLACED' CHECK (status IN ('PLACED','ACCEPTED','PREPARING','DELIVERING','DELIVERED','WAITING_RETURN','COMPLETED','CANCELLED')),
      has_loaned_equipment BOOLEAN NOT NULL DEFAULT 0,
      created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS order_status_history (
      id                 INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id           INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
      status             TEXT NOT NULL CHECK (status IN ('PLACED','ACCEPTED','PREPARING','DELIVERING','DELIVERED','WAITING_RETURN','COMPLETED','CANCELLED')),
      changed_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      changed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
      note               TEXT NULL
    );

    CREATE TABLE IF NOT EXISTS order_cancellations (
      id                  INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id            INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
      cancelled_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      contact_mode        TEXT NOT NULL CHECK (contact_mode IN ('EMAIL','PHONE')),
      reason              TEXT NOT NULL,
      created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS reviews (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id     INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
      user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
      rating       INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
      comment      TEXT NOT NULL,
      status       TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED')),
      created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      moderated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
      moderated_at DATETIME NULL
    );

    CREATE TABLE IF NOT EXISTS contact_messages (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      email       VARCHAR(255) NOT NULL,
      title       VARCHAR(150) NOT NULL,
      description TEXT NOT NULL,
      status      TEXT NOT NULL DEFAULT 'SENT' CHECK (status IN ('SENT','FAILED')),
      created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    -- Index pour optimiser les performances
    CREATE INDEX IF NOT EXISTS idx_menus_theme ON menus(theme);
    CREATE INDEX IF NOT EXISTS idx_menus_regime ON menus(regime);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
    CREATE INDEX IF NOT EXISTS idx_order_history_order_id ON order_status_history(order_id);
    """
    
    cursor.executescript(schema_sql)
    print("✅ Schéma créé")
    
    print("📊 Insertion des données de test...")
    
    # Hash de Password123!
    password_hash = '$2b$12$pA61ALPiehJDVL0VDHRlG.8aYr2Yw.1b7r4iqI42FrK38scGKqCiK'
    
    # Users
    cursor.executemany("""
    INSERT INTO users (firstname, lastname, email, phone, address, password_hash, role, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Alice', 'Martin', 'alice.user@vitegourmand.test', '0600000001', 
         '12 rue des Fleurs, 33000 Bordeaux', password_hash, 'USER', 1),
        ('Emma', 'Durand', 'emma.employee@vitegourmand.test', '0600000002', 
         '5 quai Richelieu, 33000 Bordeaux', password_hash, 'EMPLOYEE', 1),
        ('Jose', 'Admin', 'jose.admin@vitegourmand.test', '0600000003', 
         '1 place de la Bourse, 33000 Bordeaux', password_hash, 'ADMIN', 1)
    ])
    
    # Opening hours (0=lundi ... 6=dimanche)
    cursor.executemany("""
    INSERT INTO opening_hours (day_of_week, open_time, close_time, is_closed)
    VALUES (?, ?, ?, ?)
    """, [
        (0, '09:00', '18:00', 0),  # Lundi
        (1, '09:00', '18:00', 0),  # Mardi
        (2, '09:00', '18:00', 0),  # Mercredi
        (3, '09:00', '18:00', 0),  # Jeudi
        (4, '09:00', '18:00', 0),  # Vendredi
        (5, '10:00', '16:00', 0),  # Samedi
        (6, None, None, 1)         # Dimanche fermé
    ])
    
    # Dishes
    cursor.executemany("""
    INSERT INTO dishes (name, dish_type, description)
    VALUES (?, ?, ?)
    """, [
        ('Velouté de potimarron', 'STARTER', 'Crème de potimarron et éclats de noisette.'),
        ('Tartare de légumes croquants', 'STARTER', 'Légumes de saison, vinaigrette citronnée.'),
        ('Magret de canard', 'MAIN', 'Magret rôti, sauce miel-balsamique, légumes.'),
        ('Curry de pois chiches', 'MAIN', 'Curry végétalien, lait de coco, riz basmati.'),
        ('Bûche chocolat-noisette', 'DESSERT', 'Bûche gourmande chocolat-noisette.'),
        ('Panna cotta coco', 'DESSERT', 'Panna cotta coco, coulis mangue.')
    ])
    
    # Allergens
    cursor.executemany("""
    INSERT INTO dish_allergens (dish_id, allergen)
    VALUES (?, ?)
    """, [
        (1, 'Lait'),
        (1, 'Fruits à coque'),
        (3, 'Moutarde'),
        (5, 'Lait'),
        (5, 'Fruits à coque')
    ])
    
    # Menus
    cursor.executemany("""
    INSERT INTO menus (title, description, theme, regime, min_people, base_price, conditions_text, stock, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Menu Noël Tradition', 'Un menu festif et généreux pour les fêtes.', 
         'Noel', 'classique', 4, 180.00, 'Commander au moins 7 jours avant. Conserver au frais.', 5, 1),
        ('Menu Vegan Élégance', 'Un menu vegan raffiné pour tous les convives.', 
         'classique', 'vegan', 2, 90.00, 'Commander au moins 48h avant. Stock limité.', 8, 1)
    ])
    
    # Menu images
    cursor.executemany("""
    INSERT INTO menu_images (menu_id, url, alt_text, sort_order)
    VALUES (?, ?, ?, ?)
    """, [
        (1, 'https://picsum.photos/seed/menu-noel-1/800/600', 'Présentation du Menu Noël Tradition', 0),
        (1, 'https://picsum.photos/seed/menu-noel-2/800/600', 'Détails du plat principal du menu Noël', 1),
        (2, 'https://picsum.photos/seed/menu-vegan/800/600', 'Présentation du Menu Vegan Élégance', 0)
    ])
    
    # Menu dishes (Menu Noël: starter 1, main 3, dessert 5 | Menu Vegan: starter 2, main 4, dessert 6)
    cursor.executemany("""
    INSERT INTO menu_dishes (menu_id, dish_id)
    VALUES (?, ?)
    """, [
        (1, 1), (1, 3), (1, 5),  # Menu Noël
        (2, 2), (2, 4), (2, 6)   # Menu Vegan
    ])
    
    # Sample order
    cursor.execute("""
    INSERT INTO orders (
        user_id, menu_id, event_address, event_city, event_date, event_time,
        delivery_km, delivery_fee, people_count, menu_price, discount, total_price,
        status, has_loaned_equipment
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (1, 1, '20 cours de l\'Intendance, 33000 Bordeaux', 'Bordeaux', '2027-01-10', '12:30',
          0, 0, 4, 180.00, 0, 180.00, 'PLACED', 0))
    
    # Order status history
    cursor.execute("""
    INSERT INTO order_status_history (order_id, status, changed_by_user_id, note)
    VALUES (?, ?, ?, ?)
    """, (1, 'PLACED', 1, 'Commande passée par le client.'))
    
    conn.commit()
    conn.close()
    
    print("✅ Base de données SQLite initialisée avec succès!")
    print("📍 Fichier créé: vite_gourmand.db")
    print("🔑 Comptes de test (mot de passe: Password123!):")
    print("   - alice.user@vitegourmand.test (USER)")
    print("   - emma.employee@vitegourmand.test (EMPLOYEE)")  
    print("   - jose.admin@vitegourmand.test (ADMIN)")

if __name__ == "__main__":
    init_database()