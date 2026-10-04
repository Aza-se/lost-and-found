import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "campus_lost_found_secure_key"

# Image upload configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- CLIENT ROUTES ---

@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()

    conn = get_db_connection()
    query = "SELECT * FROM items WHERE status = 'UNCLAIMED'"
    params = []

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (item_title LIKE ? OR description LIKE ? OR location_found LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY id DESC"

    unclaimed_items = conn.execute(query, params).fetchall()
    claimed_items = conn.execute("SELECT * FROM items WHERE status = 'CLAIMED' ORDER BY id DESC").fetchall()
    
    # Fetch recognized honesty heroes
    honesty_heroes = conn.execute("SELECT * FROM items WHERE is_featured_hero = 1 ORDER BY id DESC").fetchall()

    total_unclaimed = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'UNCLAIMED'").fetchone()[0]
    total_claimed = conn.execute("SELECT COUNT(*) FROM items WHERE status = 'CLAIMED'").fetchone()[0]
    
    conn.close()

    return render_template(
        "index.html",
        items=unclaimed_items,
        claimed_items=claimed_items,
        honesty_heroes=honesty_heroes,
        search_query=search_query,
        active_category=category_filter,
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
        answer = request.form.get("security_answer", "").strip()
        finder_name = request.form.get("found_by_name", "Anonymous Good Samaritan").strip()

        if not title or not location or not description or not question:
            flash("Please fill in all required fields.", "danger")
            return render_template("post_item.html")

        # Handle Image Upload
        filename = None
        if 'item_image' in request.files:
            file = request.files['item_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO items (item_title, category, location_found, description, security_question, security_answer, image_filename, found_by_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_APPROVAL')""",
            (title, category, location, description, question, answer, filename, finder_name)
        )
        conn.commit()
        conn.close()

        flash("🌟 Thank you for your honesty! Your report was submitted and will appear on the board once approved.", "success")
        return redirect(url_for("index"))

    return render_template("post_item.html")

@app.route("/claim_request/<int:item_id>", methods=["POST"])
def submit_claim(item_id):
    claimer_name = request.form.get("claimer_name", "").strip()
    claimer_contact = request.form.get("claimer_contact", "").strip()
    provided_answer = request.form.get("provided_answer", "").strip()

    if not claimer_name or not claimer_contact or not provided_answer:
        flash("Please complete all details to request a claim.", "warning")
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        """INSERT INTO claims (item_id, claimer_name, claimer_contact, provided_answer, claim_status)
           VALUES (?, ?, ?, ?, 'PENDING_REVIEW')""",
        (item_id, claimer_name, claimer_contact, provided_answer)
    )
    conn.commit()
    conn.close()

    flash("Claim request submitted! Campus Security will review your request.", "success")
    return redirect(url_for("index"))


# --- ADMIN ROUTES ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            flash("Welcome back, Administrator.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    pending_items = conn.execute("SELECT * FROM items WHERE status = 'PENDING_APPROVAL' ORDER BY id DESC").fetchall()
    
    pending_claims = conn.execute("""
        SELECT claims.*, items.item_title, items.security_question, items.security_answer 
        FROM claims 
        JOIN items ON claims.item_id = items.id 
        WHERE claims.claim_status = 'PENDING_REVIEW'
        ORDER BY claims.id DESC
    """).fetchall()

    claimed_history = conn.execute("""
        SELECT items.*, claims.claimer_name, claims.claimer_contact
        FROM items
        LEFT JOIN claims ON claims.item_id = items.id AND claims.claim_status = 'APPROVED'
        WHERE items.status = 'CLAIMED'
        ORDER BY items.id DESC
    """).fetchall()

    all_items = conn.execute("SELECT * FROM items ORDER BY id DESC").fetchall()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        pending_items=pending_items,
        pending_claims=pending_claims,
        claimed_history=claimed_history,
        all_items=all_items
    )

@app.route("/admin/toggle_hero/<int:item_id>", methods=["POST"])
def toggle_hero(item_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    item = conn.execute("SELECT is_featured_hero FROM items WHERE id = ?", (item_id,)).fetchone()
    if item:
        new_status = 0 if item['is_featured_hero'] == 1 else 1
        conn.execute("UPDATE items SET is_featured_hero = ? WHERE id = ?", (new_status, item_id))
        conn.commit()
        flash("Honesty recognition status updated!", "success")

    conn.close()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/approve_item/<int:item_id>", methods=["POST"])
def approve_item(item_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("UPDATE items SET status = 'UNCLAIMED' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    flash("Item approved and published live!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/approve_claim/<int:claim_id>", methods=["POST"])
def approve_claim(claim_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    notes = request.form.get("admin_notes", "Verified identity & handed over by Admin.").strip()

    conn = get_db_connection()
    claim = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()

    if claim:
        conn.execute("UPDATE claims SET claim_status = 'APPROVED' WHERE id = ?", (claim_id,))
        conn.execute("UPDATE items SET status = 'CLAIMED', admin_notes = ? WHERE id = ?", (notes, claim['item_id']))
        conn.commit()
        flash("Claim approved! Item marked as Taken by Owner.", "success")

    conn.close()
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
