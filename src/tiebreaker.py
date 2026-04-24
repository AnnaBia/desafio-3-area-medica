def calcular_risco_objetivo(estado):
    """Calcula um score simples de risco para desempatar pacientes do mesmo nivel."""
    derivado = estado.get("derivado", {})
    historico = estado.get("historico", [])
    ultimos_fatos = {}
    if historico:
        ultimos_fatos = historico[-1].get("fatos", {})

    pioras = float(ultimos_fatos.get("quantidade_sinais_pioraram") or 0)
    spo2 = ultimos_fatos.get("spo2")
    risco_spo2 = 0.0
    if spo2 is not None:
        risco_spo2 = max(0.0, (95.0 - float(spo2)) / 2.0)

    violacoes_sla = float(derivado.get("quantidade_violacoes_sla", 0))
    return (2.0 * pioras) + risco_spo2 + (1.5 * violacoes_sla)


def tempo_para_violar_sla(estado):
    espera = float(estado.get("tempo_espera_minutos") or 0)
    sla = float(estado.get("sla_minutos_nivel_atual") or 120)
    return sla - espera


def ordenar_pacientes_mesmo_nivel(estados):
    """Ordena pacientes do mesmo nivel com criterio fixo e auditavel.

    Ordem:
    1) Maior risco objetivo
    2) Maior tempo no nivel atual
    3) Menor tempo para violar SLA
    4) Vulneravel (desempate residual)
    5) ID em ordem alfabetica
    """
    itens = []

    for estado in estados:
        risco = calcular_risco_objetivo(estado)
        falta_sla = tempo_para_violar_sla(estado)
        tempo_no_nivel = float(estado.get("tempo_no_nivel_minutos") or 0)
        vulneravel = 1 if estado.get("vulneravel") else 0
        paciente_id = str(estado.get("id"))

        chave_ordenacao = (
            -risco,
            -tempo_no_nivel,
            falta_sla,
            -vulneravel,
            paciente_id,
        )

        metricas = {
            "id": paciente_id,
            "risco": round(risco, 2),
            "tempo_para_violar_sla": round(falta_sla, 2),
            "tempo_no_nivel": int(tempo_no_nivel),
            "vulneravel": bool(vulneravel),
        }

        itens.append((estado, chave_ordenacao, metricas))

    itens.sort(key=lambda item: item[1])

    ordenados = []
    for item in itens:
        ordenados.append(item[0])

    explicacoes = []
    posicao = 1
    for item in itens:
        metricas = item[2]
        texto = (
            f"posicao {posicao}: paciente {metricas['id']} por risco={metricas['risco']}, "
            f"tempo_para_violar_sla={metricas['tempo_para_violar_sla']} min, "
            f"tempo_no_nivel={metricas['tempo_no_nivel']} min, vulneravel={metricas['vulneravel']}"
        )
        explicacoes.append(texto)
        posicao += 1

    return ordenados, explicacoes


def escolher_proximo_paciente(estados):
    if not estados:
        return {}
    resultado = ordenar_pacientes_mesmo_nivel(estados)
    ordenados = resultado[0]
    return ordenados[0]
