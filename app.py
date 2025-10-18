from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json, os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

USERS_FILE = "users.json"

# -------------------- Utility Functions --------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_user_by_email(email):
    users = load_users()
    for u in users:
        if u["email"] == email:
            return u
    return None

# -------------------- Routes --------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        users = load_users()

        if get_user_by_email(email):
            flash("Email já registrado! Faça login.", "warning")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)
        new_user = {
            "fullname": fullname,
            "email": email,
            "password": hashed_password,
            "role": role
        }
        users.append(new_user)
        save_users(users)

        flash("Registro concluído com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session.permanent = True
            session["user"] = user["fullname"]
            session["role"] = user["role"]
            flash(f"Bem-vindo(a), {user['fullname']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou senha incorretos!", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Por favor, faça login para continuar.", "warning")
        return redirect(url_for("login"))

    role = session["role"]
    user = session["user"]

    if role == "student":
        return render_template("dashboard_student.html", user=user)
    elif role == "professor":
        return render_template("dashboard_professor.html", user=user)
    elif role == "admin":
        users = load_users()
        return render_template("dashboard_admin.html", user=user, users=users)
    else:
        flash("Função desconhecida. Contate o administrador.", "danger")
        return redirect(url_for("logout"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))

# -------------------- Run Server --------------------
if __name__ == "__main__":
    app.run(debug=True)