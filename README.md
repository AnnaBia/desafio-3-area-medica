# Desafio 03 - Sistema Especialista de Triagem SUS
Projeto desenvolvido para o desafio da disciplina de Inteligência Artificial (encadeamento progressivo). Este repositório contém um sistema especialista em Python para triagem de pacientes em UPA, com base no Protocolo de Manchester adaptado, regra de vulnerabilidade e regras de segunda ordem (E1 a E5).

## Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/downloads/)
- Biblioteca padrão do Python (sem dependências externas)
- [unittest](https://docs.python.org/3/library/unittest.html) para testes

## Instalação

1. Clone o repositório para sua máquina local:
    ```bash
    git clone https://github.com/AnnaBia/desafio-3-area-medica.git
    ```
   Se você baixou o projeto em `.zip`, apenas extraia a pasta e siga para o passo 2.

2. Navegue até o diretório do projeto:
    ```bash
    cd desafio-3-area-medica
    ```

3. Valide a versão e o interpretador Python que será usado:
   Windows:
    ```bash
    py -3 --version
    ```
   Linux/macOS:
    ```bash
    python3 --version
    ```

    O sistema requer Python 3.10 ou superior.

## Uso

Os arquivos `exemplo_paciente.json` e `exemplo_fila.json` são apenas demonstrações para facilitar o primeiro teste. O sistema funciona normalmente com arquivos JSON próprios.

### Formato de entrada JSON

Paciente único (sem `--fila`): enviar um objeto JSON.

Campos esperados no objeto de paciente:
- `id` (string): identificador do paciente.
- `hora_entrada` (string, formato `HH:MM`): horário de chegada.
- `idade` (número, opcional).
- `gestante` (booleano, opcional).
- `deficiencia` (booleano, opcional).
- `leituras` (lista): histórico de leituras clínicas em ordem cronológica.

Campos de cada leitura:
- `hora` (string, formato `HH:MM`) - recomendado.
- `spo2`, `frequencia_cardiaca`, `temperatura`, `escala_dor`, `glasgow`, `vomitos_por_hora` (numéricos, opcionais).
- `pulso_presente`, `respirando`, `consciente` (booleanos, opcionais).

Exemplo mínimo de paciente próprio:
```json
{
    "id": "PAC-001",
    "hora_entrada": "08:10",
    "leituras": [
        { "hora": "08:10", "spo2": 96, "escala_dor": 3 }
    ]
}
```

Modo fila (com `--fila`): pode receber um objeto único ou, preferencialmente, uma lista de objetos de paciente.

Exemplo de fila própria:
```json
[
    {
        "id": "PAC-001",
        "hora_entrada": "08:10",
        "leituras": [{ "hora": "08:10", "spo2": 96 }]
    },
    {
        "id": "PAC-002",
        "hora_entrada": "08:12",
        "leituras": [{ "hora": "08:12", "spo2": 92 }]
    }
]
```

1. Execute a classificação de um paciente (arquivo JSON com 1 paciente):
   Windows:
    ```bash
    py -3 main.py --entrada exemplo_paciente.json
    ```
   Linux/macOS:
    ```bash
    python3 main.py --entrada exemplo_paciente.json
    ```

    Exemplo com arquivo próprio:
    Windows:
     ```bash
     py -3 main.py --entrada meu_paciente.json
     ```
    Linux/macOS:
     ```bash
     python3 main.py --entrada meu_paciente.json
     ```

2. Execute em modo fila para desempate (arquivo JSON com lista de pacientes):
   Windows:
    ```bash
    py -3 main.py --entrada exemplo_fila.json --fila
    ```
   Linux/macOS:
    ```bash
    python3 main.py --entrada exemplo_fila.json --fila
    ```

    Exemplo com arquivo próprio:
    Windows:
     ```bash
     py -3 main.py --entrada minha_fila.json --fila
     ```
    Linux/macOS:
     ```bash
     python3 main.py --entrada minha_fila.json --fila
     ```

3. Execute a suíte de testes:
    Esses testes automatizados validam os cenários principais do sistema, incluindo classificação, vulnerabilidade, regras de segunda ordem (E1 a E5) e desempate da fila.
   Windows:
    ```bash
    py -3 -m unittest discover -s tests -v
    ```
   Linux/macOS:
    ```bash
    python3 -m unittest discover -s tests -v
    ```

## Observação

Este projeto foi estruturado para atender ao enunciado do desafio, incluindo:
- regras primárias (Níveis 1 a 5), vulnerabilidade e E1 a E5 representadas como dados;
- motor de inferência separado da base de conhecimento;
- log auditável das inferências;
- módulo de desempate determinístico e justificável;
- suíte de testes com os cenários obrigatórios;
- reflexão final em [REFLEXAO.md](REFLEXAO.md).

Arquivos principais do projeto:
- src/knowledge_base.py
- src/rule_engine.py
- src/tiebreaker.py
- src/cli.py
- tests/test_system.py
