import sqlite3

DB_NAME = "lost_found.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open("schema.sql", "r") as f:
        conn.executescript(f.read())

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """INSERT INTO items (item_title, category, location_found, description, security_question)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "Scientific Calculator (Casio)",
                "Electronics",
                "Math Lab 3",
                "Black Casio FX calculator found on desk row 2.",
                "What name or initial is written inside the slide cover?"
            )
        )
    conn.commit()
    conn.close()
