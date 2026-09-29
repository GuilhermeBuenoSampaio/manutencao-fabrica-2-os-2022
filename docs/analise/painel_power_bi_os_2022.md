# Painel Power BI — O.S. 2022, Fábrica 2

## Escopo e fonte

O arquivo do painel é `powerbi/manutencao_fabrica_2_os_2022.pbix`, na raiz do projeto. O Power BI consulta a visão `dw.vw_os_analitica` do banco SQL Server `[manutencao-fabrica-2-os-2022]`. A carga SQL foi reconciliada com uma única execução Silver: `datalake/02_silver/20260928_135101_841223/os_2022_silver.parquet` (AB04 aprovado; SHA-256 `42e43d5038a8b713c519440096109c40b41dc80698cd255c825bee92097a9879`). Pastas Silver de outras execuções representam versões históricas e não devem ser somadas à carga atual.

Grão: uma linha por `formulario_os`; 337 linhas e 337 O.S. distintas. Ano 2022, local F2. Os números abaixo correspondem à visualização sem filtros de setor ou outros recortes.

## Indicadores conferidos

| Indicador | Definição | Resultado |
| --- | --- | ---: |
| O.S. registradas | Contagem distinta de `formulario_os` | 337 |
| Valor total registrado | Soma de `valor_total_brl` | R$ 449.367,51 |
| O.S. de manutenção | O.S. com `tipo = MANUTENÇÃO` | 93 |
| Valor de manutenção | Soma dos valores dessas O.S. | R$ 123.705,00 |
| O.S. de desenvolvimento | O.S. com `tipo = DESENVOLVIMENTO` | 241 |
| Valor de desenvolvimento | Soma dos valores dessas O.S. | R$ 321.692,51 |
| O.S. de adequação | O.S. com `tipo = ADEQUAÇÃO` | 3 |
| Valor de adequação | Soma dos valores dessas O.S. | R$ 3.970,00 |
| Valor médio por O.S. | Valor total / 337 | R$ 1.333,43 |
| Valor mediano por O.S. | Mediana de `valor_total_brl` | R$ 940,00 |
| Top 10 O.S. | Soma das 10 O.S. de maior valor | R$ 75.780,00 (16,86% do total) |

Os totais por tipo fecham em 337 O.S. e R$ 449.367,51. A tabela Top 10 usa filtro visual **N superior = 10** sobre `formulario_os`, ordenado por soma de `valor_total_brl` em ordem decrescente. A primeira O.S. vale R$ 13.400,00. Seu total de R$ 75.780,00 refere-se apenas às 10 linhas filtradas, não ao projeto inteiro.

## Leitura dos gráficos

- Julho tem o maior volume mensal: 63 O.S. Setembro tem o maior valor mensal: R$ 79.060,00. Volume e valor não atingem seus máximos no mesmo mês.
- Desenvolvimento responde por 241 das 337 O.S. e R$ 321.692,51. O indicador de R$ 449.367,51 inclui os três tipos e não deve ser apresentado como gasto apenas de manutenção.
- Empanados reúne 199 O.S. e R$ 260.082,51; pão de queijo, 89 e R$ 132.780,00; geral, 49 e R$ 56.505,00. A segmentação por setor altera o contexto dos cartões e dos gráficos.
- A média excede a mediana em R$ 393,43. Isso é compatível com uma distribuição de valores à direita; o Top 10 concentra 16,86% do montante. Esses resultados não demonstram, isoladamente, causa, anomalia ou regra de Pareto 80/20.

## Definições e limites

`valor_total_brl` é valor registrado na O.S.; não é, sem validação adicional, custo total da operação, impacto da parada ou lucro. `prestador_solicitado` registra a solicitação, não comprova a execução. A classificação de setor foi manual. `area_equipamento` mistura descrições de área e ativo e precisa de padronização antes de ser usada para ranking confiável de equipamentos.

Existe apenas um ano e uma unidade nesta Silver. O painel não permite afirmar sazonalidade nem comparar fábricas. Faltam horas de operação, datas confiáveis de início/fim do reparo e produção exposta ao risco; por isso não calcular MTBF, MTTR, disponibilidade, taxa de falha ou custo de parada a partir desta base.

## Verificação e publicação

1. Abrir o `.pbix` e atualizar os dados do SQL Server. O acesso ao servidor local depende da configuração da máquina que abre o relatório.
2. Sem filtros, conferir 337 O.S. e R$ 449.367,51; conferir 93/241/3 por tipo e a soma dos respectivos valores.
3. Conferir média R$ 1.333,43, mediana R$ 940,00 e Top 10 R$ 75.780,00. Ao aplicar o setor, verificar se os indicadores variam coerentemente com o recorte.
4. Manter este documento em `docs/analise/` e o `.pbix` em `powerbi/`. Antes de publicar no GitHub, verificar se a rotina de sincronização inclui ambos os caminhos e se o `.pbix` não contém dados ou credenciais que o projeto não pretende expor.

Referência analítica detalhada: `docs/analise/EDA_Silver_OS_2022_20260928.md`.
