# Infraestrutura e versionamento

## Silver local

Instale as dependências no mesmo Python que executa a pipeline:

```powershell
python -m pip install openpyxl pyarrow
```

Execute a etapa isolada após a aprovação local da AB03:

```powershell
python -u .\src\gerar_silver_os.py .
```

O arquivo é gravado em `datalake\02_silver\<run_id>\os_2022_silver.parquet`, e a documentação em `docs\execucoes\AB04\<run_id>\`.

## Azure ADLS Gen2

O projeto precisa da conta de armazenamento e de autenticação no Azure CLI. Depois de `az login`, execute:

```powershell
python -u .\src\provisionar_container_azure.py . --account-name NOME_DA_CONTA
```

O contêiner padrão é `manutencao-fabrica-2-os-2022`. A etapa AZ01 verifica a existência e gera documentação. Esta operação não envia os dados ao Azure; o envio e a reconciliação virão em uma etapa separada.

## GitHub

A `.gitignore` exclui dados de origem, evidências locais, artefatos gerados e arquivos de produção. Versione somente código, documentação descritiva revisada e SQL sem dados reais. Na raiz do projeto, após definir a URL de um repositório privado:

```powershell
git init
git branch -M main
git add .gitignore src sql docs/revisoes GITHUB_E_AZURE.md
git status
git commit -m "Estrutura pipeline origem silver e validacoes"
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Antes do commit, revise `git status` para confirmar que nenhum dado operacional entrou no conjunto versionado. Se o projeto já possuir Git, use `git status` e `git remote -v` e não repita `git init` ou `git remote add`.
