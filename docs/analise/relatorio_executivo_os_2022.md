# Relatório executivo — ordens de serviço da Fábrica 2, 2022

**Período analisado:** janeiro a dezembro de 2022  
**Unidade:** Fábrica 2 (F2)  
**Base:** 337 ordens de serviço distintas, reconciliadas entre a Silver e o SQL Server.

## Visão geral

Foram registrados **R$ 449.367,51** em 337 O.S. A maior parte corresponde a **desenvolvimento**: 241 O.S. e R$ 321.692,51. **Manutenção** representa 93 O.S. e R$ 123.705,00; **adequação**, 3 O.S. e R$ 3.970,00. Portanto, o valor geral não deve ser apresentado como gasto exclusivo de manutenção.

| Indicador | Resultado |
| --- | ---: |
| O.S. registradas | 337 |
| Valor total registrado | R$ 449.367,51 |
| Valor médio por O.S. | R$ 1.333,43 |
| Valor mediano por O.S. | R$ 940,00 |
| Dez O.S. de maior valor | R$ 75.780,00 (16,86% do total) |

## Principais achados

**O volume se concentra no segundo semestre.** De julho a dezembro houve 249 O.S. (73,89% do ano) e R$ 339.572,51 (75,57% do valor). Julho registrou o maior número de ordens, **63**; setembro, o maior valor, **R$ 79.060,00**. Como só há dados de um ano, essa concentração não estabelece sazonalidade.

**Empanados é o setor com maior volume e valor absoluto.** São 199 O.S. e R$ 260.082,51, seguidos por pão de queijo (89; R$ 132.780,00) e geral (49; R$ 56.505,00). Esses totais ajudam a orientar uma revisão de solicitações por setor. Sem horas de operação e volume produzido, não permitem comparar taxa de falhas ou eficiência entre setores.

**Algumas ordens têm valor bem acima do típico.** A média de R$ 1.333,43 supera a mediana de R$ 940,00; a O.S. mais alta vale R$ 13.400,00. As dez maiores somam 16,86% do valor anual. Isso justifica inspecionar individualmente os registros de maior valor, sem classificá-los automaticamente como desperdício ou anomalia.

## Ações recomendadas

1. **Separar os tipos na gestão de despesas.** Avaliar manutenção, desenvolvimento e adequação com objetivos e orçamentos próprios. O valor total agregado oculta essas diferenças.
2. **Revisar o pico do segundo semestre.** Examinar os motivos registrados, prioridades e solicitações de julho a novembro, começando por julho (quantidade) e setembro (valor). A análise atual aponta onde investigar, não a causa.
3. **Analisar as dez O.S. de maior valor.** Conferir escopo, peças, serviços e justificativas antes de decidir se há oportunidade de negociação ou padronização.
4. **Melhorar o cadastro operacional.** Padronizar equipamentos, áreas e prestadores; registrar prestador executante, datas de abertura e conclusão, horas de operação e impacto da parada. Isso permitirá avaliar confiabilidade e resultados de manutenção de forma mais sólida.

## Confiabilidade e alcance

A base foi reconstruída a partir dos formulários e reconciliada com **337 identificadores distintos** e **R$ 449.367,51**. A classificação de setor foi conferida estruturalmente, mas é manual. O anual legado tinha 340 linhas frente aos 337 documentos válidos; sua divergência ficou documentada, sem misturar suas linhas à Silver aprovada.

O projeto dispõe de Silver, Gold agregada, cópia no Azure, modelo dimensional e views no SQL Server, painel Power BI e versionamento do código e da documentação. O usuário informou que o finalizador da pipeline foi **aprovado**. O identificador exato da execução e os resultados de cada checagem constam do JSON FINAL01 no projeto local.

O painel está salvo em `powerbi/manutencao_fabrica_2_os_2022.pbix` e permite filtrar os resultados por setor.

**Limites para decisão:** os valores representam o que foi registrado nas O.S., não o custo completo da operação nem a perda por parada. Não há dados suficientes para MTBF, MTTR, disponibilidade, taxa de falha por equipamento, efeito causal de ações ou comparação entre anos/fábricas. `prestador_solicitado` não prova quem executou o serviço. Recomendações de manutenção preventiva precisam de cadastro de ativos e dados de exposição antes de serem quantificadas.

**Fontes internas:** `docs/analise/EDA_Silver_OS_2022_20260928.md`, `docs/analise/painel_power_bi_os_2022.md`, evidência AB04 `20260928_135101_841223` e relatório técnico desta revisão.
