import json

def leitura_de_arquivos_em_G(filename, class_name):
    """
    Lê um arquivo JSON e retorna uma lista de usuários de uma turma específica.

    Args:
        filename (str): O nome do arquivo JSON.
        class_name (str): O nome da turma a ser filtrada.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um usuário da turma.
              Retorna uma lista vazia se a turma não for encontrada ou o arquivo não existir.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            # Garante que 'data' é uma lista e filtra por 'turma'
            if isinstance(data, list):
                users_by_class = [user for user in data if user.get('turma') == class_name]
                return users_by_class
            else:
                return []
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        return []
    except json.JSONDecodeError:
        print(f"Erro: Não foi possível decodificar o arquivo JSON '{filename}'.")
        return []

import json
import os

def adicionar_arquivo_em_json(caminho_arquivo=None):
    """
    Se 'caminho_arquivo' for informado, lê esse JSON e adiciona os dados ao user.json.
    Se não for informado, pede nome e turma para adicionar manualmente.
    """

    if not os.path.exists('user.json'):
        with open('user.json', 'w', encoding='utf-8') as arquivo:
            json.dump([], arquivo, indent=4, ensure_ascii=False)

    with open('user.json', 'r', encoding='utf-8') as arquivo:
        try:
            dados_existentes = json.load(arquivo)
        except json.JSONDecodeError:
            dados_existentes = []

    if caminho_arquivo:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo_turma:
                novos_dados = json.load(arquivo_turma)

            if isinstance(novos_dados, dict):
                novos_dados = [novos_dados]

            dados_existentes.extend(novos_dados)

            print(f"{len(novos_dados)} registros adicionados de '{caminho_arquivo}'.")
        except FileNotFoundError:
            print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
            return
        except json.JSONDecodeError:
            print("Erro: O arquivo informado não está em formato JSON válido.")
            return
    else:

        nome = input("Digite o nome do aluno: ")
        turma = input("Digite a turma: ")
        novo_registro = {"nome": nome, "turma": turma}
        dados_existentes.append(novo_registro)
        print(f"Usuário '{nome}' adicionado à turma '{turma}'.")

    with open('user.json', 'w', encoding='utf-8') as arquivo:
        json.dump(dados_existentes, arquivo, indent=4, ensure_ascii=False)

    print("Arquivo 'user.json' atualizado com sucesso!")


