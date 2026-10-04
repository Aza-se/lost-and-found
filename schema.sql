DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS claims;

CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_title TEXT NOT NULL,
    category TEXT NOT NULL,
    location_found TEXT NOT NULL,
    description TEXT NOT NULL,
    security_question TEXT NOT NULL,
    security_answer TEXT,
    image_filename TEXT,
    found_by_name TEXT,
    is_featured_hero INTEGER DEFAULT 0, -- 1 = Show in Community Honor Roll
    status TEXT DEFAULT 'PENDING_APPROVAL',
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    claimer_name TEXT NOT NULL,
    claimer_contact TEXT NOT NULL,
    provided_answer TEXT NOT NULL,
    claim_status TEXT DEFAULT 'PENDING_REVIEW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items (id)
);
