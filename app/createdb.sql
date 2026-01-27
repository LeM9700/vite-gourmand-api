-- =========================
-- Vite & Gourmand - PostgreSQL schema
-- =========================

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('USER','EMPLOYEE','ADMIN');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE dish_type AS ENUM ('STARTER','MAIN','DESSERT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE order_status AS ENUM (
    'PLACED','ACCEPTED','PREPARING','DELIVERING','DELIVERED','WAITING_RETURN','COMPLETED','CANCELLED'
  );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE contact_mode AS ENUM ('EMAIL','PHONE');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE review_status AS ENUM ('PENDING','APPROVED','REJECTED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
  CREATE TYPE message_status AS ENUM ('SENT','FAILED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

CREATE TABLE IF NOT EXISTS users (
  id              BIGSERIAL PRIMARY KEY,
  firstname       VARCHAR(100) NOT NULL,
  lastname        VARCHAR(100) NOT NULL,
  email           VARCHAR(255) NOT NULL UNIQUE,
  phone           VARCHAR(30)  NOT NULL,
  address         TEXT         NOT NULL,
  password_hash   TEXT         NOT NULL,
  role            user_role    NOT NULL DEFAULT 'USER',
  is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  TEXT NOT NULL,
  expires_at  TIMESTAMPTZ NOT NULL,
  used_at     TIMESTAMPTZ NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS menus (
  id              BIGSERIAL PRIMARY KEY,
  title           VARCHAR(150) NOT NULL,
  description     TEXT NOT NULL,
  theme           VARCHAR(50) NOT NULL,
  regime          VARCHAR(50) NOT NULL,
  min_people      INT NOT NULL CHECK (min_people > 0),
  base_price      NUMERIC(10,2) NOT NULL CHECK (base_price >= 0),
  conditions_text TEXT NOT NULL,
  stock           INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS menu_images (
  id          BIGSERIAL PRIMARY KEY,
  menu_id     BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
  url         TEXT NOT NULL,
  alt_text    VARCHAR(255) NOT NULL,
  sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dishes (
  id          BIGSERIAL PRIMARY KEY,
  name        VARCHAR(150) NOT NULL,
  dish_type   dish_type NOT NULL,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dish_allergens (
  id        BIGSERIAL PRIMARY KEY,
  dish_id   BIGINT NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
  allergen  VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS menu_dishes (
  menu_id BIGINT NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
  dish_id BIGINT NOT NULL REFERENCES dishes(id) ON DELETE RESTRICT,
  PRIMARY KEY (menu_id, dish_id)
);

CREATE TABLE IF NOT EXISTS opening_hours (
  id          BIGSERIAL PRIMARY KEY,
  day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
  open_time   TIME NULL,
  close_time  TIME NULL,
  is_closed   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS orders (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  menu_id       BIGINT NOT NULL REFERENCES menus(id) ON DELETE RESTRICT,

  event_address TEXT NOT NULL,
  event_city    VARCHAR(120) NOT NULL,
  event_date    DATE NOT NULL,
  event_time    TIME NOT NULL,

  delivery_km   NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (delivery_km >= 0),
  delivery_fee  NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),

  people_count  INT NOT NULL CHECK (people_count > 0),
  menu_price    NUMERIC(10,2) NOT NULL CHECK (menu_price >= 0),
  discount      NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
  total_price   NUMERIC(10,2) NOT NULL CHECK (total_price >= 0),

  status        order_status NOT NULL DEFAULT 'PLACED',
  has_loaned_equipment BOOLEAN NOT NULL DEFAULT FALSE,

  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_status_history (
  id                 BIGSERIAL PRIMARY KEY,
  order_id           BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  status             order_status NOT NULL,
  changed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  changed_by_user_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  note               TEXT NULL
);

CREATE TABLE IF NOT EXISTS order_cancellations (
  id                  BIGSERIAL PRIMARY KEY,
  order_id            BIGINT NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
  cancelled_by_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  contact_mode        contact_mode NOT NULL,
  reason              TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reviews (
  id           BIGSERIAL PRIMARY KEY,
  order_id     BIGINT NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
  user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  rating       INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment      TEXT NOT NULL,
  status       review_status NOT NULL DEFAULT 'PENDING',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  moderated_by_user_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
  moderated_at TIMESTAMPTZ NULL
);

CREATE TABLE IF NOT EXISTS contact_messages (
  id          BIGSERIAL PRIMARY KEY,
  email       VARCHAR(255) NOT NULL,
  title       VARCHAR(150) NOT NULL,
  description TEXT NOT NULL,
  status      message_status NOT NULL DEFAULT 'SENT',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_menus_theme ON menus(theme);
CREATE INDEX IF NOT EXISTS idx_menus_regime ON menus(regime);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_history_order_id ON order_status_history(order_id);