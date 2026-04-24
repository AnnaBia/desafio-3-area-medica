from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .audit import RegistradorAuditoria
from .knowledge_base import (
    COR_POR_NIVEL,
    REGRA_VULNERABILIDADE,
    REGRAS_CLASSIFICACAO_PRIMARIA,
    REGRAS_SEGUNDA_ORDEM,
    SLA_POR_NIVEL,
)


def converter_hhmm_para_minutos(valor_hhmm: Optional[str]) -> Optional[int]:
    if not valor_hhmm or not isinstance(valor_hhmm, str) or ":" not in valor_hhmm:
        return None

    partes = valor_hhmm.split(":", 1)
    try:
        horas = int(partes[0])
        minutos = int(partes[1])
    except ValueError:
        return None

    if horas < 0 or horas > 23 or minutos < 0 or minutos > 59:
        return None

    return horas * 60 + minutos


def obter_seguro(dado: Dict[str, Any], chave: str, padrao: Any = None) -> Any:
    if chave in dado:
        return dado[chave]
    return padrao


def comparar(valor_esquerda: Any, operador: str, valor_direita: Any) -> bool:
    if operador == "eh_nulo" or operador == "is_none":
        return valor_esquerda is None
    if operador == "nao_eh_nulo" or operador == "is_not_none":
        return valor_esquerda is not None
    if valor_esquerda is None or valor_direita is None:
        return False

    operacoes = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
    }
    funcao = operacoes.get(operador)
    if funcao is None:
        return False

    try:
        return funcao(valor_esquerda, valor_direita)
    except TypeError:
        return False


def avaliar_expressao(expressao: Dict[str, Any], fatos: Dict[str, Any]) -> bool:
    if "todos" in expressao:
        for item in expressao["todos"]:
            if not avaliar_expressao(item, fatos):
                return False
        return True

    if "qualquer" in expressao:
        for item in expressao["qualquer"]:
            if avaliar_expressao(item, fatos):
                return True
        return False

    if "all" in expressao:
        for item in expressao["all"]:
            if not avaliar_expressao(item, fatos):
                return False
        return True

    if "any" in expressao:
        for item in expressao["any"]:
            if avaliar_expressao(item, fatos):
                return True
        return False

    chave_fato = expressao.get("fato")
    if chave_fato is None:
        chave_fato = expressao.get("fact")

    valor_esquerda = obter_seguro(fatos, chave_fato)

    operador = expressao.get("operador")
    if operador is None:
        operador = expressao.get("op")

    chave_fato_direita = expressao.get("fato_direita")
    if chave_fato_direita is None:
        chave_fato_direita = expressao.get("right_fact")

    if chave_fato_direita is not None:
        valor_direita = obter_seguro(fatos, chave_fato_direita)
    else:
        if "valor" in expressao:
            valor_direita = expressao.get("valor")
        else:
            valor_direita = expressao.get("value")

    return comparar(valor_esquerda, operador, valor_direita)


def detectar_sinais_estaveis(leitura: Dict[str, Any]) -> bool:
    spo2 = obter_seguro(leitura, "spo2")
    frequencia = obter_seguro(leitura, "frequencia_cardiaca")
    temperatura = obter_seguro(leitura, "temperatura")

    condicoes = []
    if spo2 is not None:
        condicoes.append(spo2 >= 94)
    if frequencia is not None:
        condicoes.append(50 <= frequencia <= 120)
    if temperatura is not None:
        condicoes.append(temperatura < 38.0)

    if not condicoes:
        return True
    return all(condicoes)


def contar_sinais_piorados(leitura_anterior: Dict[str, Any], leitura_atual: Dict[str, Any]) -> int:
    if not leitura_anterior:
        return 0

    direcao_por_sinal = {
        "spo2": "diminui",
        "frequencia_cardiaca": "extremo",
        "temperatura": "aumenta",
        "escala_dor": "aumenta",
        "glasgow": "diminui",
        "vomitos_por_hora": "aumenta",
    }

    quantidade_pioras = 0
    for sinal, direcao in direcao_por_sinal.items():
        valor_anterior = obter_seguro(leitura_anterior, sinal)
        valor_atual = obter_seguro(leitura_atual, sinal)
        if valor_anterior is None or valor_atual is None:
            continue

        if direcao == "aumenta" and valor_atual > valor_anterior:
            quantidade_pioras += 1
        elif direcao == "diminui" and valor_atual < valor_anterior:
            quantidade_pioras += 1
        elif direcao == "extremo" and abs(valor_atual - 80) > abs(valor_anterior - 80):
            quantidade_pioras += 1

    return quantidade_pioras


@dataclass
class EstadoPaciente:
    id_paciente: str
    perfil: Dict[str, Any]
    nivel_atual: int = 5
    cor_atual: str = "azul"
    minuto_entrada_no_nivel: Optional[int] = None
    historico: List[Dict[str, Any]] = field(default_factory=list)
    derivado: Dict[str, Any] = field(default_factory=dict)


class MotorEncadeamentoProgressivo:
    def __init__(self) -> None:
        self.registrador = RegistradorAuditoria()

    def _aplicar_regra_sem_rebaixamento(self, estado: EstadoPaciente, nivel_proposto: int) -> int:
        return min(estado.nivel_atual, nivel_proposto)

    def _eh_vulneravel(self, paciente: Dict[str, Any]) -> bool:
        fatos = {
            "idade": obter_seguro(paciente, "idade"),
            "gestante": bool(obter_seguro(paciente, "gestante", False)),
            "deficiencia": bool(obter_seguro(paciente, "deficiencia", False)),
        }
        return avaliar_expressao(REGRA_VULNERABILIDADE["quando"], fatos)

    def _avaliar_regras_primarias(self, fatos: Dict[str, Any]) -> List[Dict[str, Any]]:
        regras_disparadas = []
        for regra in REGRAS_CLASSIFICACAO_PRIMARIA:
            if avaliar_expressao(regra["quando"], fatos):
                regras_disparadas.append(regra)
        return regras_disparadas

    def _montar_fatos_da_leitura(
        self,
        paciente: Dict[str, Any],
        leitura_anterior: Dict[str, Any],
        leitura_atual: Dict[str, Any],
        estado: EstadoPaciente,
    ) -> Dict[str, Any]:
        fatos = dict(leitura_atual)
        fatos["idade"] = obter_seguro(paciente, "idade")
        fatos["gestante"] = bool(obter_seguro(paciente, "gestante", False))
        fatos["deficiencia"] = bool(obter_seguro(paciente, "deficiencia", False))
        fatos["vulneravel"] = self._eh_vulneravel(paciente)
        fatos["sinais_estaveis"] = detectar_sinais_estaveis(leitura_atual)

        minuto_atual = converter_hhmm_para_minutos(obter_seguro(leitura_atual, "hora"))
        minuto_entrada = converter_hhmm_para_minutos(obter_seguro(paciente, "hora_entrada"))
        minutos_espera = None
        if minuto_atual is not None and minuto_entrada is not None:
            minutos_espera = max(0, minuto_atual - minuto_entrada)

        fatos["minutos_espera"] = minutos_espera
        fatos["minutos_sla"] = SLA_POR_NIVEL.get(estado.nivel_atual, 120)
        fatos["quantidade_sinais_pioraram"] = contar_sinais_piorados(leitura_anterior, leitura_atual)

        temperatura_anterior = obter_seguro(leitura_anterior, "temperatura")
        temperatura_atual = obter_seguro(leitura_atual, "temperatura")
        if temperatura_anterior is not None and temperatura_atual is not None:
            fatos["delta_temperatura"] = temperatura_atual - temperatura_anterior
        else:
            fatos["delta_temperatura"] = 0.0

        fatos["minutos_reclassificacao_3_para_2"] = self._encontrar_minutos_reclassificacao_3_para_2(estado)
        fatos["quantidade_violacoes_sla"] = int(estado.derivado.get("quantidade_violacoes_sla", 0))
        fatos["alerta_sla_emitido_nesta_leitura"] = False
        fatos["e2_aplicada_na_leitura"] = False
        fatos["e4_aplicada"] = bool(estado.derivado.get("e4_aplicada", False))
        fatos["e5_aplicada"] = bool(estado.derivado.get("e5_aplicada", False))

        return fatos

    def _encontrar_minutos_reclassificacao_3_para_2(self, estado: EstadoPaciente) -> Optional[int]:
        if len(estado.historico) < 2:
            return None

        ultima_classificacao = estado.historico[-1]
        classificacao_anterior = estado.historico[-2]

        if classificacao_anterior.get("nivel") == 3 and ultima_classificacao.get("nivel") == 2:
            minuto_1 = converter_hhmm_para_minutos(classificacao_anterior.get("hora"))
            minuto_2 = converter_hhmm_para_minutos(ultima_classificacao.get("hora"))
            if minuto_1 is not None and minuto_2 is not None:
                return max(0, minuto_2 - minuto_1)

        return None

    def _resumo_fatos_para_log(self, fatos: Dict[str, Any]) -> Dict[str, Any]:
        chaves = [
            "spo2",
            "escala_dor",
            "glasgow",
            "frequencia_cardiaca",
            "temperatura",
            "vomitos_por_hora",
            "vulneravel",
            "minutos_espera",
            "minutos_sla",
            "quantidade_sinais_pioraram",
            "delta_temperatura",
            "quantidade_violacoes_sla",
            "minutos_reclassificacao_3_para_2",
        ]
        resumo = {}
        for chave in chaves:
            resumo[chave] = fatos.get(chave)
        return resumo

    def _aplicar_acoes_segunda_ordem(
        self,
        estado: EstadoPaciente,
        fatos: Dict[str, Any],
        regra: Dict[str, Any],
        horario: str,
    ) -> bool:
        houve_mudanca = False

        def acao_emitir_evento(acao: Dict[str, Any]) -> None:
            nonlocal houve_mudanca
            eventos = estado.derivado.setdefault("eventos", [])
            evento = {
                "hora": horario,
                "evento": acao["evento"],
                "mensagem": acao.get("mensagem", ""),
                "regra": regra["id"],
            }
            eventos.append(evento)
            houve_mudanca = True
            self.registrador.registrar(horario, regra["id"], self._resumo_fatos_para_log(fatos), evento, "evento gerado")

        def acao_definir_fato(acao: Dict[str, Any]) -> None:
            nonlocal houve_mudanca
            nome_fato = acao["fato"]
            valor = acao["valor"]
            if fatos.get(nome_fato) != valor:
                fatos[nome_fato] = valor
                estado.derivado[nome_fato] = valor
                houve_mudanca = True
                self.registrador.registrar(
                    horario,
                    regra["id"],
                    self._resumo_fatos_para_log(fatos),
                    {nome_fato: valor},
                    "fato atualizado",
                )

        def acao_incrementar_contador(acao: Dict[str, Any]) -> None:
            nonlocal houve_mudanca
            nome_contador = acao["contador"]
            passo = int(acao.get("passo", 1))
            valor_atual = int(estado.derivado.get(nome_contador, 0))
            novo_valor = valor_atual + passo
            estado.derivado[nome_contador] = novo_valor
            fatos[nome_contador] = novo_valor
            houve_mudanca = True
            self.registrador.registrar(
                horario,
                regra["id"],
                self._resumo_fatos_para_log(fatos),
                {nome_contador: novo_valor},
                "contador incrementado",
            )

        def acao_elevar_prioridade(acao: Dict[str, Any]) -> None:
            nonlocal houve_mudanca
            niveis = int(acao.get("niveis", 1))
            nivel_proposto = max(1, estado.nivel_atual - niveis)
            nivel_ajustado = self._aplicar_regra_sem_rebaixamento(estado, nivel_proposto)
            if nivel_ajustado < estado.nivel_atual:
                estado.nivel_atual = nivel_ajustado
                estado.cor_atual = COR_POR_NIVEL[estado.nivel_atual]
                houve_mudanca = True
                self.registrador.registrar(
                    horario,
                    regra["id"],
                    self._resumo_fatos_para_log(fatos),
                    {"nivel": estado.nivel_atual},
                    acao.get("motivo", "prioridade elevada"),
                )

        def acao_definir_prioridade(acao: Dict[str, Any]) -> None:
            nonlocal houve_mudanca
            nivel_proposto = int(acao["nivel"])
            nivel_ajustado = self._aplicar_regra_sem_rebaixamento(estado, nivel_proposto)
            if nivel_ajustado < estado.nivel_atual:
                estado.nivel_atual = nivel_ajustado
                estado.cor_atual = COR_POR_NIVEL[estado.nivel_atual]
                houve_mudanca = True
                self.registrador.registrar(
                    horario,
                    regra["id"],
                    self._resumo_fatos_para_log(fatos),
                    {"nivel": estado.nivel_atual},
                    acao.get("motivo", "prioridade ajustada"),
                )

        acoes_disponiveis = {
            "emitir_evento": acao_emitir_evento,
            "definir_fato": acao_definir_fato,
            "incrementar_contador": acao_incrementar_contador,
            "elevar_prioridade": acao_elevar_prioridade,
            "definir_prioridade": acao_definir_prioridade,
        }

        for acao in regra.get("acoes", []):
            tipo_acao = acao.get("tipo")
            executora = acoes_disponiveis.get(tipo_acao)
            if executora is not None:
                executora(acao)

        return houve_mudanca

    def _executar_encadeamento_progressivo(self, estado: EstadoPaciente, fatos: Dict[str, Any], horario: str) -> None:
        rodadas_maximas = 5
        rodada = 0
        while rodada < rodadas_maximas:
            houve_mudanca = False
            for regra in REGRAS_SEGUNDA_ORDEM:
                if avaliar_expressao(regra["quando"], fatos):
                    mudou = self._aplicar_acoes_segunda_ordem(estado, fatos, regra, horario)
                    if mudou:
                        houve_mudanca = True
            if not houve_mudanca:
                break
            rodada += 1

    def processar_paciente(self, paciente: Dict[str, Any]) -> Dict[str, Any]:
        id_paciente = obter_seguro(paciente, "id", "SEM-ID")
        estado = EstadoPaciente(id_paciente=id_paciente, perfil=deepcopy(paciente))

        leituras = obter_seguro(paciente, "leituras", [])
        if leituras is None:
            leituras = []

        leitura_anterior: Dict[str, Any] = {}

        for leitura_atual in leituras:
            horario = obter_seguro(leitura_atual, "hora", "00:00")
            fatos = self._montar_fatos_da_leitura(paciente, leitura_anterior, leitura_atual, estado)

            regras_disparadas = self._avaliar_regras_primarias(fatos)

            niveis_propostos = []
            for regra in regras_disparadas:
                niveis_propostos.append(regra["nivel_proposto"])

            if niveis_propostos:
                nivel_proposto = min(niveis_propostos)
            else:
                nivel_proposto = 5

            if regras_disparadas:
                motivos_primarios = []
                for regra in regras_disparadas:
                    motivos_primarios.append(regra["id"])
            else:
                motivos_primarios = ["DEFAULT_N5"]

            if self._eh_vulneravel(paciente) and nivel_proposto > 1:
                nivel_proposto -= 1
                motivos_primarios.append(REGRA_VULNERABILIDADE["id"])

            nivel_ajustado = self._aplicar_regra_sem_rebaixamento(estado, nivel_proposto)
            mudou_nivel = nivel_ajustado < estado.nivel_atual

            if mudou_nivel:
                estado.nivel_atual = nivel_ajustado
                estado.cor_atual = COR_POR_NIVEL[estado.nivel_atual]
                estado.minuto_entrada_no_nivel = converter_hhmm_para_minutos(horario)

            classificacao = {
                "hora": horario,
                "nivel": estado.nivel_atual,
                "cor": estado.cor_atual,
                "motivos": motivos_primarios,
                "fatos": self._resumo_fatos_para_log(fatos),
            }
            estado.historico.append(classificacao)
            self.registrador.registrar(
                horario,
                "PRIMARIA",
                self._resumo_fatos_para_log(fatos),
                classificacao,
                "classificacao primaria",
            )

            fatos["minutos_sla"] = SLA_POR_NIVEL.get(estado.nivel_atual, 120)
            fatos["minutos_reclassificacao_3_para_2"] = self._encontrar_minutos_reclassificacao_3_para_2(estado)

            self._executar_encadeamento_progressivo(estado, fatos, horario)

            if not mudou_nivel and estado.minuto_entrada_no_nivel is None:
                estado.minuto_entrada_no_nivel = converter_hhmm_para_minutos(horario)

            leitura_anterior = dict(leitura_atual)

        minutos_espera_total = None
        if leituras:
            ultimo_minuto = converter_hhmm_para_minutos(obter_seguro(leituras[-1], "hora"))
            minuto_entrada = converter_hhmm_para_minutos(obter_seguro(paciente, "hora_entrada"))
            if ultimo_minuto is not None and minuto_entrada is not None:
                minutos_espera_total = max(0, ultimo_minuto - minuto_entrada)

        return {
            "id": estado.id_paciente,
            "nivel_atual": estado.nivel_atual,
            "cor_atual": estado.cor_atual,
            "historico": estado.historico,
            "derivado": estado.derivado,
            "vulneravel": self._eh_vulneravel(paciente),
            "tempo_espera_minutos": minutos_espera_total,
            "tempo_no_nivel_minutos": self._tempo_no_nivel_atual_em_minutos(estado, leituras),
            "sla_minutos_nivel_atual": SLA_POR_NIVEL.get(estado.nivel_atual, 120),
            "log": self.registrador.entradas,
        }

    def _tempo_no_nivel_atual_em_minutos(self, estado: EstadoPaciente, leituras: List[Dict[str, Any]]) -> int:
        if not leituras:
            return 0

        ultimo_minuto = converter_hhmm_para_minutos(obter_seguro(leituras[-1], "hora"))
        minuto_inicio_nivel = estado.minuto_entrada_no_nivel
        if ultimo_minuto is None or minuto_inicio_nivel is None:
            return 0

        return max(0, ultimo_minuto - minuto_inicio_nivel)
