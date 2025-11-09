# ai_routes.py
from flask import Blueprint, request, jsonify, render_template, session
from dotenv import load_dotenv
import google.generativeai as genai
import os

# ----- Blueprint -----
ai_blueprint = Blueprint('ai', __name__)

# ----- Configuração do Gemini -----
load_dotenv()

try:
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("A chave GEMINI_API_KEY não foi encontrada no arquivo .env.")

    genai.configure(api_key=API_KEY)

    # Inicializa o modelo de chat com contexto acadêmico
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=(
            "Você é um assistente acadêmico. Suas respostas devem ser informativas, "
            "baseadas em fatos, bem estruturadas e focadas em tópicos de ciências, história, literatura ou matemática."
        )
    )

except Exception as e:
    print(f"Erro na inicialização do Gemini: {e}")
    model = None

# ----- Rotas -----
@ai_blueprint.route('/chatbot')
def chatbot():
    """Renderiza a interface do chatbot."""
    return render_template('chatbot.html')


@ai_blueprint.route('/chat', methods=['POST'])
def chat():
    """Recebe a mensagem do usuário, interage com o Gemini e retorna a resposta."""
    
    if not model:
        return jsonify({"response": "Serviço de IA indisponível."}), 503

    user_email = session.get('email')
    if not user_email:
        return jsonify({"response": "Usuário não logado."}), 401

    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"response": "Por favor, digite uma pergunta."}), 400

    # Inicializa histórico do usuário se não existir
    if 'chat_sessions' not in session:
        session['chat_sessions'] = {}

    if user_email not in session['chat_sessions']:
        session['chat_sessions'][user_email] = model.start_chat(history=[])

    chat_session = session['chat_sessions'][user_email]

    try:
        response = chat_session.send_message(user_message)
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Erro ao interagir com o Gemini: {e}")
        return jsonify({"response": "Desculpe, ocorreu um erro ao processar sua solicitação."}), 500
