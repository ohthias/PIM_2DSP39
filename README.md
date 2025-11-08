# PIM_2DSP39 – INTEC

**Projeto Integrado Multidisciplinar – 2º Semestre**

Este projeto é um **sistema acadêmico completo**, desenvolvido em **Python com Flask**, que permite gerenciar usuários, cursos, turmas, materiais, avisos, diários e notas de alunos. O sistema inclui funcionalidades para alunos, professores e administradores, com persistência de dados em arquivos JSON e integração opcional com uma biblioteca C para cálculo de médias.

---

## Funcionalidades Principais

### Para Alunos

* Visualizar dashboard personalizado com turmas, materiais e avisos.
* Acessar conteúdos de suas turmas.
* Consultar notas e médias calculadas.
* Participar de chats da turma.

### Para Professores

* Criar, editar e gerenciar turmas.
* Lançar e atualizar notas de alunos com cálculo de média via biblioteca C.
* Adicionar materiais e avisos nas turmas.
* Registrar aulas no diário da turma.
* Gerenciar alunos em turmas (adicionar/remover).

### Para Administradores

* Criar, editar e remover cursos.
* Gerenciar professores e alunos.
* Criar turmas automaticamente ao editar cursos.

---

## Estrutura do Projeto

```text
PIM_2DSP39/
├─ app.py                   # Arquivo principal Flask
├─ utils.py                 # Funções auxiliares, ex: cálculo de média
├─ libs/
│  └─ notas.dll             # Biblioteca C para cálculo de média
├─ data/                    # Armazena os arquivos JSON
│  ├─ users.json
│  ├─ turmas.json
│  ├─ materiais.json
│  ├─ avisos.json
│  ├─ chat_turma.json
│  ├─ diario_turma.json
│  └─ cursos.json
├─ static/                  # Arquivos estáticos (CSS, JS, uploads)
│  └─ materiais/
└─ templates/               # Templates HTML para Flask
```

---

## Tecnologias Utilizadas

* **Python 3.x**
* **Flask** (web framework)
* **Bootstrap 5** (frontend)
* **JSON** (persistência de dados)
* **C / ctypes** (cálculo de médias via DLL)

---

## Pré-requisitos

* Python 3.x instalado
* Pip para instalação de dependências
* Sistema Windows (se for usar a DLL `.dll`) ou Linux (se usar `.so`)

---

## Instalação e Execução

1. Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd PIM_2DSP39
```

2. Instale dependências:

```bash
pip install Flask
```

3. Execute o servidor:

```bash
flask run
```

4. Acesse no navegador:

```
http://127.0.0.1:5000/
```

---

## Configuração da Biblioteca C (DLL)

O cálculo da média pode ser feito via **biblioteca C** para desempenho:

```python
import ctypes
lib = ctypes.CDLL("libs/notas.dll")
lib.calcular_media.restype = ctypes.c_double
lib.calcular_media.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]

def calcular_media_c(np1, np2, peso_np1=0.4, peso_np2=0.6):
    return lib.calcular_media(np1, np2, peso_np1, peso_np2)
```

> Certifique-se de que a DLL está no caminho correto `libs/notas.dll`. Para Linux, substitua por `.so`.

---

## Estrutura de Dados

Exemplo de um usuário aluno:

```json
{
    "fullname": "Maria Silva",
    "email": "maria@teste.com",
    "password": "<hash>",
    "role": "student",
    "curso": "Análise de Sistemas",
    "periodo_atual": 1,
    "matricula": "AN01023",
    "notas": {
        "Matemática": {"NP1": 8.0, "NP2": 7.5, "media": 7.7}
    }
}
```