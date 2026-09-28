# Revisão — Manutenção Fábrica 2 (O.S. 2022)

Revisão de um projeto de análise de ordens de serviço de 2022. O objetivo é reconstruir a base a partir dos formulários originais, documentar a qualidade dos dados e comparar os resultados da nova análise com as conclusões do estudo anterior. A execução analítica ocorre localmente; o projeto prevê armazenamento no Azure, versionamento do código no GitHub, modelagem em SQL Server e apresentação no Power BI com Power Query e DAX.

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

Cada execução gera JSON e Markdown em `docs/execucoes/<etapa>/<execução>/`. Os identificadores de execução e hashes SHA-256 ligam as evidências às entradas sem sobrescrever resultados anteriores. O arquivo anual anterior não é substituído automaticamente pelo anual reconstruído.

## Estado verificado em 28/09/2026

- AB01 e AB02: **337 O.S.** reconstruídas e reconciliadas com os documentos originais.
- AB03: **337 classificações**, sendo 199 de empanados, 89 de pão de queijo e 49 de geral; nenhuma divergência estrutural detectada.
- AB04: Silver Parquet aprovada na execução `20260928_013744_604732`, com **337 linhas**, **337 chaves distintas** e **R$ 449.367,51** de custo registrado. O relatório registra leitura de conferência após a gravação.
- AB00: a execução anterior apontou **340 linhas** no anual preexistente contra 337 documentos válidos da origem (12 versus 10 em maio; 64 versus 63 em julho). Esse resultado documenta uma divergência do arquivo legado e não invalida, por si, a reconciliação do anual reconstruído. A comparação e o destino do legado devem ser decididos explicitamente.
- AZ01: a primeira tentativa de provisionar o contêiner foi reprovada por falha de autenticação multifator no Azure CLI. Não há confirmação de criação do contêiner nesta documentação.

Esses números descrevem execuções identificadas; novas execuções devem ser conferidas pelos próprios relatórios, não presumidas iguais.

## Estrutura

```text
src/                  scripts das etapas e orquestrador
datalake/00_landing/  formulários originais
datalake/01_bronze_raw/ anual preexistente e tabelas mensais
datalake/02_silver/  Parquet tratado por execução
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

Na raiz do projeto, rode o orquestrador para AB00–AB04:

```powershell
python -u .\src\run_pipeline_origem.py .
```

O orquestrador cria uma nova pasta por execução e exige documentação para considerar uma etapa concluída. O status geral pode permanecer `REPROVADO` enquanto AB00 comparar o anual legado divergente, mesmo que a reconstrução e a Silver estejam aprovadas. Consulte o JSON de cada etapa para separar essas situações.

Para reproduzir isoladamente a Silver já documentada, use `gerar_silver_os.py` após uma AB03 aprovada para os mesmos bytes das planilhas. Para a configuração do Azure e os comandos de GitHub, consulte [GITHUB_E_AZURE.md](GITHUB_E_AZURE.md).

## Próximas etapas

1. Resolver e documentar o papel do anual legado frente ao anual reconstruído.
2. Provisionar e verificar o contêiner Azure; enviar arquivos autorizados e reconciliar hashes.
3. Construir a Gold e o modelo dimensional em SQL Server, com documentação por etapa.
4. Aplicar Power Query e DAX no Power BI e comparar a análise revisada à versão anterior, incluindo variáveis, tratamento de extremos, escolha de clusters e recomendações.
5. Executar o finalizador para verificar arquivos, evidências, Azure, SQL Server, Power BI e documentação antes de encerrar o projeto.

A avaliação da clusterização deve primeiro reproduzir o método original e verificar seu código e escalas reais; nenhuma mudança de conclusão é antecipada aqui.
