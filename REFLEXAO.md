## Reflexão sobre o critério de desempate

Pensando em uma UPA lotada, com muitos pacientes no mesmo Nível 3, nosso grupo entendeu que não bastava usar apenas ordem de chegada. O critério precisava olhar risco clínico de forma objetiva e, ao mesmo tempo, evitar que alguém fosse ignorado por muito tempo.

No sistema implementado, a ordem de desempate ficou assim: primeiro risco objetivo dinâmico (piora de sinais, queda de SpO2, alertas acumulados); depois tempo no nível atual (quem está há mais tempo no mesmo nível sobe na fila); depois tempo restante para violar SLA; em seguida vulnerabilidade como desempate residual; e, por fim, ID do paciente para garantir determinismo.

Esse desenho ajudou a manter coerência com o trabalho: não usar atributos protegidos (raça, gênero, origem ou renda), gerar decisões repetíveis para a mesma entrada e deixar log auditável em linguagem legível. Na prática, o log explica por que o paciente X ficou na frente do Y, evitando a ideia de "caixa-preta".

Onde pode falhar? O principal risco é dependência de dado atualizado. Se os sinais vitais não forem registrados com frequência, o motor pode manter uma prioridade antiga, mesmo com piora real do quadro. Outro limite aparece em cenários extremos: se muitos pacientes estiverem piorando ao mesmo tempo, o componente de risco pode dominar por longos períodos. Por isso, o fator de tempo no nível é importante para reduzir inação, e os pesos devem ser revisados com dados reais de operação.

Nos testes obrigatórios (incluindo os cinco empates, piora progressiva, E4 e E5), o critério se manteve estável e sem viés sistemático observável. A saída foi consistente e auditável, com desempate final por ID apenas quando todos os critérios clínicos relevantes ficaram equivalentes.
