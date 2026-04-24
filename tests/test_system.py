import unittest

from src.rule_engine import MotorEncadeamentoProgressivo
from src.tiebreaker import escolher_proximo_paciente, ordenar_pacientes_mesmo_nivel


def criar_paciente(
    patient_id,
    hora_entrada,
    idade=30,
    gestante=False,
    deficiencia=False,
    leituras=None,
):
    return {
        "id": patient_id,
        "idade": idade,
        "gestante": gestante,
        "deficiencia": deficiencia,
        "hora_entrada": hora_entrada,
        "leituras": leituras or [],
    }


class TestSistemaEspecialista(unittest.TestCase):
    def setUp(self):
        self.motor = MotorEncadeamentoProgressivo()

    def test_progressiva_piora_para_nivel_2(self):
        p = criar_paciente(
            "PAC-A",
            "14:00",
            leituras=[
                {
                    "hora": "14:00",
                    "spo2": 95,
                    "frequencia_cardiaca": 90,
                    "temperatura": 37.0,
                    "escala_dor": 2,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
                {
                    "hora": "14:25",
                    "spo2": 89,
                    "frequencia_cardiaca": 122,
                    "temperatura": 38.6,
                    "escala_dor": 7,
                    "glasgow": 14,
                    "vomitos_por_hora": 2,
                    "pulso_presente": True,
                    "respirando": True,
                },
            ],
        )
        out = self.motor.processar_paciente(p)
        self.assertEqual(out["nivel_atual"], 1)

    def test_progressiva_piora_dispara_e2(self):
        p = criar_paciente(
            "PAC-B",
            "15:00",
            leituras=[
                {
                    "hora": "15:00",
                    "spo2": 96,
                    "frequencia_cardiaca": 80,
                    "temperatura": 37.0,
                    "escala_dor": 3,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
                {
                    "hora": "15:10",
                    "spo2": 94,
                    "frequencia_cardiaca": 120,
                    "temperatura": 38.2,
                    "escala_dor": 5,
                    "glasgow": 15,
                    "vomitos_por_hora": 1,
                    "pulso_presente": True,
                    "respirando": True,
                },
            ],
        )
        out = self.motor.processar_paciente(p)
        self.assertTrue(out["derivado"].get("agendar_nova_leitura_minutos") == 5)

    def test_regra_e4_vulneravel_temperatura(self):
        p = criar_paciente(
            "PAC-C",
            "16:00",
            idade=70,
            leituras=[
                {
                    "hora": "16:00",
                    "spo2": 95,
                    "frequencia_cardiaca": 88,
                    "temperatura": 37.0,
                    "escala_dor": 3,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
                {
                    "hora": "16:15",
                    "spo2": 95,
                    "frequencia_cardiaca": 90,
                    "temperatura": 38.2,
                    "escala_dor": 3,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
            ],
        )
        out = self.motor.processar_paciente(p)
        self.assertEqual(out["nivel_atual"], 2)

    def test_regra_e5_dupla_violacao_sla(self):
        p = criar_paciente(
            "PAC-D",
            "10:00",
            leituras=[
                {
                    "hora": "10:00",
                    "spo2": 95,
                    "frequencia_cardiaca": 90,
                    "temperatura": 37.0,
                    "escala_dor": 6,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
                {
                    "hora": "10:40",
                    "spo2": 95,
                    "frequencia_cardiaca": 90,
                    "temperatura": 37.1,
                    "escala_dor": 6,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
                {
                    "hora": "10:45",
                    "spo2": 95,
                    "frequencia_cardiaca": 90,
                    "temperatura": 37.1,
                    "escala_dor": 6,
                    "glasgow": 15,
                    "vomitos_por_hora": 0,
                    "pulso_presente": True,
                    "respirando": True,
                },
            ],
        )
        out = self.motor.processar_paciente(p)
        self.assertTrue(out["derivado"].get("bloquear_novas_admissoes"))
        self.assertTrue(out["derivado"].get("acionar_protocolo_sobrecarga"))

    def test_trata_campos_ausentes_sem_excecao(self):
        p = criar_paciente(
            "PAC-E",
            "09:00",
            leituras=[{"hora": "09:00"}, {"hora": "09:20", "escala_dor": 1}],
        )
        out = self.motor.processar_paciente(p)
        self.assertIn("nivel_atual", out)

    def test_tie_e1_mesma_hora(self):
        a = {
            "id": "A",
            "nivel_atual": 3,
            "tempo_espera_minutos": 10,
            "tempo_no_nivel_minutos": 10,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        b = {
            "id": "B",
            "nivel_atual": 3,
            "tempo_espera_minutos": 10,
            "tempo_no_nivel_minutos": 10,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        ordenados, _ = ordenar_pacientes_mesmo_nivel([b, a])
        self.assertEqual([x["id"] for x in ordenados], ["A", "B"])

    def test_tie_e2_piora_objetiva(self):
        estavel = {
            "id": "ESTAVEL",
            "nivel_atual": 3,
            "tempo_espera_minutos": 25,
            "tempo_no_nivel_minutos": 25,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        piora = {
            "id": "PIORA",
            "nivel_atual": 3,
            "tempo_espera_minutos": 5,
            "tempo_no_nivel_minutos": 5,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 2, "spo2": 92}}],
        }
        escolhido = escolher_proximo_paciente([estavel, piora])
        self.assertEqual(escolhido["id"], "PIORA")

    def test_tie_e3_vulneravel_vs_risco_objetivo(self):
        vuln = {
            "id": "VULN",
            "nivel_atual": 3,
            "tempo_espera_minutos": 28,
            "tempo_no_nivel_minutos": 28,
            "vulneravel": True,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        clinico = {
            "id": "CLIN",
            "nivel_atual": 3,
            "tempo_espera_minutos": 15,
            "tempo_no_nivel_minutos": 15,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 1, "spo2": 92}}],
        }
        escolhido = escolher_proximo_paciente([vuln, clinico])
        self.assertEqual(escolhido["id"], "CLIN")

    def test_tie_e4_iminencia_sla(self):
        p1 = {
            "id": "P1",
            "nivel_atual": 3,
            "tempo_espera_minutos": 28,
            "tempo_no_nivel_minutos": 20,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        p2 = {
            "id": "P2",
            "nivel_atual": 3,
            "tempo_espera_minutos": 28,
            "tempo_no_nivel_minutos": 21,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        escolhido = escolher_proximo_paciente([p1, p2])
        self.assertEqual(escolhido["id"], "P2")

    def test_tie_e5_entrou_no_nivel_primeiro(self):
        recem_reclass = {
            "id": "RECENTE",
            "nivel_atual": 3,
            "tempo_espera_minutos": 25,
            "tempo_no_nivel_minutos": 0,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        antigo_no_nivel = {
            "id": "ANTIGO",
            "nivel_atual": 3,
            "tempo_espera_minutos": 15,
            "tempo_no_nivel_minutos": 15,
            "vulneravel": False,
            "sla_minutos_nivel_atual": 30,
            "derivado": {},
            "historico": [{"fatos": {"quantidade_sinais_pioraram": 0, "spo2": 95}}],
        }
        escolhido = escolher_proximo_paciente([recem_reclass, antigo_no_nivel])
        self.assertEqual(escolhido["id"], "ANTIGO")


if __name__ == "__main__":
    unittest.main()
