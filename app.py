from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json, os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

# -------------------- Arquivos --------------------
USERS_FILE = "users.json"
TURMAS_FILE = "turmas.json"
MATERIAIS_FILE = "materiais.json"
UPLOAD_FOLDER = "static/materiais"
AVISOS_FILE = "avisos.json"
CHAT_TURMA_FILE = "chat_turma.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- Funções utilitárias --------------------
def load_json(filename):
    """Lê qualquer arquivo JSON e retorna uma lista ou cria um novo se não existir."""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(filename, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(filename, data):
    """Salva dados em JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def get_user_by_email(email):
    users = load_users()
    for u in users:
        if u["email"] == email:
            return u
    return None

def load_avisos():
    return load_json(AVISOS_FILE)

def save_avisos(avisos):
    save_json(AVISOS_FILE, avisos)
    
def load_chat_turma():
    return load_json(CHAT_TURMA_FILE)

def save_chat_turma(chat):
    save_json(CHAT_TURMA_FILE, chat)

# -------------------- Rotas principais --------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

# --- Registro e Login --- #
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
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash(f"Bem-vindo(a), {user['fullname']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou senha incorretos!", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))

# -------------------- Dashboard --------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Por favor, faça login para continuar.", "warning")
        return redirect(url_for("login"))

    role = session["role"]
    user = session["user"]

    if role == "student":
        materiais = load_json(MATERIAIS_FILE)
        turmas = load_json(TURMAS_FILE)
        minhas_turmas = [t for t in turmas if session["email"] in t["alunos"]]
        materiais_turma = [m for m in materiais if m["turma"] in [t["nome"] for t in minhas_turmas]]
        avisos = [a for a in load_json(AVISOS_FILE) if a["turma"] in [t["nome"] for t in minhas_turmas]]
        return render_template("dashboard_student.html", user=user, materiais=materiais_turma, minhas_turmas=minhas_turmas, avisos=avisos, email=session["email"])

    elif role == "professor":
        users = load_users()
        turmas = load_json(TURMAS_FILE)
        minhas_turmas = [t for t in turmas if t.get("email_professor") == session["email"]]
        return render_template("dashboard_professor.html", user=user, users=users, minhas_turmas=minhas_turmas)

    elif role == "admin":
        users = load_users()
        return render_template("dashboard_admin.html", user=user, users=users)

    else:
        flash("Função desconhecida. Contate o administrador.", "danger")
        return redirect(url_for("logout"))

# -------------------- Funções de Turma --------------------
@app.route("/criar_turma", methods=["GET", "POST"])
def criar_turma():
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito aos professores.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = request.form["nome"]
        professor = session["user"]

        turmas = load_json(TURMAS_FILE)
        if any(t["nome"] == nome for t in turmas):
            flash("Já existe uma turma com esse nome!", "warning")
        else:
            turmas.append({"nome": nome, "professor": professor, "email_professor": session["email"], "alunos": []})
            save_json(TURMAS_FILE, turmas)
            flash(f"Turma '{nome}' criada com sucesso!", "success")

        return redirect(url_for("dashboard"))

    return render_template("criar_turma.html")

@app.route("/turma/<nome>")
def turma(nome):
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    turmas = load_json(TURMAS_FILE)
    turma = next((t for t in turmas if t["nome"] == nome), None)
    if not turma:
        flash("Turma não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    users = load_users()
    alunos = [u for u in users if u["email"] in turma["alunos"]]

    # Materiais da turma
    materiais = load_json(MATERIAIS_FILE)
    materiais_turma = [m for m in materiais if m["turma"] == turma["nome"]]

    # Avisos da turma
    avisos = load_json("avisos.json")
    avisos_turma = [a for a in avisos if a["turma"] == turma["nome"]]
    avisos_turma = sorted(avisos_turma, key=lambda x: x["data"], reverse=True)

    return render_template(
        "turma.html",
        turma=turma,
        alunos=alunos,
        materiais=materiais_turma,
        avisos=avisos_turma
    )

@app.route("/buscar_alunos")
def buscar_alunos():
    """Busca de alunos pelo nome (para professores adicionarem em turmas)."""
    termo = request.args.get("q", "").lower()
    users = load_users()
    filtrados = [u for u in users if u["role"] == "student" and termo in u["fullname"].lower()]
    return jsonify(filtrados)

@app.route("/adicionar_aluno", methods=["POST"])
def adicionar_aluno():
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    turma_nome = request.form["turma"]
    aluno_email = request.form["aluno_email"]

    turmas = load_json(TURMAS_FILE)
    users = load_users()

    aluno = next((u for u in users if u["email"] == aluno_email), None)
    turma = next((t for t in turmas if t["nome"] == turma_nome), None)

    if aluno and turma:
        if aluno_email not in turma["alunos"]:
            turma["alunos"].append(aluno_email)
            save_json(TURMAS_FILE, turmas)
            flash(f"Aluno {aluno['fullname']} adicionado à turma {turma_nome}.", "success")
        else:
            flash("Aluno já está na turma!", "warning")
    else:
        flash("Aluno ou turma não encontrados.", "danger")

    return redirect(url_for("turma", nome=turma_nome))

@app.route("/remover_aluno", methods=["POST"])
def remover_aluno():
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    turma_nome = request.form["turma"]
    aluno_email = request.form["aluno_email"]

    turmas = load_json(TURMAS_FILE)
    turma = next((t for t in turmas if t["nome"] == turma_nome), None)

    if turma and aluno_email in turma["alunos"]:
        turma["alunos"].remove(aluno_email)
        save_json(TURMAS_FILE, turmas)
        flash("Aluno removido com sucesso!", "success")
    else:
        flash("Aluno não encontrado na turma.", "danger")

    return redirect(url_for("turma", nome=turma_nome))

# -------------------- Upload de Materiais --------------------
@app.route("/upload_material", methods=["POST"])
def upload_material():
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    turma = request.form["turma"]
    arquivo = request.files["arquivo"]

    if arquivo:
        caminho = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho)

        materiais = load_json(MATERIAIS_FILE)
        materiais.append({
            "turma": turma,
            "professor": session["user"],
            "arquivo": arquivo.filename
        })
        save_json(MATERIAIS_FILE, materiais)

        flash(f"Material '{arquivo.filename}' enviado para a turma {turma}.", "success")
    else:
        flash("Nenhum arquivo selecionado.", "warning")

    return redirect(url_for("turma", nome=turma))

# -------------------- Rota para adicionar aviso --------------------
@app.route("/adicionar_aviso", methods=["POST"])
def adicionar_aviso():
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    turma_nome = request.form["turma"]
    titulo = request.form["titulo"]
    mensagem = request.form["mensagem"]

    if not titulo.strip() or not mensagem.strip():
        flash("Título e mensagem não podem estar vazios.", "warning")
        return redirect(url_for("turma", nome=turma_nome))

    avisos = load_avisos()
    from datetime import datetime
    novo_aviso = {
        "turma": turma_nome,
        "titulo": titulo.strip(),
        "mensagem": mensagem.strip(),
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    avisos.append(novo_aviso)
    save_avisos(avisos)

    flash("Aviso publicado com sucesso!", "success")
    return redirect(url_for("turma", nome=turma_nome))

# -------------------- Acessar Turma (Aluno) --------------------
@app.route("/acessar_turma/<nome>")
def acessar_turma(nome):
    # Verifica se o usuário está logado e é aluno
    if "user" not in session or session.get("role") != "student":
        flash("Acesso restrito.", "danger")
        return redirect(url_for("dashboard"))

    email_aluno = session["email"]

    # Carrega turmas
    turmas = load_json(TURMAS_FILE)
    turma = next((t for t in turmas if t["nome"] == nome), None)

    if not turma:
        flash("Turma não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    # Verifica se o aluno está matriculado na turma
    if email_aluno not in turma.get("alunos", []):
        flash("Você não está matriculado nesta turma.", "danger")
        return redirect(url_for("dashboard"))

    # Carrega materiais e avisos da turma
    materiais_all = load_json(MATERIAIS_FILE)
    materiais = [m for m in materiais_all if m["turma"] == nome]

    avisos_all = load_json(AVISOS_FILE)
    avisos = [a for a in avisos_all if a["turma"] == nome]

    # Mural (inicialmente vazio)
    mural = []

    return render_template(
        "acessar_turma.html",
        turma=turma,
        materiais=materiais,
        avisos=avisos,
        mural=mural,
        user=session["user"],
        email=session.get("email")
    )
    
# -------------------- Chat da Turma --------------------
@app.route("/chat/<turma_nome>")
def chat_turma(turma_nome):
    chat = load_chat_turma()
    turma_chat = next((c for c in chat if c["turma"] == turma_nome), {"turma": turma_nome, "mensagens": []})
    return jsonify(turma_chat)

@app.route("/chat/enviar", methods=["POST"])
def chat_enviar():
    data = request.json
    turma_nome = data.get("turma")
    usuario = session.get("user")
    texto = data.get("texto")

    if not usuario or not texto.strip():
        return jsonify({"error": "Dados inválidos"}), 400

    chat = load_chat_turma()
    turma_chat = next((c for c in chat if c["turma"] == turma_nome), None)
    from datetime import datetime

    nova_msg = {
        "id": int(datetime.now().timestamp()*1000),  # id único
        "usuario": usuario,
        "texto": texto.strip(),
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "respostas": []
    }

    if turma_chat:
        turma_chat["mensagens"].append(nova_msg)
    else:
        chat.append({"turma": turma_nome, "mensagens": [nova_msg]})

    save_chat_turma(chat)
    return jsonify(nova_msg)

@app.route("/chat/responder", methods=["POST"])
def chat_responder():
    data = request.json
    turma_nome = data.get("turma")
    msg_id = data.get("msg_id")
    usuario = session.get("user")
    texto = data.get("texto")

    if not usuario or not texto.strip():
        return jsonify({"error": "Dados inválidos"}), 400

    chat = load_chat_turma()
    turma_chat = next((c for c in chat if c["turma"] == turma_nome), None)
    if not turma_chat:
        return jsonify({"error": "Turma não encontrada"}), 404

    mensagem = next((m for m in turma_chat["mensagens"] if m["id"] == msg_id), None)
    if not mensagem:
        return jsonify({"error": "Mensagem não encontrada"}), 404

    from datetime import datetime
    resposta = {
        "usuario": usuario,
        "texto": texto.strip(),
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    mensagem["respostas"].append(resposta)
    save_chat_turma(chat)
    return jsonify(resposta)

# -------------------- Rodar servidor --------------------
if __name__ == "__main__":
    app.run(debug=True)
