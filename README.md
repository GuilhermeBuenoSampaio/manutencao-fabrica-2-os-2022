# Revisão — Manutenção Fábrica 2 (O.S. 2022)

Revisão de um projeto de análise de ordens de serviço de 2022. A base foi reconstruída a partir dos formulários originais, classificada por setor, reconciliada na Silver e na Gold, carregada em um modelo dimensional SQL Server e apresentada no Power BI. A execução analítica ocorre localmente; `datalake/` e `quality/` são sincronizados com o Azure, enquanto código, SQL, documentação pública e o PBIX são versionados no GitHub. A comparação aprofundada com as conclusões e a clusterização do estudo anterior permanece como trabalho analítico futuro.

## Perguntas de negócio

- Como o valor registrado e a quantidade de ordens de serviço variam por mês, tipo e setor?
- Quais gastos correspondem a manutenção, desenvolvimento e adequação?
- Quais O.S. concentram os maiores valores, e como os resultados revisados se comparam aos do estudo anterior?

O custo financeiro da parada de produção não consta dos formulários. Assim, o valor registrado representa os serviços e itens disponíveis na fonte e não todo o impacto operacional de uma quebra.

## Fonte, granularidade e chave

Cada documento da `00_landing` representa uma ordem de serviço. Na base anual reconstruída e na Silver, a granularidade é **uma linha por O.S.**. O campo `formulário`, armazenado como `formulario_os` na Silver, identifica cada registro e deve ser único e não nulo. Um equipamento pode ter várias O.S.; isso não é duplicação da chave. Peças e quantidades podem se repetir dentro de uma O.S. Quando houver vários itens, seu total é somado e a quantidade e o valor unitário da linha consolidada ficam vazios, pois não há um único par representativo.

A coluna `setor` foi classificada manualmente em `empanados`, `pão de queijo` ou `geral`, mantendo a mesma granularidade. A validação automática confere cobertura, unicidade e integridade da cópia; a atribuição de cada equipamento ao setor depende de conhecimento operacional.

## Fluxo de dados

| Etapa | Entrada | Saída e validação |
| --- | --- | --- |
| AB00 | Documentos mensais em `datalake/00_landing` e anual preexistente em `01_bronze_raw` | Inventário por mês, códigos repetidos e comparação com o anual anterior |
| AB01 | Documentos originais da `00_landing` | `quality/AB01/<execução>/A-OS_2022_gerado.xlsx`, uma linha por documento |
| AB02 | Anual gerado e documentos originais | Reconciliação por O.S. dos campos e valores de origem |
| AB03 | Anual gerado e classificação manual | Verificação da nova coluna `setor` e preservação das demais colunas |
| AB04 | Classificação aprovada na AB03 | `datalake/02_silver/<execução>/os_2022_silver.parquet` e documentação da Silver |
| GO01 | Silver AB04 aprovada | `datalake/03_gold/<execução Silver>/kpis_mes_tipo_setor.parquet`, agregado por mês, tipo e setor |
| AZ01 | Conta de armazenamento e contêiner configurados | Verificação do contêiner `manutencao-fabrica-2-os-2022` |
| AZ02 | Pastas locais `datalake/` e `quality/` | Arquivos sincronizados com o Azure e conferidos por SHA-256 |
| SQL01 | Silver AB04 e modelo dimensional no SQL Server | Reconciliação de linhas, valores, chaves, agregados e campos da fato |
| GH01 | Código, SQL, documentação pública e PBIX | Commit e envio ao GitHub, sem versionar Parquet, formulários e evidências de execução |
| FINAL01 | Evidências e arquivos das etapas anteriores | Conferência final e relatório de aprovação/reprovação |

Cada execução gera JSON e Markdown em `docs/execucoes/<etapa>/<execução>/`. Os identificadores de execução e hashes SHA-256 ligam as evidências às entradas sem sobrescrever resultados anteriores. O arquivo anual anterior não é substituído automaticamente pelo anual reconstruído.

## Estado verificado em 28/09/2026

- AB01 e AB02: **337 O.S.** reconstruídas e reconciliadas com os documentos originais.
- AB03: **337 classificações**, sendo 199 de empanados, 89 de pão de queijo e 49 de geral; nenhuma divergência estrutural detectada.
- AB04: a execução Silver usada pela EDA, pelo SQL e pela Gold é `20260928_135101_841223`. São **337 linhas**, **337 chaves distintas** e **R$ 449.367,51** de valor registrado; SHA-256 do Parquet: `42e43d5038a8b713c519440096109c40b41dc80698cd255c825bee92097a9879`. Outras execuções permanecem históricas e não entram nessa soma.
- AB00: a execução anterior apontou **340 linhas** no anual preexistente contra 337 documentos válidos da origem (12 versus 10 em maio; 64 versus 63 em julho). Esse resultado documenta uma divergência do arquivo legado e não invalida, por si, a reconciliação do anual reconstruído. A comparação e o destino do legado devem ser decididos explicitamente.
- AZ01: após as tentativas iniciais reprovadas, a verificação do contêiner foi **aprovada**.
- GO01: Gold agregada por mês, tipo e setor em `datalake/03_gold/20260928_135101_841223/kpis_mes_tipo_setor.parquet`, reconciliada com 337 O.S. e R$ 449.367,51.
- AZ02: a sincronização de `datalake/` (incluindo a Gold) e `quality/` foi aprovada no contêiner `manutencao-fabrica-2-os-2022`, conta `stcustomeranalyticsgb01`. O total de arquivos da execução final deve ser lido na respectiva evidência AZ02; o resultado anterior de 358 arquivos precedeu a criação da Gold.
- SQL Server: banco `[manutencao-fabrica-2-os-2022]`, fato com uma O.S. por linha, cinco dimensões e quatro views analíticas. A reconciliação Silver × SQL (SQL01) foi aprovada para a Silver indicada.
- Power BI: painel `powerbi/manutencao_fabrica_2_os_2022.pbix`, ligado à visão `dw.vw_os_analitica`; os cartões e gráficos sem filtros foram conferidos com os valores da EDA.
- GitHub e FINAL01: após corrigir o caminho `powerbi/` e incluir explicitamente o PBIX ignorado, o usuário informou que a execução completa de `run_pipeline_projeto.py` ficou **aprovada**. Os identificadores de execução e commit estão nos JSONs GH01 e FINAL01 locais, não informados neste README.

Esses números descrevem execuções identificadas; novas execuções devem ser conferidas pelos próprios relatórios, não presumidas iguais.

## Estrutura

```text
src/                  scripts das etapas e orquestrador
datalake/00_landing/  formulários originais
datalake/01_bronze_raw/ anual preexistente e tabelas mensais
datalake/02_silver/  Parquet tratado por execução
datalake/03_gold/    Gold agregada por mês, tipo e setor
quality/              anual reconstruído e classificação manual
docs/execucoes/       evidências JSON, Markdown e logs por etapa
docs/analise/         EDA e relatórios técnico e executivo
sql/                  modelo dimensional, carga, reconciliação e views
powerbi/              painel manutencao_fabrica_2_os_2022.pbix
```

Dados de origem, classificações, relatórios de execução e Parquet permanecem fora do GitHub via `.gitignore`. O repositório guarda código, SQL, documentação analítica e o PBIX explicitamente autorizado em `powerbi/`, sem incluir os dados operacionais brutos.

## Execução local

Use Python 3.12 e instale as bibliotecas necessárias no mesmo interpretador que executará os scripts:

```powershell
python -m pip install openpyxl pyarrow pyodbc
```

Na raiz do projeto, para executar apenas AB00–AB04:

```powershell
python -u .\src\run_pipeline_origem.py .
```

O orquestrador cria uma nova pasta por execução e exige documentação para considerar uma etapa concluída. AB00 registra a diferença do anual legado; o orquestrador completo a distingue da validação da base reconstruída. Consulte o JSON de cada etapa para separar essas situações.

Para executar origem, Gold, Azure, GitHub e finalização na sequência, use:

```powershell
python -u .\src\run_pipeline_projeto.py . --account-name stcustomeranalyticsgb01
```

Para reproduzir isoladamente a Silver já documentada, use `gerar_silver_os.py` após uma AB03 aprovada para os mesmos bytes das planilhas. A carga e a reconciliação no SQL Server têm scripts em `sql/`; a evidência SQL01 aprovada para a mesma Silver é requisito do finalizador. Para a configuração do Azure e os comandos de GitHub, consulte [GITHUB_E_AZURE.md](GITHUB_E_AZURE.md).

## Resultados da análise

A análise usa **uma execução Silver aprovada por vez**. As pastas de execução preservam versões históricas do Parquet; registros de versões diferentes não devem ser somados.

| Indicador sem filtros | Resultado |
| --- | ---: |
| O.S. registradas | 337 |
| Valor total registrado | R$ 449.367,51 |
| Manutenção | 93 O.S.; R$ 123.705,00 |
| Desenvolvimento | 241 O.S.; R$ 321.692,51 |
| Adequação | 3 O.S.; R$ 3.970,00 |
| Média e mediana por O.S. | R$ 1.333,43; R$ 940,00 |
| Dez O.S. de maior valor | R$ 75.780,00 (16,86% do total) |

Julho teve o maior número de O.S. (63) e setembro o maior valor registrado (R$ 79.060,00). Empanados reuniu 199 O.S. e R$ 260.082,51; pão de queijo, 89 e R$ 132.780,00; geral, 49 e R$ 56.505,00. Esses totais não são taxas de falha: faltam denominadores como horas de operação e produção por setor.

A apresentação no Power BI inclui cartões por tipo, média, mediana, séries mensais, valores por setor, segmentação e tabela das dez O.S. de maior valor. A view `dw.vw_os_analitica` mantém uma linha por O.S. As demais views são `dw.vw_kpis_gerais`, `dw.vw_kpis_mes` e `dw.vw_kpis_tipo_setor`.

## Documentação e limites

- [EDA da Silver](docs/analise/EDA_Silver_OS_2022_20260928.md)
- [Indicadores e painel Power BI](docs/analise/painel_power_bi_os_2022.md)
- [Relatório técnico](docs/analise/relatorio_tecnico_os_2022.md)
- [Relatório executivo](docs/analise/relatorio_executivo_os_2022.md)

`valor_total_brl` é o **valor registrado na O.S.**, não o custo operacional completo. `prestador_solicitado` não comprova a execução. A Silver não contém horas de operação, datas confiáveis de início e fim de reparo ou perdas por parada; não sustenta MTBF, MTTR, disponibilidade, custo de parada ou inferência causal. A classificação de setor foi manual. O campo `area_equipamento` mistura descrições de área e ativo e precisa de padronização antes de um ranking confiável de equipamentos.

A comparação detalhada das conclusões revisadas com o estudo anterior, inclusive a metodologia de clusterização original, **ainda não foi realizada** nesta revisão. É uma análise futura; nenhuma mudança de conclusão sobre clusters é antecipada.

A aprovação FINAL01 confere evidências, hashes, artefatos locais e arquivos do commit, mas **não abre o PBIX para recalcular DAX**. Para manter o painel, confira a conexão com o SQL Server e os números sem filtros após cada atualização de dados.


## Análise 02 — aprofundamento da manutenção

Análise independente da EDA geral: 93 O.S. e R$ 123.705,00. Examina recorrência mensal, distribuição de valor, casos contextualizados e natureza parcial das intervenções. Dashboard e totais conferidos pelo responsável em 29/09/2026.

- [Índice e instruções](docs/analise/manutencao_2022/README.md)
- [Relatório técnico](docs/analise/manutencao_2022/relatorio_tecnico_manutencao_2022.md)
- [Relatório executivo](docs/analise/manutencao_2022/relatorio_executivo_manutencao_2022.md)

O PBIX está em `powerbi/bi_analise_manutencao_2022/analise_manutencao_2022.pbix`. Os scripts SQL estão em `sql/analise_manutencao_2022/`. A pipeline da EDA não seleciona essas pastas. O README da raiz é compartilhado.

```powershell
python -u .\src\run_pipeline_manutencao_2022.py . --simular
python -u .\src\run_pipeline_manutencao_2022.py .
```

A publicação usa o mesmo contêiner Azure, em `analises/analise_manutencao_2022/<run_id>/`, sem sobrescrever versões. Inclui SQL, documentação, PBIX e scripts de publicação. GitHub recebe somente a lista explícita. O finalizador é acionado por último e confere arquivos, hashes e commit remoto; não executa SQL nem recalcula DAX. A evidência desta análise fica em `docs/execucoes/analise_manutencao_2022/`, separada de FINAL01.

Classificação confirmada: 13 de 93 O.S. (13,98%); 9 corretivas e 4 preventivas. Há 1 provável e 79 não avaliadas. Não inferir taxa real de falha, criticidade apenas pelo valor ou perdas de produção sem dados de parada.
