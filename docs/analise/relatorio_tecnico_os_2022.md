# Relatório técnico — revisão das O.S. 2022 da Fábrica 2

**Data de referência:** 28/09/2026  
**Projeto:** `manutencao-fabrica-2-os-2022`  
**Escopo:** reconstrução da origem, qualidade, Silver, Gold, Azure, SQL Server, Power BI, GitHub e encerramento.

## 1. Objetivo e delimitação

O projeto revisou a base de ordens de serviço de 2022 da Fábrica 2 a partir dos formulários originais. O objetivo técnico foi manter uma linha por O.S., tornar a classificação de setor rastreável, reconciliar valores entre as camadas e disponibilizar uma visão analítica no SQL Server e no Power BI. O objetivo analítico foi descrever volume e valor registrado por mês, tipo e setor e inspecionar a concentração das O.S. de maior valor.

Este relatório cobre **uma execução Silver específica**, `20260928_135101_841223`. Pastas de outras execuções permanecem como histórico e não são somadas à carga. O usuário informou que a execução final do orquestrador e FINAL01 ficou **APROVADA**; o JSON dessa última execução não foi fornecido para inclusão de seu `run_id` e commit neste documento. A evidência autoritativa do encerramento é `docs/execucoes/FINAL01/<run_id_da_pipeline>/conclusao_FINAL01.json` no projeto local.

## 2. Arquitetura e linhagem

| Etapa | Entrada | Saída / controle |
| --- | --- | --- |
| AB00 | Documentos originais e anual legado | Inventário e divergência histórica registrada |
| AB01 | `datalake/00_landing/` | Anual reconstruído em `quality/AB01/<run_id>/` |
| AB02 | Anual reconstruído e formulários | Reconciliação por O.S. e por campos |
| AB03 | Anual aprovado e classificação manual | Setor validado sem modificar as demais colunas |
| AB04 | Resultado AB03 | Silver `datalake/02_silver/<run_id>/os_2022_silver.parquet` |
| GO01 | Silver AB04 aprovada | Gold `datalake/03_gold/<run_id>/kpis_mes_tipo_setor.parquet` |
| AZ01/AZ02 | Contêiner e pastas locais | Provisionamento e espelhamento de `datalake/` e `quality/` no Azure; verificação de hashes |
| SQL01 | Silver aprovada e banco SQL Server | Reconciliação integral da Silver com a fato e os joins |
| GH01 | Código, SQL, docs e PBIX explícitos | Commit e envio ao GitHub; dados e evidências operacionais fora do versionamento |
| FINAL01 | Evidências e artefatos anteriores | JSON/Markdown de aprovação ou reprovação por checagem |

Ordem do `run_pipeline_projeto.py`: origem → Gold local → Azure → GitHub → finalizador. O finalizador só é chamado após aprovação das etapas anteriores. A reconciliação SQL01 é lida como evidência para a **mesma Silver**; não é uma consulta SQL nova realizada pelo finalizador. O PBIX é conferido como arquivo local e no commit; o script não recalcula medidas DAX dentro dele.

O armazenamento Azure usa a conta `stcustomeranalyticsgb01` e o contêiner `manutencao-fabrica-2-os-2022`. AZ02 inventaria `datalake/` e `quality/`, envia os caminhos correspondentes, baixa o arquivo remoto e compara SHA-256; arquivos divergentes no mesmo caminho são conflitos e não são sobrescritos. Assim, a Gold entra no mesmo fluxo de sincronização após a materialização local.

## 3. Origem, grão e qualidade

- Grão da Silver e da fato: **uma linha por `formulario_os`**. O identificador é chave natural; `numero_controle` se repete e não serve de chave substituta.
- Silver: **337 linhas**, **337 identificadores distintos**, nenhuma chave nula; **16 colunas** e nenhum nulo observado nesta versão.
- AB04: `docs/execucoes/AB04/20260928_135101_841223/conclusao_AB04.json` aprovado. SHA-256 do Parquet: `42e43d5038a8b713c519440096109c40b41dc80698cd255c825bee92097a9879`.
- Valor total: **R$ 449.367,51**. `qtd × valor_unitario_brl = valor_total_brl` nas 337 linhas observadas nesta execução; não se deve somar quantidades heterogêneas sem padronizar suas unidades.
- O anual legado apresentava **340 linhas** para **337 documentos válidos**. Essa divergência de AB00 foi preservada como pendência histórica; a reconstrução e a reconciliação AB01–AB04 seguiram seus próprios controles.
- A classificação manual de setor resultou em **199 empanados, 89 pão de queijo e 49 geral**, com cobertura das 337 O.S. A atribuição semântica depende de conhecimento operacional.

## 4. Gold e modelo SQL

GO01 agrupa a Silver aprovada por `ano`, `mes_numero`, `mes`, `tipo` e `setor`, gerando `os_registradas` e `valor_registrado_brl` em decimal. No teste com a Silver de referência, o Parquet Gold teve **61 grupos** e reconciliou **337 O.S. e R$ 449.367,51**; reexecução com a mesma fonte confirmou o conteúdo. A evidência de produção da execução aprovada está em `docs/execucoes/GO01/<run_id_da_silver>/`.

No banco SQL Server `[manutencao-fabrica-2-os-2022]`, o schema `dw` usa `dw.fato_os` no grão de uma O.S. e as dimensões `dim_tempo` (mês), `dim_setor`, `dim_tipo`, `dim_prestador_solicitado` e `dim_area_equipamento`. A fato tem PK em `formulario_os`, FKs para as dimensões, valores `DECIMAL` e restrições de valor/quantidade. `local` permanece atributo da fato porque só existe F2 nesta versão. As grafias originais de prestador e área/equipamento são preservadas.

Os scripts são `sql/01_modelo_dimensional_os_2022.sql`, `02_carregar_silver_sql_server.py`, `03_reconciliar_silver_sql_server.py` e `04_kpis_os_2022.sql`. A carga é transacional e valida o SHA da Silver; SQL01 compara contagem de linhas, chaves, soma, agregados e campos da Silver com a fato reconstruída por joins. A execução SQL01 aprovada para a fonte é condição do FINAL01. As views publicadas são `dw.vw_os_analitica`, `dw.vw_kpis_gerais`, `dw.vw_kpis_mes` e `dw.vw_kpis_tipo_setor`. A view analítica fornece ao Power BI o grão por O.S.

Gold em Parquet e o DW em SQL são **dois produtos derivados da mesma Silver**. O Parquet Gold é agregado por mês, tipo e setor; a fato SQL mantém o detalhe por O.S. para filtros e rankings. A reconciliação com a Silver evita tratar as duas materializações como fontes independentes a serem somadas.

## 5. Indicadores e reconciliação analítica

| Indicador sem filtros | Regra | Valor |
| --- | --- | ---: |
| O.S. registradas | `DISTINCTCOUNT(formulario_os)` | 337 |
| Valor registrado | `SUM(valor_total_brl)` | R$ 449.367,51 |
| Manutenção | O.S. / soma filtrada em `tipo = MANUTENÇÃO` | 93 / R$ 123.705,00 |
| Desenvolvimento | O.S. / soma filtrada em `tipo = DESENVOLVIMENTO` | 241 / R$ 321.692,51 |
| Adequação | O.S. / soma filtrada em `tipo = ADEQUAÇÃO` | 3 / R$ 3.970,00 |
| Média por O.S. | Soma / número de O.S. do recorte | R$ 1.333,43 |
| Mediana por O.S. | Percentil 50 de `valor_total_brl` | R$ 940,00 |
| Dez O.S. de maior valor | Soma das dez primeiras por valor | R$ 75.780,00; 16,86% do total |

As contagens por tipo somam 337 e os valores somam R$ 449.367,51. O Top 10 usa `formulario_os` no filtro **N superior = 10**, ordenado pela soma de `valor_total_brl` em ordem decrescente. A O.S. de maior valor é R$ 13.400,00. No Power BI, a mediana e a média são apresentadas juntas para evidenciar a assimetria sem presumir sua causa.

| Setor | O.S. | Valor registrado |
| --- | ---: | ---: |
| Empanados | 199 | R$ 260.082,51 |
| Pão de queijo | 89 | R$ 132.780,00 |
| Geral | 49 | R$ 56.505,00 |

Julho teve **63 O.S.**, o maior volume mensal. Setembro teve **R$ 79.060,00**, o maior valor mensal. O segundo semestre reúne 249 O.S. (73,89%) e R$ 339.572,51 (75,57%); apenas um ano de observação não permite concluir sazonalidade. As 68 O.S. mais altas, aproximadamente 20% dos registros, somam R$ 211.990,00 (47,18%), portanto a distribuição observada **não confirma uma regra 80/20** para valores por O.S.

## 6. Painel e documentação

O PBIX está em `powerbi/manutencao_fabrica_2_os_2022.pbix`. O painel exibe cartões por tipo, total, média e mediana, barras mensais de quantidade e valor, valores por setor, segmentação por setor e tabela Top 10. O documento `docs/analise/painel_power_bi_os_2022.md` define os cálculos e as verificações visuais; `docs/analise/EDA_Silver_OS_2022_20260928.md` contém a exploração da Silver. O PBIX versionado depende da conexão SQL Server configurada no ambiente em que for aberto.

GH01 usa uma lista explícita para código, SQL e documentos. O arquivo PBIX de `powerbi/` foi incluído explicitamente, mesmo com a pasta ignorada no `.gitignore`; `datalake/`, `quality/` e `docs/execucoes/` permanecem fora do repositório. A evidência FINAL01 aprovada informada pelo usuário fecha o conjunto de controles de origem, Gold, Azure, SQL, arquivo PBIX, documentação e commit. Os códigos e hashes exatos da execução final devem ser lidos no JSON FINAL01 correspondente.

## 7. Limites de interpretação e próximos controles

1. **Valor registrado ≠ custo operacional total.** O total inclui desenvolvimento e adequação. Não quantifica parada de produção, perda de receita, lucro ou margem.
2. **Prestador solicitado ≠ executor comprovado.** Rótulos compostos e grafias parecidas exigem validação antes de comparar fornecedores.
3. **Área/equipamento não é um cadastro de ativos.** São 179 rótulos, 119 com apenas uma ocorrência; é preciso separar área, equipamento e aliases antes de produzir indicadores por ativo.
4. **Sem exposição e tempo de reparo.** Não há base para MTBF, MTTR, disponibilidade, taxa de falha ou prioridade baseada em perda de produção.
5. **Recorte temporal e operacional estreito.** Apenas 2022 e F2, sem inferência causal ou comparação anual.
6. **Dashboard e automação têm alcances distintos.** FINAL01 confere arquivo/commit/evidência, não abre o PBIX para recalcular DAX. Na manutenção, conferir as medidas e a atualização do modelo após qualquer nova carga.
7. **README.** O exemplar do README disponível na revisão descreve AZ01 e SQL/Gold como futuras etapas; atualizá-lo para refletir a execução final e os caminhos efetivos antes da divulgação pública. Este relatório não substitui essa atualização.

## 8. Evidências de referência

- Silver e linhagem: `docs/execucoes/AB04/20260928_135101_841223/conclusao_AB04.json`.
- Gold: `docs/execucoes/GO01/20260928_135101_841223/conclusao_GO01.json` e Parquet no mesmo `run_id` sob `datalake/03_gold/`.
- Azure: evidências AZ01, AZ02 e `pipeline_azure` em `docs/execucoes/`.
- SQL: última evidência `SQL01` aprovada para `source_run = 20260928_135101_841223`.
- GitHub: evidência GH01 e commit registrados na execução final.
- Encerramento: `docs/execucoes/FINAL01/<run_id_da_pipeline>/conclusao_FINAL01.json` e `.md`.

As evidências de execução não são incluídas no GitHub; permanecem no projeto local. O status final citado foi informado pelo usuário após a execução da correção do caminho `powerbi/` e do versionamento do PBIX.
