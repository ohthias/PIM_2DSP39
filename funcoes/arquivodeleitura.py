import json

def get_users_by_class(filename, class_name):
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

if __name__ == "__main__":
    
    target_class = "Turma A"
    filename = "users.json"

    users_from_class = get_users_by_class(filename, target_class)

    if users_from_class:
        print(f"Usuários da {target_class}:")
        for user in users_from_class:
            print(user)
    else:
        print(f"Nenhum usuário encontrado na {target_class}.")

