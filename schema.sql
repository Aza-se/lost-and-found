CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_title TEXT NOT NULL,
    category TEXT NOT NULL,
    location_found TEXT NOT NULL,
    description TEXT NOT NULL,
    security_question TEXT NOT NULL,
    status TEXT DEFAULT 'UNCLAIMED',
    date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
