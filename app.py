from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import json, os
import random
from utils import calcular_media_c

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

pesos = {"NP1": 0.4, "NP2": 0.6}

# -------------------- Arquivos --------------------
USERS_FILE = "data/users.json"
TURMAS_FILE = "data/turmas.json"
MATERIAIS_FILE = "data/materiais.json"
AVISOS_FILE = "data/avisos.json"
CHAT_TURMA_FILE = "data/chat_turma.json"
DIARIO_FILE = "data/diario_turma.json"
CURSOS_FILE = "data/cursos.json"
UPLOAD_FOLDER = "static/materiais"
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
    
def load_cursos():
    return load_json(CURSOS_FILE)

def save_cursos(cursos):
    save_json(CURSOS_FILE, cursos)
    
def load_diario():
    return load_json(DIARIO_FILE)

def save_diario(diario):
    save_json(DIARIO_FILE, diario)

def gerar_matricula(curso_nome, periodo):
    """Gera uma matrícula lógica do tipo CU0XXX"""
    prefixo = curso_nome[:2].upper()  # pega as 2 primeiras letras do curso
    numero_random = random.randint(100, 999)
    return f"{prefixo}{int(periodo)}{numero_random}"

# -------------------- Função para analisar o nome da turma --------------------
def parse_turma_nome(turma_nome):
    partes = turma_nome.split('-')
    if len(partes) >= 3:
        curso = '-'.join(partes[:-2])
        materia = partes[-2]
        periodo_str = partes[-1]
        if periodo_str.startswith('P') and periodo_str[1:].isdigit():
            periodo = int(periodo_str[1:])
            return curso, materia, periodo
    return None, None, None


# -------------------- Rotas principais --------------------
@app.route("/")
def home():
    return redirect(url_for("login"))

# --- Registro e Login --- #
@app.route("/register", methods=["GET", "POST"])
def register():
    cursos = load_cursos()  # carrega todos os cursos disponíveis

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

        # Se for estudante, adiciona curso e estrutura de notas
        if role == "student":
            curso_nome = request.form.get("curso")
            curso = next((c for c in cursos if c["nome"] == curso_nome), None)

            if not curso:
                flash("Curso inválido.", "danger")
                return redirect(url_for("register"))

            periodo_inicial = "1"
            materias_periodo = curso["materias"].get(periodo_inicial, [])
            matricula = gerar_matricula(curso_nome, periodo_inicial)

            # Cria estrutura de notas por matéria
            notas = {
                (m["nome"] if isinstance(m, dict) else m): {"NP1": None, "NP2": None}
                for m in materias_periodo
            }

            new_user["curso"] = curso_nome
            new_user["periodo_atual"] = int(periodo_inicial)
            new_user["matricula"] = matricula
            new_user["notas"] = notas

        users.append(new_user)
        save_users(users)

        flash("Registro concluído com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    # renderiza template com cursos disponíveis
    return render_template("register.html", cursos=cursos)


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
    email = session["email"]

    if role == "student":
        # Carrega informações
        users = load_users()
        current_user = next((u for u in users if u["email"] == email), None)

        if not current_user:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("logout"))

        materiais = load_json(MATERIAIS_FILE)
        turmas = load_json(TURMAS_FILE)
        minhas_turmas = [t for t in turmas if email in t["alunos"]]
        materiais_turma = [m for m in materiais if m["turma"] in [t["nome"] for t in minhas_turmas]]
        avisos = [a for a in load_json(AVISOS_FILE) if a["turma"] in [t["nome"] for t in minhas_turmas]]

        # Pega informações do curso, período e matrícula
        curso = current_user.get("curso")
        periodo = current_user.get("periodo_atual")
        matricula = current_user.get("matricula")
        notas = current_user.get("notas", {})
        
        return render_template(
            "dashboard_student.html",
            user=user,
            materiais=materiais_turma,
            minhas_turmas=minhas_turmas,
            avisos=avisos,
            email=email,
            curso=curso,
            periodo=periodo,
            matricula=matricula,
            notas=notas
        )
        
    elif role == "professor":
        users = load_users()
        turmas = load_json(TURMAS_FILE)
        minhas_turmas = [t for t in turmas if t.get("email_professor") == session["email"]]
        return render_template("dashboard_professor.html", user=user, users=users, minhas_turmas=minhas_turmas)

    elif role == "admin":
        users = load_users()
        return render_template("dashboard_admin.html", cursos=load_cursos(), users=users, professores=[u for u in users if u["role"] == "professor"])

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

    # Diário da turma
    diario = load_diario()
    registro_turma = next((d for d in diario if d["turma"] == nome), {"turma": nome, "registros": []})

    # Calcular aulas disponíveis (baseado na matéria da turma)
    def parse_turma_nome(turma_nome):
        partes = turma_nome.split('-')
        if len(partes) >= 3:
            curso = '-'.join(partes[:-2])
            materia = partes[-2]
            periodo_str = partes[-1]
            if periodo_str.startswith('P') and periodo_str[1:].isdigit():
                periodo = int(periodo_str[1:])
                return curso, materia, periodo
        return None, None, None

    curso_nome, materia_nome, periodo = parse_turma_nome(nome)
    aulas = []
    if curso_nome and materia_nome and periodo is not None:
        cursos = load_cursos()
        curso = next((c for c in cursos if c["nome"] == curso_nome), None)
        if curso:
            materia = next((m for m in curso["materias"].get(str(periodo), []) if m["nome"] == materia_nome), None)
            if materia:
                aulas_totais = materia["aulas"]
                aulas = [f"Aula {i}" for i in range(1, aulas_totais + 1)]

    # Notas dos alunos
    notas = {}
    for aluno in alunos:
        todas_notas = aluno.get("notas", {})
        notas_disciplina = todas_notas.get(materia_nome, {})
        notas[aluno["email"]] = notas_disciplina

    pesos = turma.get("pesos", {"NP1": 0.4, "NP2": 0.6})

    return render_template(
        "turma.html",
        turma=turma,
        alunos=alunos,
        materiais=materiais_turma,
        avisos=avisos_turma,
        registros=registro_turma["registros"],
        aulas=aulas,
        pesos=pesos,
        notas=notas,
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

# -------------------- Diário da Turma --------------------
@app.route("/turma/<nome>/diario", methods=["GET", "POST"])
def diario_turma(nome):
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito aos professores.", "danger")
        return redirect(url_for("dashboard"))

    turmas = load_json(TURMAS_FILE)
    turma = next((t for t in turmas if t["nome"] == nome), None)
    if not turma:
        flash("Turma não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    # Função para parsear o nome da turma e extrair curso, matéria e período
    def parse_turma_nome(turma_nome):
        partes = turma_nome.split('-')
        if len(partes) >= 3:
            curso = '-'.join(partes[:-2])  # Junta tudo exceto as últimas duas partes
            materia = partes[-2]  # Penúltima parte é a matéria
            periodo_str = partes[-1]  # Última parte é "P1", "P2", etc.
            if periodo_str.startswith('P') and periodo_str[1:].isdigit():
                periodo = int(periodo_str[1:])
                return curso, materia, periodo
        return None, None, None

    curso_nome, materia_nome, periodo = parse_turma_nome(nome)
    if not curso_nome or not materia_nome or periodo is None:
        flash("Nome da turma inválido. Não foi possível identificar a matéria.", "danger")
        return redirect(url_for("dashboard"))

    cursos = load_cursos()
    curso = next((c for c in cursos if c["nome"] == curso_nome), None)
    if not curso:
        flash("Curso associado à turma não encontrado.", "danger")
        return redirect(url_for("dashboard"))

    materia = next((m for m in curso["materias"].get(str(periodo), []) if m["nome"] == materia_nome), None)
    if not materia:
        flash("Matéria da turma não encontrada no curso.", "danger")
        return redirect(url_for("dashboard"))

    aulas_totais = materia["aulas"]
    aulas = [f"Aula {i}" for i in range(1, aulas_totais + 1)]  # Lista de aulas disponíveis

    diario = load_diario()
    registro_turma = next((d for d in diario if d["turma"] == nome), {"turma": nome, "registros": []})

    if request.method == "POST":
        aula = request.form["aula"]
        conteudo = request.form["conteudo"].strip()
        if aula and conteudo:
            from datetime import datetime
            novo_registro = {
                "id": int(datetime.now().timestamp()*1000),
                "aula": aula,
                "conteudo": conteudo,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            registro_turma["registros"].append(novo_registro)
            # Atualiza ou adiciona ao diário
            diario = [d for d in diario if d["turma"] != nome] + [registro_turma]
            save_diario(diario)
            flash("Registro do diário salvo com sucesso!", "success")
            return redirect(url_for("diario_turma", nome=nome))
        else:
            flash("Selecione a aula e preencha o conteúdo do registro.", "warning")


    return render_template("turma.html", turma=turma, registros=registro_turma["registros"], aulas=aulas)

@app.route("/turma/<nome>/diario/editar/<int:registro_id>", methods=["POST"])
def editar_diario(nome, registro_id):
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito aos professores.", "danger")
        return redirect(url_for("dashboard"))
    diario = load_diario()
    registro_turma = next((d for d in diario if d["turma"] == nome), None)
    if not registro_turma:
        flash("Turma não encontrada no diário.", "danger")
        return redirect(url_for("diario_turma", nome=nome))
    registro = next((r for r in registro_turma["registros"] if r["id"] == registro_id), None)
    if not registro:
        flash("Registro não encontrado.", "danger")
        return redirect(url_for("diario_turma", nome=nome))
    # Atualiza os campos editáveis (aula e conteúdo)
    aula = request.form.get("aula")
    conteudo = request.form.get("conteudo", "").strip()
    if aula and conteudo:
        registro["aula"] = aula
        registro["conteudo"] = conteudo
        # Opcional: atualizar a data para refletir a edição
        from datetime import datetime
        registro["data"] = datetime.now().strftime("%d/%m/%Y %H:%M") + " (editado)"
        save_diario(diario)
        flash("Registro editado com sucesso!", "success")
    else:
        flash("Selecione a aula e preencha o conteúdo.", "warning")
    return redirect(url_for("diario_turma", nome=nome))

# -------------------- Lançamento de Notas --------------------
@app.route("/turma/<nome>/notas", methods=["GET", "POST"])
def notas_turma(nome):
    if "user" not in session or session["role"] != "professor":
        flash("Acesso restrito aos professores.", "danger")
        return redirect(url_for("dashboard"))

    turmas = load_json(TURMAS_FILE)
    turma = next((t for t in turmas if t["nome"] == nome), None)
    if not turma:
        flash("Turma não encontrada.", "danger")
        return redirect(url_for("dashboard"))

    users = load_users()
    alunos = [u for u in users if u["email"] in turma["alunos"]]

    # Notas da disciplina da turma
    curso_nome, materia_nome, periodo = parse_turma_nome(nome)
    notas = {}
    for aluno in alunos:
        todas_notas = aluno.get("notas", {})
        notas_disciplina = todas_notas.get(materia_nome, {})
        notas[aluno["email"]] = notas_disciplina

    pesos = turma.get("pesos", {"NP1": 0.4, "NP2": 0.6})

    if request.method == "POST":
        for aluno in alunos:
            np1 = request.form.get(f"nota_{aluno['email']}_NP1")
            np2 = request.form.get(f"nota_{aluno['email']}_NP2")
            try:
                np1_val = float(np1) if np1 else 0
                np2_val = float(np2) if np2 else 0
            except ValueError:
                np1_val = np2_val = 0

            if "notas" not in aluno:
                aluno["notas"] = {}
            if materia_nome not in aluno["notas"]:
                aluno["notas"][materia_nome] = {}
            aluno["notas"][materia_nome]["NP1"] = np1_val
            aluno["notas"][materia_nome]["NP2"] = np2_val
            aluno["notas"][materia_nome]["media"] = calcular_media_c(
                np1_val, np2_val, pesos["NP1"], pesos["NP2"]
            )

        save_users(users)
        flash("Notas atualizadas com sucesso!", "success")
        return redirect(url_for("notas_turma", nome=nome))

    return render_template(
        "turma.html",
        turma=turma,
        alunos=alunos,
        pesos=pesos,
        notas=notas,
        tab_active="notasTab"
    )

# -------------------- Cursos --------------------

@app.route("/cursos")
def listar_cursos():
    if "role" not in session or session["role"] != "admin":
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))

    cursos = load_cursos()
    return render_template("dashboard_admin.html", cursos=cursos)


@app.route("/criar_curso", methods=["GET", "POST"])
def criar_curso():
    if "role" not in session or session["role"] != "admin":
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nome = request.form["nome"]
        periodos = int(request.form["periodos"])

        cursos = load_cursos()
        if any(c["nome"].lower() == nome.lower() for c in cursos):
            flash("Já existe um curso com esse nome!", "warning")
            return redirect(url_for("listar_cursos"))

        novo_curso = {
            "nome": nome,
            "periodos": periodos,
            "materias": {str(i): [] for i in range(1, periodos + 1)}
        }
        cursos.append(novo_curso)
        save_cursos(cursos)

        flash("Curso criado com sucesso!", "success")
        return redirect(url_for("listar_cursos"))

    return render_template("criar_curso.html", curso=None)


@app.route("/cursos/<nome>/editar", methods=["GET", "POST"])
def editar_curso(nome):
    if "role" not in session or session["role"] != "admin":
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))

    cursos = load_cursos()
    curso = next((c for c in cursos if c["nome"] == nome), None)
    users = load_users()
    professores = [u for u in users if u["role"] == "professor"]
    
    if not curso:
        flash("Curso não encontrado.", "danger")
        return redirect(url_for("listar_cursos"))

    if request.method == "POST":
        users = load_users()
        turmas = load_json(TURMAS_FILE)
        for i in range(1, curso["periodos"] + 1):
            materias = request.form.getlist(f"materias_{i}[]")
            aulas = request.form.getlist(f"aulas_{i}[]")
            professores_email = request.form.getlist(f"professores_{i}[]")

            curso["materias"][str(i)] = []
            for m, a, p_email in zip(materias, aulas, professores_email):
                if m.strip():
                    curso["materias"][str(i)].append({
                        "nome": m.strip(),
                        "aulas": int(a) if a.strip() else 0,
                        "professor": p_email
                    })

                    # Criar turma automaticamente
                    if p_email:
                        turma_nome = f"{curso['nome']}-{m.strip()}-P{i}"
                        if not any(t["nome"] == turma_nome for t in turmas):
                            # Pega estudantes do curso e período
                            alunos = [u["email"] for u in users
                                    if u.get("curso") == curso["nome"]
                                    and u.get("periodo_atual") == i]
                            turmas.append({
                                "nome": turma_nome,
                                "professor": next((u["fullname"] for u in users if u["email"] == p_email), ""),
                                "email_professor": p_email,
                                "alunos": alunos
                            })

        save_cursos(cursos)
        save_json(TURMAS_FILE, turmas)
        flash("Curso e turmas atualizados com sucesso!", "success")
        return redirect(url_for("listar_cursos"))

    return render_template("editar_curso.html", curso=curso, professores=professores)


@app.route("/cursos/<nome>/deletar", methods=["POST"])
def deletar_curso(nome):
    if "role" not in session or session["role"] != "admin":
        flash("Acesso restrito ao administrador.", "danger")
        return redirect(url_for("dashboard"))

    cursos = load_cursos()
    cursos = [c for c in cursos if c["nome"] != nome]
    save_cursos(cursos)

    flash("Curso removido com sucesso!", "success")
    return redirect(url_for("listar_cursos"))

# -------------------- Rodar servidor --------------------
if __name__ == "__main__":
    app.run(debug=True)
