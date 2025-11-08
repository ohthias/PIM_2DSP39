def recomendar_materiais(aluno, turmas, materiais, pesos):
    """
    Gera recomendações de estudo para o aluno com base em notas.
    
    aluno: dict do usuário
    turmas: lista de turmas
    materiais: lista de materiais
    pesos: dict de pesos {'NP1': 0.4, 'NP2': 0.6}
    
    Retorna: lista de materiais recomendados
    """
    recomendados = []

    # Percorre cada matéria do aluno
    notas = aluno.get("notas", {})
    for materia, nota_info in notas.items():
        np1 = nota_info.get("NP1", 0)
        np2 = nota_info.get("NP2", 0)
        media = np1*pesos.get("NP1",0.5) + np2*pesos.get("NP2",0.5)

        # Se a média for baixa, prioriza essa matéria
        if media < 7:
            # Busca materiais da turma correspondente
            for turma in turmas:
                if aluno["email"] in turma.get("alunos", []):
                    nome_turma = turma["nome"]
                    materias_da_turma = [m for m in materiais if m["turma"] == nome_turma]
                    for m in materias_da_turma:
                        # Só adiciona materiais relacionados à matéria com dificuldade
                        if materia.lower() in m["arquivo"].lower() or materia.lower() in m.get("descricao","").lower():
                            recomendados.append({
                                "materia": materia,
                                "arquivo": m["arquivo"],
                                "turma": nome_turma
                            })
    return recomendados
