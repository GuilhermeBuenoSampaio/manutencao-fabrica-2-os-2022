# Comparação do projeto original com a revisão — O.S. Fábrica 2, 2022

Comparação realizada em 29/09/2026 (horário de São Paulo). Base documental: ZIP original enviado pelo responsável e ZIP da revisão (8), complementados pelos relatórios de manutenção preparados e pelas conferências SQL/Power BI informadas na conversa. Não é uma comparação de desempenho da fábrica entre dois anos: ambas as análises examinam 2022.

## Resultado central

O original já possuía Python, SQL, modelo dimensional, camadas Bronze/Silver/Gold, Power BI, documentos executivos e código K-Means. A evolução consiste principalmente na reconciliação da população, explicitação da granularidade, rastreabilidade por execução e interpretação operacional com limites documentados. Usar menos algoritmos nesta revisão não implica menor qualidade analítica.

A base antiga tinha 320 linhas, mas 317 formulários distintos. O relatório e a planilha de respostas apresentavam 320 como total de O.S. Na revisão, 337 linhas correspondem a 337 formulários distintos. Não se deve tratar a diferença de 17 linhas como simplesmente 17 novas O.S.: a identidade e a granularidade também foram corrigidas.

## Indicadores recalculados a partir das planilhas

| Indicador | Original | Revisão | Diferença |
|---|---:|---:|---:|
| Linhas na base consolidada | 320 | 337 | +17 |
| Formulários distintos | 317 | 337 | +20 |
| Valor total registrado | R$ 416.327,51 | R$ 449.367,51 | +R$ 33.040,00 |
| Linhas classificadas como manutenção | 95 | 93 | -2 |
| Valor de manutenção | R$ 119.745,00 | R$ 123.705,00 | +R$ 3.960,00 |
| Linhas de desenvolvimento | 222 | 241 | +19 |
| Valor de desenvolvimento | R$ 292.612,51 | R$ 321.692,51 | +R$ 29.080,00 |
| Adequação | 3; R$ 3.970,00 | 3; R$ 3.970,00 | Sem mudança |
| Maior valor mensal | Setembro; R$ 79.060,00 | Setembro; R$ 79.060,00 | Sem mudança |
| Maior quantidade mensal de linhas/O.S. | Julho; 65 linhas | Julho; 63 O.S. | -2 |

O aumento do total é de aproximadamente 7,94%, mas representa correção da representação da mesma população histórica, não crescimento real de gastos entre períodos. A manutenção teve aumento de aproximadamente 3,31% no valor representado, mesmo com menor contagem após consolidação.

## Reconciliação exata dos R$ 33.040,00

| Componente | Evidência na comparação | Diferença de valor |
|---|---|---:|
| Registros de novembro ausentes do consolidado antigo | Formulários 788F2 a 811F2, 24 registros | R$ 26.590,00 |
| O.S. 630F2 | Valor antigo R$ 2.300,00; atual R$ 8.150,00 | R$ 5.850,00 |
| Conjunto relacionado à O.S. 665F2 | Antigo: 665F2 e 829F2 somavam R$ 600,00; atual: 665F2 R$ 1.200,00 | R$ 600,00 |
| **Total reconciliado** | **26.590 + 5.850 + 600** | **R$ 33.040,00** |

Esta reconciliação descreve diferenças entre os dois consolidados. A revisão possui evidência AB04 aprovada vinculada à origem. Não foi reexecutada toda a ingestão dos documentos brutos do ZIP original nesta comparação; portanto, não se atribui a causa de cada erro a uma edição manual ou a um script específico sem prova adicional.

### Contagens e identidade dos formulários

A ponte de linhas é: **320 + 24 registros de novembro - 7 linhas consolidadas = 337**.

Sete identificadores presentes somente no antigo (825F2 a 831F2) correspondem a partes de serviços que aparecem consolidados na revisão:

| Original | Representação na revisão | Observação financeira |
|---|---|---|
| 557F2 + 825F2 | 557F2 | R$ 3.700 + R$ 3.700 = R$ 7.400 |
| 559F2 + 826F2 | 559F2 | R$ 500 + R$ 500 = R$ 1.000 |
| 602F2 + 827F2 | 602F2 | R$ 825 + R$ 825 = R$ 1.650 |
| 628F2 + 828F2 | 628F2 | R$ 840 + R$ 840 = R$ 1.680 |
| 665F2 + 829F2 | 665F2 | R$ 300 + R$ 300; revisão R$ 1.200 |
| 705F2 + 830F2 | 705F2 | R$ 250 + R$ 250 = R$ 500 |
| 756F2 + 831F2 | 756F2 | R$ 835 + R$ 835 = R$ 1.670 |

Todos os códigos abreviados têm prefixo `OSM.MQ/EQ-`. O vínculo acima decorre da correspondência de descrição, mês, equipamento e valores entre os consolidados. Ele não é justificativa para apagar qualquer O.S. real: o critério atual é o formulário validado na origem.

No antigo, três formulários apareciam duas vezes com serviços diferentes: 696F2, 750F2 e 771F2. Na revisão, os pares correspondentes aparecem como 696/697, 750/751 e 771/772, respectivamente. São correções de identidade observáveis, sem mudança financeira desses pares. Uma comparação por JOIN somente no formulário, sem tratar os repetidos, produziria falsos sinais de reclassificação ou alteração de valor.

## Diferenças técnicas

| Aspecto | Evidência original | Evidência da revisão |
|---|---|---|
| Arquitetura | Camadas e exports já existentes; fato e dimensões SQL | Estrutura reutilizada, com EDA e manutenção publicadas por pipelines distintas |
| Granularidade | Fato definido como registro/lançamento; formulário podia repetir | Uma linha por O.S.; `formulario_os` como chave primária |
| Modelo SQL | Dimensões tempo, tipo, equipamento, setor, local, prestador; hash de linha e índices | Fato com PK por formulário, dimensões e views de leitura, valores decimais, preservação de rótulos |
| Qualidade | Scripts de normalização e verificação pela combinação formulário/controle | Etapas AB00–AB04, contagens, domínio de setor, integridade e hashes entre etapas |
| Setores | EMPANADOS, PÃO DE QUEIJO, F2 e MANUTENÇÃO usados como setores | Classificação manual documentada em empanados, pão de queijo e geral |
| Execução | Runner chama módulos; Q5 pode ser pulado com exceção e continuar | Aprovações por etapa, evidências e finalizador; falha de etapa necessária reprova publicação |
| Persistência | Arquivos e exports com nomes fixos; várias versões de scripts | Pastas por execução, versões preservadas, comparação de hashes e critérios explícitos de reutilização |
| Consumo analítico | XLSX/CSV/exportações para painel; alguns XLSX exportados com dados em uma coluna textual | SQL Server e views detalhadas para DAX; conferência SQL/Power BI documentada |
| Publicação | O relatório descreve governança; o ZIP contém implementações e versões | Scripts explícitos Azure/GitHub, lista de arquivos e verificação final de publicação |
| Documentação | Executivo e apresentação com afirmações estratégicas fortes | Técnico, executivo, contexto por caso, incerteza e limite de cada aprovação |

Nos XLSX antigos de fato/KPIs inspecionados, cabeçalho e linhas CSV estavam em uma única coluna. O script `unificado_v3_analysis.py` tenta reconstruir colunas por split de vírgulas. Esse procedimento é frágil se descrições contiverem vírgulas; a existência desse risco não prova, por si só, que todos os resultados antigos estejam errados.

A revisão não elimina a necessidade de contexto humano: setor e natureza dependem de validação operacional. A aprovação do finalizador confirma publicação e integridade de arquivos; não recalcula o PBIX nem executa automaticamente todas as consultas de manutenção.

## Mudança na interpretação dos resultados

| Tema | Original | Revisão e implicação |
|---|---|---|
| Maior gasto versus maior risco | Score chamado criticidade, com frequência, valor e ticket | Esses dados mostram perfil financeiro e recorrência de registros; criticidade requer efeito na produção, redundância e recuperação |
| Carrinhos | Maior score, uma linha e R$ 12.400 | Uma O.S. atende 40 carrinhos; não significa um ativo com custo unitário de R$ 12.400 |
| Gôndolas | Aparecem entre equipamentos críticos | Seis O.S./R$ 12.780 do mesmo conjunto reformado para reutilização e capacidade de depósito |
| Caldeira | Frequência usada na priorização | Três ajustes NR confirmados, além de outros serviços; recorrência não comprova repetição da mesma falha |
| Empanados | Projetos e complexidade destacados | Transferência F1–F2 contextualiza montagem, ajuste e reparo; não atribui causa automaticamente a cada O.S. |
| Pão de queijo | Perfil descrito como mais estável | Linha comercialmente importante, equipamentos mais antigos e embaladoras sensíveis segundo relato; estabilidade não foi medida por disponibilidade |
| Picador de queijo | Não é destaque na lista executiva antiga de críticos | Duas quebras/R$ 1.130, com relevância operacional apesar de valor baixo; recurso manual reduz ritmo conforme relato |
| Construção/montagem | Associação forte entre desenvolvimento e projeto | Pode ser fabricação interna de reposição corretiva; avaliar contexto antes de inferir natureza |
| Concentração | Ranking/Pareto presentes | Maior rótulo 10,02%; três maiores 21,40%; sem impor regra 80/20 |
| Natureza da manutenção | Separação manutenção/desenvolvimento/adequação | Classificação adicional: 9 corretivas, 4 preventivas, 1 provável, 79 não avaliadas; cobertura confirmada de 13,98% |

A conclusão geral de que desenvolvimento predomina no valor anual permanece: R$ 292.612,51 no antigo e R$ 321.692,51 na revisão. Setembro continua sendo o mês de maior valor. O que mudou foi a precisão da população e o grau de sustentação das interpretações operacionais.

## K-Means e score de criticidade: comparação metodológica

O script antigo de clustering utiliza StandardScaler e K-Means com K=3, random_state=42 e n_init=10. As variáveis são quantidade de O.S., quantidade total, valor total, ticket médio e número de meses. Isso é uma segmentação descritiva por perfil, não previsão de falha. A padronização e a semente fixa são escolhas úteis.

No script inspecionado não há seleção de K por silhouette/elbow ou teste de estabilidade. Quantidade de O.S., valor total e ticket são relacionados, e a soma de quantidades de peças diferentes pode misturar unidades sem significado comum. Rótulos livres também não são IDs estáveis de ativos. O ZIP contém código de clustering, mas não contém os arquivos de resultado `clusters_manutencao_por_equipamento`; não foi possível confirmar a execução e composição finais dos clusters.

Em outro script, o score é a soma de z-scores de frequência, valor e ticket. Esse score é calculável e auditável como um índice exploratório, mas não foi validado contra paradas, perdas ou criticidade operacional. Assim, seu nome e uso para priorização exigem cautela. A revisão não substitui esse score por outro supostamente preditivo: documenta os casos e limitações primeiro.

O ranking de peças antigo explode textos separados por vírgula/ponto e vírgula e atribui o valor completo da O.S. a cada termo. Isso representa valor de serviços associados ao termo, não custo específico daquela peça. Se uma O.S. tiver vários termos, somar os grupos pode repetir o valor. Não existe prova de taxa de desgaste ou necessidade de estoque mínimo apenas por esse ranking.

## Recomendações e limites da comparação

Preservar como mérito do original a iniciativa de separar manutenção e desenvolvimento, usar modelo dimensional e explorar perfis. Na revisão, comunicar como avanços verificáveis: reconciliação por formulário, rastreabilidade, identificação de conjuntos, contexto operacional, classificação parcial transparente e publicação independente.

Evitar afirmar redução de custo, melhoria de disponibilidade, aumento de vida útil ou superioridade de um modelo preditivo: tais resultados não foram medidos. Também não converter automaticamente o tipo da O.S. em tratamento contábil CAPEX/OPEX; esta comparação avalia classificação analítica, sem validar enquadramento contábil.

A documentação antiga sustenta afirmações como alto volume, margens reduzidas, risco elevado e perda de controle ausente sem disponibilizar as medições correspondentes nesta base. Algumas podem refletir conhecimento da operação, mas devem ser identificadas como contexto, não como resultado estatístico das O.S.

## Fontes internas verificadas

Original:
- `datalake/02_silver/PROJ_01_OS_BATISTA_M&E/B-OS_2022_normalizado.xlsx`, aba 2022: 320 linhas e 317 formulários distintos.
- `datalake/03_gold_exports/PROJ_01_OS_BATISTA_M&E/power_bi/PROJ_01_OS_Fabrica2_respostas_v3.xlsx`: resumo, temporal, score e setores.
- Relatório executivo DOCX e apresentação PDF em `projetos/PROJ_01_OS_BATISTA_M&E/docs/`.
- Código `cluster_manutencao_por_equipamento.py`, `unificado_v3_analysis.py`, `run_all.py` e modelo/carga SQL v2.

Revisão:
- `quality/AB01/20260928_135101_841223/A-OS_2022_gerado.xlsx`: comparação de formulários, tipos, valores e meses.
- Evidências AB03/AB04 desse run, incluindo 337/337, R$ 449.367,51 e vínculo de hashes até a Silver.
- Modelo SQL, consultas específicas, relatórios da manutenção e conferências SQL/Power BI informadas pelo responsável.

O ZIP (8) antecede a publicação final da manutenção. A aprovação posterior foi informada pelo responsável, não auditada novamente contra serviços remotos nesta comparação. O conteúdo interno dos PBIX não foi recalculado. A comparação descreve os artefatos enviados; não confirma que sejam exatamente a versão executada há um ano. Existem inclusive subpastas históricas no original, portanto foram usados os consolidados e a apresentação que concordam em 320/R$ 416.327,51.
