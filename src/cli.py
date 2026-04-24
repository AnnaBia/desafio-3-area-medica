import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .rule_engine import MotorEncadeamentoProgressivo
from .tiebreaker import ordenar_pacientes_mesmo_nivel


def processar_paciente_unico(dados_paciente: Dict[str, Any]) -> Dict[str, Any]:
    motor = MotorEncadeamentoProgressivo()
    return motor.processar_paciente(dados_paciente)


def processar_fila(lista_pacientes: List[Dict[str, Any]]) -> Dict[str, Any]:
    motor = MotorEncadeamentoProgressivo()
    estados = []
    for dados_paciente in lista_pacientes:
        estado = motor.processar_paciente(dados_paciente)
        estados.append(estado)

    if not estados:
        return {"fila": [], "explicacoes": []}

    menor_nivel = min(item["nivel_atual"] for item in estados)
    candidatos = []
    for item in estados:
        if item["nivel_atual"] == menor_nivel:
            candidatos.append(item)

    ordenados, explicacoes = ordenar_pacientes_mesmo_nivel(candidatos)

    fila = []
    for item in ordenados:
        fila.append(item["id"])

    return {
        "nivel_prioritario": menor_nivel,
        "fila": fila,
        "explicacoes": explicacoes,
        "estados": estados,
    }


def executar_cli() -> None:
    parser = argparse.ArgumentParser(description="Sistema especialista SUS com encadeamento progressivo.")
    parser.add_argument(
        "--entrada",
        "--input",
        dest="entrada",
        required=True,
        help="Arquivo JSON com paciente unico ou lista de pacientes.",
    )
    parser.add_argument(
        "--fila",
        "--queue",
        dest="fila",
        action="store_true",
        help="Ativa modo de fila para desempate.",
    )
    args = parser.parse_args()

    conteudo = json.loads(Path(args.entrada).read_text(encoding="utf-8"))

    if args.fila:
        pacientes = conteudo if isinstance(conteudo, list) else [conteudo]
        saida = processar_fila(pacientes)
    else:
        if isinstance(conteudo, list):
            raise SystemExit("Use --fila para processar lista de pacientes.")
        saida = processar_paciente_unico(conteudo)

    print(json.dumps(saida, indent=2, ensure_ascii=False))


def main() -> None:
    executar_cli()


if __name__ == "__main__":
    main()
