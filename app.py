import hmac
import os
import sqlite3

from flask import Flask, Response, redirect, render_template, request, url_for


def create_app(database="signups.db"):
    app = Flask(__name__)
    app.config["DATABASE"] = database
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD")

    def get_db():
        return sqlite3.connect(app.config["DATABASE"])

    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS signups ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "email TEXT NOT NULL, "
            "major TEXT NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )

    @app.route("/", methods=["GET", "POST"])
    def signup():
        if request.method == "GET":
            return render_template("signup.html", error=None, form={})

        form = {k: request.form.get(k, "").strip() for k in ("name", "email", "major")}
        if not all(form.values()):
            error = "Please fill in all fields."
        elif "@" not in form["email"]:
            error = "Please enter a valid email address."
        else:
            error = None

        if error:
            return render_template("signup.html", error=error, form=form), 400

        with get_db() as conn:
            conn.execute(
                "INSERT INTO signups (name, email, major) VALUES (?, ?, ?)",
                (form["name"], form["email"], form["major"]),
            )
        return redirect(url_for("thanks"))

    @app.route("/thanks")
    def thanks():
        return render_template("thanks.html")

    @app.route("/admin")
    def admin():
        expected = app.config["ADMIN_PASSWORD"]
        auth = request.authorization
        given = auth.password if auth and auth.password else ""
        # Locked entirely when no password is configured.
        if not expected or not hmac.compare_digest(given.encode(), expected.encode()):
            return Response(
                "Password required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Trip sign-up admin"'},
            )

        with get_db() as conn:
            signups = conn.execute(
                "SELECT name, email, major, created_at FROM signups ORDER BY id"
            ).fetchall()
        return render_template("admin.html", signups=signups)

    return app
