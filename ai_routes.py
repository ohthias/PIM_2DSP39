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

    # Criar estrutura JSON serializable para o histórico
    def normalize_history(raw_history):
        normalized = []
        for msg in raw_history:
            normalized.append({
                "role": msg.role,
                "parts": [str(p) for p in msg.parts]   # CONVERTE PARTS → TEXTO
            })
        return normalized

    # 1. Criar estrutura base
    if 'chat_histories' not in session:
        session['chat_histories'] = {}

    if user_email not in session['chat_histories']:
        session['chat_histories'][user_email] = []

    # 2. Recupera histórico serializável
    user_history = session['chat_histories'][user_email]

    try:
        # 3. Inicia a sessão com histórico NORMALIZADO
        chat_session = model.start_chat(history=[
            {"role": h["role"], "parts": h["parts"]} for h in user_history
        ])
        
        # 4. Envia a mensagem
        response = chat_session.send_message(user_message)

        # 5. Normaliza o novo histórico antes de salvar
        new_history = normalize_history(chat_session.history)

        session['chat_histories'][user_email] = new_history
        session.modified = True

        return jsonify({"response": response.text})
    
    except Exception as e:
        print(f"Erro ao interagir com o Gemini: {e}")
        return jsonify({"response": "Desculpe, ocorreu um erro ao processar sua solicitação."}), 500
