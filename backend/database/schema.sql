-- Users/Servers
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Unique Items (normalization)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    image_url TEXT,
    UNIQUE(name)
);

-- Market Listings (The core data)
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER,
    item_id INTEGER,
    seller_name TEXT,
    quantity INTEGER,
    price_won INTEGER DEFAULT 0,
    price_yang INTEGER DEFAULT 0,
    total_price_yang BIGINT, -- Calculated total value for sorting
    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(server_id) REFERENCES servers(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);

-- Item Bonuses/Attributes (e.g., "Ortalama Zarar 45%")
CREATE TABLE IF NOT EXISTS listing_bonuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER,
    bonus_name TEXT NOT NULL,
    bonus_value TEXT,
    FOREIGN KEY(listing_id) REFERENCES listings(id)
);

-- Price History (Market Analysis)
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    avg_unit_price BIGINT,
    min_unit_price BIGINT,
    total_listings INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_listings_item_server ON listings(item_id, server_id);
CREATE INDEX idx_listings_seen_at ON listings(seen_at);
CREATE INDEX idx_price_history_item ON price_history(item_name);
CREATE INDEX idx_price_history_timestamp ON price_history(timestamp);