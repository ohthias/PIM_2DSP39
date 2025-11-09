def calcular_previsao_nota(notas, pesos={"NP1": 0.4, "NP2": 0.6}, nota_minima=7):
    """
    Calcula a média prevista e indica risco de reprovação.
    """
    np1 = notas.get("NP1", 0)
    np2 = notas.get("NP2", 0)
    media_prevista = np1 * pesos.get("NP1", 0.5) + np2 * pesos.get("NP2", 0.5)
    risco_reprovacao = media_prevista < nota_minima
    return media_prevista, risco_reprovacao

def recomendar_estudo(aluno, turmas, materiais, diario, pesos={"NP1":0.4, "NP2":0.6}, nota_minima=7):
    recomendacoes = []

    notas = aluno.get("notas", {})
    for materia, nota_info in notas.items():
        media_prevista, risco = calcular_previsao_nota(nota_info, pesos, nota_minima)
        
        # Buscar aulas e materiais da turma
        for turma in turmas:
            if aluno["email"] in turma.get("alunos", []):
                turma_nome = turma["nome"]
                registro_turma = next((d for d in diario if d["turma"] == turma_nome), {"registros":[]})
                aulas_registradas = [r["aula"] for r in registro_turma["registros"]]
                total_aulas = len(aulas_registradas)
                aulas_faltantes = [f"Aula {i}" for i in range(1, total_aulas+1) if f"Aula {i}" not in aulas_registradas]

                materiais_da_turma = [m for m in materiais if m["turma"] == turma_nome]
                materiais_recomendados = [m for m in materiais_da_turma if materia.lower() in m["arquivo"].lower()]

                # Sempre adiciona recomendação, mas prioriza risco ou faltas
                for m in materiais_recomendados:
                    recomendacoes.append({
                        "materia": materia,
                        "arquivo": m["arquivo"],
                        "turma": turma_nome,
                        "media_prevista": round(media_prevista, 2),
                        "risco_reprovacao": risco,
                        "aulas_faltantes": aulas_faltantes
                    })

                # Se não houver materiais, ainda sugere revisão da matéria
                if not materiais_recomendados:
                    recomendacoes.append({
                        "materia": materia,
                        "arquivo": None,
                        "turma": turma_nome,
                        "media_prevista": round(media_prevista, 2),
                        "risco_reprovacao": risco,
                        "aulas_faltantes": aulas_faltantes
                    })

    return recomendacoes
