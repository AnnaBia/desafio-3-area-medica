from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RegistradorAuditoria:
    entradas: List[Dict[str, Any]] = field(default_factory=list)

    def registrar(
        self,
        horario: str,
        regra_id: str,
        fatos_entrada: Dict[str, Any],
        conclusao: Dict[str, Any],
        nota: str = "",
    ) -> None:
        self.entradas.append(
            {
                "hora": horario,
                "regra": regra_id,
                "fatos_entrada": dict(fatos_entrada),
                "conclusao": dict(conclusao),
                "nota": nota,
            }
        )

    def em_linhas(self) -> List[str]:
        linhas: List[str] = []
        for item in self.entradas:
            linhas.append(
                (
                    f"[{item['hora']}] regra={item['regra']} "
                    f"entrada={item['fatos_entrada']} conclusao={item['conclusao']} nota={item['nota']}"
                )
            )
        return linhas
