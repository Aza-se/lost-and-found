import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('schema.sql') as f:
        conn.executescript(f.read())
    
    # Check if seed data exists
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO items (item_title, category, location_found, description, security_question, security_answer, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Scientific Calculator (Casio)",
            "Electronics",
            "Math Lab 3",
            "Black Casio FX calculator found on desk row 2.",
            "What name or initial is written inside the slide cover?",
            "alex",
            "UNCLAIMED"
        ))
        
        cursor.execute("""
            INSERT INTO items (item_title, category, location_found, description, security_question, security_answer, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Blue Backpack with Keychain",
            "Others",
            "Student Union Cafeteria",
            "Dark blue JanSport backpack containing notebooks.",
            "What color is the mascot keychain attached to the front zipper?",
            "red",
            "PENDING_APPROVAL"
        ))
        
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()