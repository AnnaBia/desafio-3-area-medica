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

3. Verifique a versão do Python:
   Windows:
    ```bash
    py -3 --version
    ```
   Linux/macOS:
    ```bash
    python3 --version
    ```

## Uso

1. Execute a classificação de um paciente (arquivo JSON com 1 paciente):
   Windows:
    ```bash
    py -3 main.py --entrada exemplo_paciente.json
    ```
   Linux/macOS:
    ```bash
    python3 main.py --entrada exemplo_paciente.json
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

3. Execute a suíte de testes:
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
