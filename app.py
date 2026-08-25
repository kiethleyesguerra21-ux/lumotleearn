from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

app.secret_key = "student-portal-secret-key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE SETUP
# =========================================================

def create_database():

    conn = get_db()

    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL
        )
    """)

    # Add course column if it doesn't exist
    columns = conn.execute("""
        PRAGMA table_info(users)
    """).fetchall()

    column_names = [column["name"] for column in columns]

    if "course" not in column_names:
        conn.execute("""
            ALTER TABLE users
            ADD COLUMN course TEXT DEFAULT 'Information Technology'
        """)

    if "year_level" not in column_names:
        conn.execute("""
            ALTER TABLE users
            ADD COLUMN year_level TEXT DEFAULT '1st Year'
        """)

    # -----------------------------------------------------
    # SUBJECTS TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL,
            subject_name TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # GRADES TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            grade TEXT NOT NULL
        )
    """)

    # -----------------------------------------------------
    # MODULES TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            module_title TEXT NOT NULL,
            description TEXT
        )
    """)

    # -----------------------------------------------------
    # ACTIVITIES TABLE
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            activity_title TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.commit()

    # =====================================================
    # SAMPLE SUBJECTS
    # =====================================================

    sample_subjects = [
        ("IT101", "Programming"),
        ("WD101", "Web Development"),
        ("DB101", "Database Management"),
        ("CC101", "Computer Fundamentals")
    ]

    for code, name in sample_subjects:

        existing = conn.execute("""
            SELECT id
            FROM subjects
            WHERE subject_code = ?
        """, (code,)).fetchone()

        if not existing:

            conn.execute("""
                INSERT INTO subjects
                (subject_code, subject_name)
                VALUES (?, ?)
            """, (code, name))

    conn.commit()

    # =====================================================
    # SAMPLE MODULES AND ACTIVITIES
    # =====================================================

    subjects = conn.execute("""
        SELECT *
        FROM subjects
    """).fetchall()

    for subject in subjects:

        subject_id = subject["id"]
        subject_name = subject["subject_name"]

        # -------------------------------
        # MODULES
        # -------------------------------

        module_count = conn.execute("""
            SELECT COUNT(*) AS total
            FROM modules
            WHERE subject_id = ?
        """, (subject_id,)).fetchone()["total"]

        if module_count == 0:

            conn.execute("""
                INSERT INTO modules
                (subject_id, module_title, description)
                VALUES (?, ?, ?)
            """, (
                subject_id,
                "Module 1: Introduction",
                f"Introduction to {subject_name}."
            ))

            conn.execute("""
                INSERT INTO modules
                (subject_id, module_title, description)
                VALUES (?, ?, ?)
            """, (
                subject_id,
                "Module 2: Basic Concepts",
                f"Basic concepts of {subject_name}."
            ))

        # -------------------------------
        # ACTIVITIES
        # -------------------------------

        activity_count = conn.execute("""
            SELECT COUNT(*) AS total
            FROM activities
            WHERE subject_id = ?
        """, (subject_id,)).fetchone()["total"]

        if activity_count == 0:

            conn.execute("""
                INSERT INTO activities
                (subject_id, activity_title, description)
                VALUES (?, ?, ?)
            """, (
                subject_id,
                "Activity 1",
                f"First activity for {subject_name}."
            ))

            conn.execute("""
                INSERT INTO activities
                (subject_id, activity_title, description)
                VALUES (?, ?, ?)
            """, (
                subject_id,
                "Activity 2",
                f"Second activity for {subject_name}."
            ))

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return redirect(url_for("login"))


# =========================================================
# USER LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user_id = request.form["user_id"].strip()
        username = request.form["username"].strip()

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE user_id = ?
            AND username = ?
        """, (user_id, username)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid User ID or Username."
        )

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    # Get logged-in user
    user = conn.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    # Get subjects
    subjects = conn.execute("""
        SELECT *
        FROM subjects
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        subjects=subjects
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# GRADES
# =========================================================

@app.route("/grades")
def grades():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    grades = conn.execute("""
        SELECT
            grades.grade,
            subjects.subject_code,
            subjects.subject_name
        FROM grades
        JOIN subjects
        ON grades.subject_id = subjects.id
        WHERE grades.user_id = ?
        ORDER BY subjects.subject_code
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "grades.html",
        grades=grades
    )


# =========================================================
# SUBJECT
# =========================================================

@app.route("/subject/<int:subject_id>")
def subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    subject_data = conn.execute("""
        SELECT *
        FROM subjects
        WHERE id = ?
    """, (subject_id,)).fetchone()

    modules = conn.execute("""
        SELECT *
        FROM modules
        WHERE subject_id = ?
        ORDER BY id
    """, (subject_id,)).fetchall()

    activities = conn.execute("""
        SELECT *
        FROM activities
        WHERE subject_id = ?
        ORDER BY id
    """, (subject_id,)).fetchall()

    conn.close()

    if not subject_data:
        return "Subject not found", 404

    return render_template(
        "subject.html",
        subject=subject_data,
        modules=modules,
        activities=activities
    )


# =========================================================
# USER LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # ADMIN ACCOUNT
        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect(url_for("admin"))

        return render_template(
            "admin_login.html",
            error="Invalid admin username or password."
        )

    return render_template("admin_login.html")


# =========================================================
# ADMIN PANEL
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    users = conn.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users
    )


# =========================================================
# ADMIN CREATE USER
# =========================================================

@app.route("/admin/create-user", methods=["POST"])
def create_user():

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    user_id = request.form["user_id"].strip()
    username = request.form["username"].strip()

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO users
            (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return redirect(url_for("admin"))

    conn.close()

    return redirect(url_for("admin"))


# =========================================================
# ADMIN DELETE USER
# =========================================================

@app.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):

    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("admin_login"))


# =========================================================
# CREATE DATABASE
# =========================================================

create_database()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)