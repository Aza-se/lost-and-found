from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "school_lost_found_secret_key"

init_db()

@app.route("/")
def index():
    category_filter = request.args.get("category", "")
    conn = get_db_connection()

    query = "SELECT * FROM items WHERE status = 'UNCLAIMED'"
    params = []

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY id DESC"

    items = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("index.html", items=items, active_category=category_filter)

@app.route("/post", methods=["GET", "POST"])
def post_item():
    if request.method == "POST":
        title = request.form["item_title"]
        category = request.form["category"]
        location = request.form["location_found"]
        description = request.form["description"]
        question = request.form["security_question"]

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO items (item_title, category, location_found, description, security_question)
               VALUES (?, ?, ?, ?, ?)""",
            (title, category, location, description, question)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("post_item.html")

@app.route("/claim/<int:item_id>", methods=["POST"])
def claim_item(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item:
        conn.execute("UPDATE items SET status = 'CLAIMED' WHERE id = ?", (item_id,))
        conn.commit()
        flash(f"Claim request submitted for '{item['item_title']}'. Present proof at the main office.", "success")
    conn.close()
    return redirect(url_for("index"))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
