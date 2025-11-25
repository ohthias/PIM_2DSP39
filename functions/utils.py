"""
Módulo utilitário para leitura, escrita e manipulação de dados em arquivos JSON
utilizados no sistema acadêmico.

Funções principais:
- Leitura e gravação de dados persistentes (usuários, avisos, chats, cursos e diários)
- Geração de matrículas únicas para alunos
- Interpretação e extração de informações de nomes de turmas

Autor: [Seu nome]
Data: [Data de criação ou modificação]
"""

import json
import os
import random

# -----------------------------
# Caminhos globais dos arquivos
# -----------------------------
USERS_FILE = "data/users.json"
AVISOS_FILE = "data/avisos.json"
CHAT_TURMA_FILE = "data/chat_turma.json"
CURSOS_FILE = "data/cursos.json"
DIARIO_FILE = "data/diario_turma.json"
UPLOAD_FOLDER = "static/materiais"
MATERIAIS_FILE = "data/materiais.json"

# ===============================
# Funções genéricas de leitura e gravação
# ===============================
def load_json(filename):
    """
    Lê qualquer arquivo JSON e retorna seu conteúdo como lista ou dicionário.
    Caso o arquivo não exista ou esteja vazio/corrompido, cria um novo arquivo
    com uma lista vazia e retorna [].

    Parâmetros:
        filename (str): Caminho completo do arquivo JSON.

    Retorna:
        list | dict: Conteúdo do arquivo JSON ou lista vazia se o arquivo não for válido.
    """
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(filename, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_json(filename, data):
    """
    Salva dados (lista ou dicionário) em formato JSON no arquivo especificado.

    Parâmetros:
        filename (str): Caminho do arquivo a ser salvo.
        data (list | dict): Dados a serem escritos no arquivo.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ===============================
# Funções específicas de manipulação de dados
# ===============================
def load_users():
    """Carrega a lista de usuários a partir do arquivo JSON correspondente."""
    return load_json(USERS_FILE)


def save_users(users):
    """Salva a lista de usuários no arquivo JSON correspondente."""
    save_json(USERS_FILE, users)


def get_user_by_email(email):
    """
    Busca um usuário específico pelo e-mail.

    Parâmetros:
        email (str): Endereço de e-mail do usuário.

    Retorna:
        dict | None: Dicionário com os dados do usuário se encontrado, ou None caso contrário.
    """
    users = load_users()
    for u in users:
        if u["email"] == email:
            return u
    return None


def load_avisos():
    """Carrega a lista de avisos do arquivo JSON."""
    return load_json(AVISOS_FILE)


def save_avisos(avisos):
    """Salva a lista de avisos no arquivo JSON."""
    save_json(AVISOS_FILE, avisos)


def load_chat_turma():
    """Carrega o histórico de chat das turmas."""
    return load_json(CHAT_TURMA_FILE)


def save_chat_turma(chat):
    """Salva o histórico de chat das turmas."""
    save_json(CHAT_TURMA_FILE, chat)


def load_cursos():
    """Carrega a lista de cursos cadastrados."""
    return load_json(CURSOS_FILE)


def save_cursos(cursos):
    """Salva a lista de cursos cadastrados."""
    save_json(CURSOS_FILE, cursos)


def load_diario():
    """Carrega o diário de classe (registro de notas e presenças)."""
    return load_json(DIARIO_FILE)


def save_diario(diario):
    """Salva o diário de classe (registro de notas e presenças)."""
    save_json(DIARIO_FILE, diario)


# ===============================
# Funções auxiliares de lógica acadêmica
# ===============================
def gerar_matricula(curso_nome, periodo):
    """
    Gera um código de matrícula único com base no curso e período informados.

    Exemplo de formato: 'IN2103' → curso 'Informática', período 2, número aleatório 103.

    Parâmetros:
        curso_nome (str): Nome do curso (usado para gerar o prefixo).
        periodo (int | str): Período do aluno.

    Retorna:
        str: Código de matrícula no formato <duas letras do curso><período><número aleatório>.
    """
    prefixo = curso_nome[:2].upper()
    numero_random = random.randint(100, 999)
    return f"{prefixo}{int(periodo)}{numero_random}"


def parse_turma_nome(turma_nome):
    """
    Analisa o nome completo de uma turma e extrai o curso, a matéria e o período.

    Exemplo:
        Entrada: "Informática-Algoritmos-P2"
        Saída: ("Informática", "Algoritmos", 2)

    Parâmetros:
        turma_nome (str): Nome completo da turma, separado por hífens.

    Retorna:
        tuple: (curso, matéria, período)
               ou (None, None, None) se o formato for inválido.
    """
    partes = turma_nome.split('-')
    if len(partes) >= 3:
        curso = '-'.join(partes[:-2])
        materia = partes[-2]
        periodo_str = partes[-1]
        if periodo_str.startswith('P') and periodo_str[1:].isdigit():
            periodo = int(periodo_str[1:])
            return curso, materia, periodo
    return None, None, None