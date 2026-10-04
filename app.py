import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "campus_lost_found_secret_key"

# Initialize database schema and default items
init_db()

@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    status_filter = request.args.get("status", "UNCLAIMED").strip()

    conn = get_db_connection()
    
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if status_filter and status_filter != "ALL":
        query += " AND status = ?"
        params.append(status_filter)

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (item_title LIKE ? OR description LIKE ? OR location_found LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY id DESC"

    items = conn.execute(query, params).fetchall()
    
    # Quick statistics counts
    total_unclaimed = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'UNCLAIMED'").fetchone()[0]
    total_claimed = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'CLAIMED'").fetchone()[0]
    
    conn.close()

    return render_template(
        "index.html",
        items=items,
        search_query=search_query,
        active_category=category_filter,
        active_status=status_filter,
        total_unclaimed=total_unclaimed,
        total_claimed=total_claimed
    )

@app.route("/post", methods=["GET", "POST"])
def post_item():
    if request.method == "POST":
        title = request.form.get("item_title", "").strip()
        category = request.form.get("category", "Others").strip()
        location = request.form.get("location_found", "").strip()
        description = request.form.get("description", "").strip()
        question = request.form.get("security_question", "").strip()

        if not title or not location or not description or not question:
            flash("Please fill in all required fields.", "danger")
            return render_template("post_item.html")

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO items (item_title, category, location_found, description, security_question)
               VALUES (?, ?, ?, ?, ?)""",
            (title, category, location, description, question)
        )
        conn.commit()
        conn.close()

        flash(f"'{title}' successfully published to Campus Lost & Found!", "success")
        return redirect(url_for("index"))

    return render_template("post_item.html")

@app.route("/claim/<int:item_id>", methods=["POST"])
def claim_item(item_id):
    answer = request.form.get("security_answer", "").strip()

    if not answer:
        flash("You must provide an answer to claim the item.", "warning")
        return redirect(url_for("index"))

    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if item:
        conn.execute("UPDATE items SET status = 'CLAIMED' WHERE id = ?", (item_id,))
        conn.commit()
        flash(f"Claim request recorded for '{item['item_title']}'. Please present proof at the main office.", "success")
    else:
        flash("Item not found.", "danger")

    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Reads PORT environment variable dynamically (for Render) or defaults to 5000 (local)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


