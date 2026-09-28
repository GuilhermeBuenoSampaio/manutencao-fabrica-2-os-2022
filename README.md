# Revisão — Manutenção Fábrica 2 (O.S. 2022)

Revisão de um projeto de análise de ordens de serviço de 2022. O objetivo é reconstruir a base a partir dos formulários originais, documentar a qualidade dos dados e comparar os resultados da nova análise com as conclusões do estudo anterior. A execução analítica ocorre localmente; `datalake/` e `quality/` são sincronizados com o Azure, e o código e a documentação pública são versionados no GitHub. A modelagem em SQL Server e a apresentação no Power BI com Power Query e DAX fazem parte da próxima fase.

## Perguntas de negócio

- Como custos e quantidade de ordens de serviço variam por mês, equipamento, prestador, tipo e setor?
- Quais gastos correspondem a manutenção, desenvolvimento e adequação?
- As recomendações da análise anterior permanecem quando a origem e a clusterização são revisadas?

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
| AZ01 | Conta de armazenamento e contêiner configurados | Verificação do contêiner `manutencao-fabrica-2-os-2022` |
| AZ02 | Pastas locais `datalake/` e `quality/` | Arquivos sincronizados com o Azure e conferidos por SHA-256 |
| GH01 | Código e documentação pública | Commit e envio ao GitHub, sem versionar dados e evidências de execução |

Cada execução gera JSON e Markdown em `docs/execucoes/<etapa>/<execução>/`. Os identificadores de execução e hashes SHA-256 ligam as evidências às entradas sem sobrescrever resultados anteriores. O arquivo anual anterior não é substituído automaticamente pelo anual reconstruído.

## Estado verificado em 28/09/2026

- AB01 e AB02: **337 O.S.** reconstruídas e reconciliadas com os documentos originais.
- AB03: **337 classificações**, sendo 199 de empanados, 89 de pão de queijo e 49 de geral; nenhuma divergência estrutural detectada.
- AB04: Silver Parquet aprovada na execução `20260928_013744_604732`, com **337 linhas**, **337 chaves distintas** e **R$ 449.367,51** de valor registrado. O relatório registra leitura de conferência após a gravação. Outra execução aprovada foi preservada em pasta própria; os números de cada versão devem ser confirmados na respectiva evidência AB04.
- AB00: a execução anterior apontou **340 linhas** no anual preexistente contra 337 documentos válidos da origem (12 versus 10 em maio; 64 versus 63 em julho). Esse resultado documenta uma divergência do arquivo legado e não invalida, por si, a reconciliação do anual reconstruído. A comparação e o destino do legado devem ser decididos explicitamente.
- AZ01: após as tentativas iniciais reprovadas, a verificação do contêiner foi **aprovada**.
- AZ02: a sincronização de `datalake/` e `quality/` foi **aprovada**, com **358/358 arquivos enviados ou reutilizados e verificados** no contêiner `manutencao-fabrica-2-os-2022`, na conta `stcustomeranalyticsgb01`.
- A execução completa de `run_pipeline_projeto.py` foi informada como **aprovada**, incluindo origem, Azure e GitHub. O relatório `docs/execucoes/pipeline_projeto/<execução>/conclusao_pipeline_projeto.json` identifica as evidências de cada etapa.

Esses números descrevem execuções identificadas; novas execuções devem ser conferidas pelos próprios relatórios, não presumidas iguais.

## Estrutura

```text
src/                  scripts das etapas e orquestrador
datalake/00_landing/  formulários originais
datalake/01_bronze_raw/ anual preexistente e tabelas mensais
datalake/02_silver/  Parquet tratado por execução
datalake/03_gold/    saídas Gold locais, quando produzidas
quality/              anual reconstruído e classificação manual
docs/execucoes/       evidências JSON, Markdown e logs por etapa
sql/                  futura modelagem e cargas para SQL Server
powerbi/              futura apresentação analítica
```

Dados de origem, classificações, relatórios de execução e Parquet permanecem fora do GitHub via `.gitignore`. O repositório guarda código e documentação revisada sem registros operacionais.

## Execução local

Use Python 3.12 e instale as bibliotecas necessárias no mesmo interpretador que executará os scripts:

```powershell
python -m pip install openpyxl pyarrow
```

Na raiz do projeto, para executar apenas AB00–AB04:

```powershell
python -u .\src\run_pipeline_origem.py .
```

O orquestrador cria uma nova pasta por execução e exige documentação para considerar uma etapa concluída. AB00 registra a diferença do anual legado; o orquestrador completo a distingue da validação da base reconstruída. Consulte o JSON de cada etapa para separar essas situações.

Para executar origem, Azure e GitHub na sequência, use:

```powershell
python -u .\src\run_pipeline_projeto.py . --account-name stcustomeranalyticsgb01
```

Para reproduzir isoladamente a Silver já documentada, use `gerar_silver_os.py` após uma AB03 aprovada para os mesmos bytes das planilhas. Para a configuração do Azure e os comandos de GitHub, consulte [GITHUB_E_AZURE.md](GITHUB_E_AZURE.md).

## Próxima fase: análise exploratória e modelo dimensional

A análise usará **uma execução Silver aprovada de cada vez**. As pastas de execução preservam versões históricas do Parquet; seus registros não devem ser somados entre versões.

1. Definir as perguntas de negócio e os KPIs candidatos.
2. Explorar a Silver aprovada: esquema, tipos, nulos, categorias, distribuição mensal, valores e extremos.
3. Confirmar fórmulas, denominadores e limitações dos KPIs com base na EDA.
4. Definir a granularidade da fato e construir dimensões e cargas no SQL Server sem multiplicar O.S.
5. Reconciliar contagens e valores entre Silver, modelo dimensional e indicadores antes de publicar a análise.

### Perguntas e KPIs candidatos

| Pergunta | KPI candidato | Regra inicial |
| --- | --- | --- |
| Como as O.S. se distribuem ao longo de 2022? | O.S. por mês | Contagem distinta de `formulario_os` por `ano` e `mes_numero`. |
| Quais setores concentram as ocorrências? | O.S. por setor e participação percentual | Contagem distinta por `setor` dividida pelo total de O.S. da execução. |
| Quais áreas ou equipamentos demandam mais serviços? | O.S. por área/equipamento | Contagem distinta por `area_equipamento`, após conferir a consistência dos nomes. |
| Onde se concentra o valor registrado? | Valor por mês, setor e área/equipamento | Soma de `valor_total_brl` em cada agrupamento. |
| Há concentração em poucas áreas ou equipamentos? | Participação acumulada | Ordenar por contagem de O.S. ou valor e calcular o percentual acumulado, identificando a métrica usada. |
| Como variam tipos e prestadores solicitados? | O.S. e valor por tipo/prestador | Contagem distinta e soma de `valor_total_brl` por `tipo` ou `prestador_solicitado`. |

Essas fórmulas são candidatas; a EDA determinará quais indicadores são sustentados pela fonte. `valor_total_brl` é o **valor registrado na O.S.**, não o custo operacional total. A Silver não possui datas e horários confiáveis de início e fim nem o custo da parada de produção; portanto, ela não sustenta tempo médio de reparo, disponibilidade ou impacto financeiro total de uma quebra. A classificação do setor foi manual e deve ser interpretada com essa limitação.

Depois da reconciliação, serão preparados Power Query, medidas DAX e o dashboard no Power BI. A análise revisada será comparada à anterior, inclusive quanto a variáveis, extremos, clusterização e recomendações. O finalizador deverá verificar arquivos, evidências, Azure, SQL Server, Power BI e documentação antes do encerramento.

A avaliação da clusterização deve primeiro reproduzir o método original e verificar seu código e escalas reais; nenhuma mudança de conclusão é antecipada aqui.
