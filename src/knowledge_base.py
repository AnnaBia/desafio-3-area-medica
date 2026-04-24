SLA_POR_NIVEL = {
    1: 0,
    2: 10,
    3: 30,
    4: 60,
    5: 120,
}

COR_POR_NIVEL = {
    1: "vermelho",
    2: "laranja",
    3: "amarelo",
    4: "verde",
    5: "azul",
}

REGRAS_CLASSIFICACAO_PRIMARIA = [
    {
        "id": "N1_CARDIORRESP",
        "tipo": "primaria",
        "descricao": "Nivel 1 por ausencia de pulso ou apneia confirmada.",
        "nivel_proposto": 1,
        "quando": {
            "qualquer": [
                {"fato": "pulso_presente", "operador": "==", "valor": False},
                {"fato": "respirando", "operador": "==", "valor": False},
            ]
        },
    },
    {
        "id": "N2_MUITO_URGENTE",
        "tipo": "primaria",
        "descricao": "Nivel 2 por hipoxemia grave, dor intensa, Glasgow baixo ou FC extrema.",
        "nivel_proposto": 2,
        "quando": {
            "qualquer": [
                {"fato": "spo2", "operador": "<", "valor": 90},
                {"fato": "escala_dor", "operador": ">=", "valor": 8},
                {"fato": "glasgow", "operador": "<", "valor": 14},
                {"fato": "frequencia_cardiaca", "operador": ">", "valor": 150},
                {"fato": "frequencia_cardiaca", "operador": "<", "valor": 40},
            ]
        },
    },
    {
        "id": "N3_URGENTE",
        "tipo": "primaria",
        "descricao": "Nivel 3 por febre alta, dor moderada, vomitos repetidos ou FC alterada.",
        "nivel_proposto": 3,
        "quando": {
            "qualquer": [
                {"fato": "temperatura", "operador": ">", "valor": 39.0},
                {
                    "todos": [
                        {"fato": "escala_dor", "operador": ">=", "valor": 5},
                        {"fato": "escala_dor", "operador": "<=", "valor": 7},
                    ]
                },
                {"fato": "vomitos_por_hora", "operador": ">", "valor": 3},
                {
                    "todos": [
                        {"fato": "frequencia_cardiaca", "operador": ">=", "valor": 120},
                        {"fato": "frequencia_cardiaca", "operador": "<=", "valor": 150},
                    ]
                },
                {
                    "todos": [
                        {"fato": "frequencia_cardiaca", "operador": ">=", "valor": 40},
                        {"fato": "frequencia_cardiaca", "operador": "<=", "valor": 50},
                    ]
                },
            ]
        },
    },
    {
        "id": "N4_POUCO_URGENTE",
        "tipo": "primaria",
        "descricao": "Nivel 4 por dor leve com sinais estaveis.",
        "nivel_proposto": 4,
        "quando": {
            "todos": [
                {"fato": "escala_dor", "operador": ">=", "valor": 1},
                {"fato": "escala_dor", "operador": "<=", "valor": 4},
                {"fato": "sinais_estaveis", "operador": "==", "valor": True},
            ]
        },
    },
    {
        "id": "N5_NAO_URGENTE",
        "tipo": "primaria",
        "descricao": "Nivel 5 por ausencia de dor relevante e estabilidade geral.",
        "nivel_proposto": 5,
        "quando": {
            "todos": [
                {
                    "qualquer": [
                        {"fato": "escala_dor", "operador": "==", "valor": 0},
                        {"fato": "escala_dor", "operador": "eh_nulo", "valor": True},
                    ]
                },
                {"fato": "sinais_estaveis", "operador": "==", "valor": True},
            ]
        },
    },
]

REGRA_VULNERABILIDADE = {
    "id": "VULN_SUS_2017",
    "tipo": "modificador_primario",
    "descricao": "Eleva um nivel para idosos, gestantes ou deficiencia fisica grave.",
    "quando": {
        "qualquer": [
            {"fato": "idade", "operador": ">=", "valor": 60},
            {"fato": "gestante", "operador": "==", "valor": True},
            {"fato": "deficiencia", "operador": "==", "valor": True},
        ]
    },
    "efeito": {
        "acao": "elevar_um_nivel",
    },
}

REGRAS_SEGUNDA_ORDEM = [
    {
        "id": "E1_RECLASS_3_TO_2_FAST",
        "tipo": "segunda_ordem",
        "descricao": "Reclassificacao de nivel 3 para 2 em menos de 30 min.",
        "quando": {
            "todos": [
                {"fato": "minutos_reclassificacao_3_para_2", "operador": "nao_eh_nulo", "valor": True},
                {"fato": "minutos_reclassificacao_3_para_2", "operador": "<", "valor": 30},
            ]
        },
        "acoes": [
            {
                "tipo": "emitir_evento",
                "evento": "evento_critico",
                "mensagem": "Paciente reclassificado de nivel 3 para 2 em menos de 30 minutos.",
            },
            {
                "tipo": "definir_fato",
                "fato": "notificar_medico_plantao",
                "valor": True,
            },
        ],
    },
    {
        "id": "E2_PIORA_MULTIPLA",
        "tipo": "segunda_ordem",
        "descricao": "Dois ou mais sinais vitais pioraram simultaneamente.",
        "quando": {
            "todos": [
                {"fato": "quantidade_sinais_pioraram", "operador": ">=", "valor": 2},
                {"fato": "e2_aplicada_na_leitura", "operador": "!=", "valor": True},
            ]
        },
        "acoes": [
            {
                "tipo": "elevar_prioridade",
                "niveis": 1,
                "motivo": "E2: piora simultanea de dois ou mais sinais vitais.",
            },
            {
                "tipo": "definir_fato",
                "fato": "agendar_nova_leitura_minutos",
                "valor": 5,
            },
            {
                "tipo": "definir_fato",
                "fato": "e2_aplicada_na_leitura",
                "valor": True,
            },
        ],
    },
    {
        "id": "E3_SLA_VIOLADO",
        "tipo": "segunda_ordem",
        "descricao": "Paciente aguardando alem do SLA do nivel atual.",
        "quando": {
            "todos": [
                {"fato": "minutos_espera", "operador": ">", "fato_direita": "minutos_sla"},
                {"fato": "alerta_sla_emitido_nesta_leitura", "operador": "!=", "valor": True},
            ]
        },
        "acoes": [
            {
                "tipo": "emitir_evento",
                "evento": "violacao_sla",
                "mensagem": "Paciente excedeu o SLA do nivel atual e foi escalado para supervisor.",
            },
            {
                "tipo": "incrementar_contador",
                "contador": "quantidade_violacoes_sla",
                "passo": 1,
            },
            {
                "tipo": "definir_fato",
                "fato": "escalar_supervisor",
                "valor": True,
            },
            {
                "tipo": "definir_fato",
                "fato": "alerta_sla_emitido_nesta_leitura",
                "valor": True,
            },
        ],
    },
    {
        "id": "E4_VULNERAVEL_FEBRE_SUBIDA",
        "tipo": "segunda_ordem",
        "descricao": "Paciente vulneravel com aumento de temperatura acima de 1C.",
        "quando": {
            "todos": [
                {"fato": "vulneravel", "operador": "==", "valor": True},
                {"fato": "delta_temperatura", "operador": ">", "valor": 1.0},
                {"fato": "e4_aplicada", "operador": "!=", "valor": True},
            ]
        },
        "acoes": [
            {
                "tipo": "definir_prioridade",
                "nivel": 2,
                "motivo": "E4: vulneravel com aumento de temperatura > 1C.",
            },
            {
                "tipo": "definir_fato",
                "fato": "e4_aplicada",
                "valor": True,
            },
        ],
    },
    {
        "id": "E5_DUPLA_VIOLACAO_SLA",
        "tipo": "segunda_ordem",
        "descricao": "Duas violacoes de SLA para o mesmo paciente.",
        "quando": {
            "todos": [
                {"fato": "quantidade_violacoes_sla", "operador": ">=", "valor": 2},
                {"fato": "e5_aplicada", "operador": "!=", "valor": True},
            ]
        },
        "acoes": [
            {
                "tipo": "emitir_evento",
                "evento": "sobrecarga",
                "mensagem": "Duas violacoes de SLA no mesmo paciente. Bloquear novas admissoes.",
            },
            {
                "tipo": "definir_fato",
                "fato": "bloquear_novas_admissoes",
                "valor": True,
            },
            {
                "tipo": "definir_fato",
                "fato": "acionar_protocolo_sobrecarga",
                "valor": True,
            },
            {
                "tipo": "definir_fato",
                "fato": "e5_aplicada",
                "valor": True,
            },
        ],
    },
]
