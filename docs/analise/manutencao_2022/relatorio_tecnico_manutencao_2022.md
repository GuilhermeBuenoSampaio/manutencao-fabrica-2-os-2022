# Relatório técnico — aprofundamento da manutenção 2022

Data de consolidação: 29/09/2026. Análise independente da EDA geral, com a mesma fonte aprovada, banco e contêiner. Não gera uma nova população de O.S.

## Escopo, fonte e granularidade

População: 93 O.S. de manutenção, 93 formulários distintos, R$ 123.705,00 registrados. Fonte: Silver AB04 `20260928_135101_841223`, fato `dw.fato_os` e views de leitura. O valor representa o registro da O.S.; não equivale ao custo completo de operação ou parada.

A Gold da EDA agrega mês, tipo e setor. O aprofundamento utiliza o detalhe do DW porque as descrições, peças e formulários são necessários para a investigação. Não se soma Silver de execuções distintas e não se recria Bronze/Silver/Gold na publicação.

Consultas em `sql/analise_manutencao_2022/`: 01 diagnóstico; 02 caldeira; 03 gôndolas; 04 mês/setor; 05 recorrência mensal; 06 linha de coxinha; 07 picador; 08 casos documentados; 09 rótulos com registro único; 10 embaladoras; 11 natureza das intervenções; 12 KPIs. Os nomes existentes dos arquivos são preservados, inclusive `03_investigacao_gondulas.sql` e `07_investigacao_investigacao_picador_queijo.sql`.

Views utilizadas: `dw.vw_manutencao_os_2022`, `dw.vw_manutencao_casos_2022` e `dw.vw_manutencao_natureza_2022`. A view de KPIs agregados inclui linha total e serve à conferência SQL; a tabela detalhada alimenta o painel, evitando somar total e subtotais.

## Método e reconciliação

Foram usados COUNT/DISTINCT, SUM, médias, máximos, agrupamentos por setor/rótulo/mês, matriz mensal, concentração acumulada e leitura individual das descrições. As saídas SQL e os indicadores Power BI foram conferidos pelo responsável durante a execução. Essa conferência é manual; a pipeline de publicação não executa SQL nem recalcula DAX.

| Setor | O.S. | Valor registrado |
|---|---:|---:|
| Empanados | 53 | R$ 63.190,00 |
| Pão de queijo | 27 | R$ 43.730,00 |
| Geral | 13 | R$ 16.785,00 |
| Total | 93 | R$ 123.705,00 |

Os agrupamentos por rótulo/setor e mês/setor reconciliaram 93 O.S. e R$ 123.705,00. O maior rótulo reúne 10,02% do valor; os três maiores, 21,40%; alcançar 80% exige 33 combinações de setor/rótulo. Não foi imposto um padrão 80/20. A distribuição contextualiza a dispersão, sem tratar cada rótulo como ativo único.

## Recorrência e contexto operacional

CALDEIRA ORBITAL registra 6 O.S. em 4 meses; MAQUINA COXINHA, 4 em 3 meses. Outros rótulos com várias O.S. em um só mês podem representar partes de uma mesma intervenção. Variações de nome não são fundidas automaticamente.

A transferência da linha de empanados da F1 para a F2 em 2022 contextualiza ajustes e reparos. Ela não demonstra a causa de cada intervenção. A linha de pão de queijo é comercialmente relevante, tem equipamentos em geral mais antigos e embaladoras sensíveis, conforme relato operacional.

Construção e montagem podem ser fabricação interna de peças de reposição. Não se inferiu desenvolvimento ou prevenção apenas pelo vocabulário. A experiência de fabricar inox por menor preço que uma peça comprada é uma hipótese para estudo fabricar versus comprar, sem economia quantificada nesta base.

## Casos documentados

| Caso | O.S. | Valor |
|---|---:|---:|
| Ajustes NR da caldeira confirmados | 3 | R$ 2.430,00 |
| Conjunto de 40 carrinhos de congelamento | 1 | R$ 12.400,00 |
| Reforma do mesmo conjunto de gôndolas | 6 | R$ 12.780,00 |
| Quebras do picador de queijo | 2 | R$ 1.130,00 |
| Total vinculado | 12 | R$ 28.740,00 |
| Sem vínculo documentado | 81 | R$ 94.965,00 |

Os ajustes NR confirmados correspondem a 504F2, 622F2 e 740F2; isso não atesta conformidade normativa. O valor dos carrinhos cobre 40 unidades, não um único ativo. As gôndolas foram reformadas para reutilização e ampliação da capacidade de armazenamento. O picador apresentou duas quebras confirmadas; o recurso manual é mais lento, segundo relato operacional.

## Natureza parcial das intervenções

| Natureza avaliada | O.S. | Valor |
|---|---:|---:|
| Corretiva confirmada | 9 | R$ 20.030,00 |
| Preventiva confirmada | 4 | R$ 4.800,00 |
| Preventiva provável, não confirmada | 1 | R$ 1.650,00 |
| Não avaliada | 79 | R$ 97.225,00 |
| Total | 93 | R$ 123.705,00 |

A avaliação operacional está detalhada em [natureza e criticidade](natureza_e_criticidade_intervencoes.md). Confirmadas: 13/93 = 13,98%; corretivas sobre toda a população: 9/93 = 9,68%; preventivas: 4/93 = 4,30%; não avaliadas: 79/93 = 84,95%. A provável representa 1/93 = 1,08% e não integra as confirmadas.

Entre as 13 confirmadas, 69,23% são corretivas. É um subconjunto selecionado; não estima a taxa corretiva da operação. No pão de queijo, 7 corretivas e 2 preventivas foram confirmadas; em empanados, 2 e 2. Geral não tem natureza confirmada. Ausência de classificação não significa ausência de falha.

## Power BI e DAX

PBIX: `powerbi/bi_analise_manutencao_2022/analise_manutencao_2022.pbix`; página Manutenção 2022. Tabela importada: `'dw vw_manutencao_natureza_2022'`.

Medidas centrais: DISTINCTCOUNT de formulario_os; SUM de valor_total_brl; CALCULATE com filtro da natureza para contagens e valores; DIVIDE para cobertura. Os argumentos DAX usam vírgulas no ambiente do projeto. A tabela detalhada preserva uma linha por O.S.

O painel inclui cartões, tabela por setor, casos documentados, corretivas confirmadas, matriz mês/setor/rótulo e segmentação por setor. O mês não é somado. O filtro que exclui SEM_VINCULO_DOCUMENTADO atua somente no visual de casos: 12 O.S./R$ 28.740,00. O detalhe de corretivas: 9/R$ 20.030,00. Cartões gerais: 93/R$ 123.705,00. Totais e filtros foram confirmados pelo responsável.

## Publicação independente e governança

`run_pipeline_manutencao_2022.py` seleciona somente documentos desta análise, SQL específico, PBIX, README compartilhado e scripts necessários à publicação. Primeiro inventaria e registra SHA-256; depois envia ao mesmo contêiner em `analises/analise_manutencao_2022/<run_id>/`, baixa e compara bytes; publica lista explícita no GitHub, sem force; por último chama `finalizar_manutencao_2022.py`.

A pipeline da EDA não chama esta pipeline. A sincronização GitHub da EDA mantém lista explícita; o inventário Azure exclui diretórios exclusivos deste aprofundamento. Nenhum dado é apagado. Cada envio cria versão própria; versões anteriores não são sobrescritas. Evidências de publicação ficam em `docs/execucoes/analise_manutencao_2022/<run_id>/`, localmente, fora do GitHub.

O finalizador revalida arquivos locais, conteúdo do commit remoto e downloads Azure. Não abre PBIX, não confirma a validade operacional das classificações e não executa consultas no SQL Server. SIMULADO não é APROVADO. A aprovação de publicação só ocorre após execução real bem-sucedida.

## Limitações e recomendação técnica

Sem horas de parada/operação e volumes, não calcular MTBF, MTTR, disponibilidade, perda financeira ou modelo de manutenção preditiva. Recorrência mensal não é recorrência da mesma falha. Criticidade depende do efeito sobre produção, redundância e tempo de recuperação; valor e frequência isolados não a medem.

Priorizar IDs estáveis de ativos, abertura/retomada com data e hora, modalidade de intervenção, componente/causa, estoque e alternativa operacional. Para fabricar versus comprar, registrar cotações comparáveis, material, fabricação, instalação e histórico de vida útil. Não se utilizou ML nesta etapa: a base atual não fornece alvo e exposição adequados para validação preditiva.
