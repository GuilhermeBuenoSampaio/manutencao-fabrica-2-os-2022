# Escopo — Diagnóstico aprofundado das O.S. de manutenção (2022)

**Projeto:** Manutenção Fábrica 2 — O.S. 2022  
**Análise:** 02 — manutenção, derivada da análise geral  
**Execução planejada:** 29/09/2026  
**Estado:** planejado; números além dos totais já reconciliados aguardam execução

## 1. Objetivo e decisão apoiada

Identificar quais registros, áreas ou ativos merecem investigação pela equipe de manutenção, distinguindo frequência de intervenções, criticidade para a produção, valor acumulado e casos de alto valor. A saída é uma lista curta de casos com evidências rastreáveis por `formulario_os` e perguntas operacionais para validar, não uma afirmação de causa ou economia realizada. Valor baixo da O.S. não implica baixa prioridade quando a indisponibilidade do equipamento compromete o fluxo produtivo.

O universo inicial é **93 O.S. classificadas como MANUTENÇÃO**, com **R$ 123.705,00** de valor registrado, dentro das 337 O.S. e R$ 449.367,51 da Silver AB04 `20260928_135101_841223`. As O.S. de desenvolvimento, inclusive as ligadas à implantação da linha de empanados segundo contexto operacional informado, não compõem rankings de manutenção. A relação de cada O.S. de desenvolvimento com a implantação deve ser validada nos documentos se vier a ser apresentada como achado documental.

**Contexto operacional informado em 29/09/2026:** a equipe interna de manutenção e desenvolvimento frequentemente constrói ou monta uma peça para substituir a peça defeituosa de um equipamento. Portanto, palavras como “construção”, “solda” e “montagem” **não justificam excluir ou reclassificar uma O.S. de manutenção**. Descrições resumem o serviço realizado, mesmo quando aparecem iguais em campos de defeito e serviço. Para distinguir reposição corretiva de instalação/expansão, verificar a função da intervenção no formulário e, quando necessário, confirmar com a equipe. Um caso relatado de peça feita em inox por um terço do preço da peça comprada em alumínio é exemplo de contexto; sem cotação e histórico verificáveis para a O.S. correspondente, não generalizar economia ou maior durabilidade.

## 2. Fontes e grão

| Camada | Papel nesta análise | Limite |
| --- | --- | --- |
| Silver `datalake/02_silver/20260928_135101_841223/os_2022_silver.parquet` | Fonte aprovada, uma linha por `formulario_os`; referência de reconciliação | Preservar versão e SHA da AB04; não misturar execuções |
| Gold atual `datalake/03_gold/20260928_135101_841223/kpis_mes_tipo_setor.parquet` | Conferência de totais por mês, tipo e setor | É agregada: não contém formulário, equipamento, descrição ou peças |
| SQL Server `[manutencao-fabrica-2-os-2022]`, `dw.fato_os` e `dw.vw_os_analitica` | Fonte operacional da investigação, carregada da Silver aprovada; cálculos detalhados em SQL | `area_equipamento_original` é rótulo misto de área e ativo |
| Documentos originais e evidências AB01–AB04/SQL01 | Revisar descrições, ambiguidades e rastreabilidade | Consulta pontual, preservando material original |

**Decisão de arquitetura:** a investigação não será calculada apenas da Gold agregada. Criar views específicas no SQL sobre a fato de grão O.S.; se uma Gold detalhada adicional for necessária para consumo fora do SQL, materializá-la em novo caminho e com nova evidência, sem alterar `kpis_mes_tipo_setor.parquet` nem repetir as 337 linhas como se fossem fatos novos. Reutilizar a mesma conta Azure e o contêiner `manutencao-fabrica-2-os-2022`; sincronizar novos arquivos somente após validação e pela rotina existente.

## 3. Perguntas e cálculos

1. **Recorrência:** quantas O.S. de manutenção por rótulo original de área/equipamento e por setor? Quais formulários compõem cada contagem? Não fundir rótulos semelhantes sem tabela de equivalência revisada.
2. **Concentração de valores:** por rótulo e setor, calcular soma, média, mediana, máximo e participação no total de manutenção; distinguir muitos serviços pequenos de poucas O.S. caras. Calcular Pareto acumulado apenas sobre os grupos definidos e documentar o denominador.
3. **Evolução mensal:** quantidade e valor de manutenção por mês e setor, mantendo meses sem ocorrências visíveis quando apropriado. Comparar com a análise geral sem incluir desenvolvimento no numerador de manutenção.
4. **Casos prioritários:** examinar O.S. de maior valor e grupos recorrentes; ler `descricao_defeito`, `descricao_servico_realizado` e `pecas_equipamentos_necessarios`. Registrar se a intervenção repôs ou reparou componente, instalou ativo novo, ou se a finalidade permanece desconhecida. Critérios de seleção explícitos e lista de formulários, sem atribuir causa apenas pelo verbo usado no texto.
5. **Ação operacional:** para cada caso, registrar evidência, hipótese, pergunta à manutenção, dado adicional necessário e eventual decisão após validação em campo.
   Avaliar a criticidade considerando possibilidade de operação manual, capacidade perdida, tempo de recuperação, equipamento reserva, estoque de segurança e impacto potencial em vendas e logística. Registrar esses efeitos como relatos até que volumes, tempos e pedidos afetados sejam medidos.
6. **Fabricar versus comprar:** em reposições identificáveis, investigar quando a fabricação interna de uma peça é alternativa à aquisição pronta, considerando custo total, prazo de reposição e desempenho em uso. A existência de uma O.S. com fabricação não prova que havia alternativa comercial equivalente nem economia realizada.

**Datas:** o modelo verificado expõe `ano`, `mes_numero` e `mes_nome`, não uma data completa da O.S. Só calcular dias entre intervenções se a fonte tiver datas completas, coerentes e comprovadamente ligadas à mesma entidade/ativo. Com apenas mês, analisar recorrência por mês e sequência mensal; não chamar isso de MTBF.

## 4. Tratamento de nomes e unidade de comparação

- Criar um inventário de `area_equipamento_original`, com contagem, setor, exemplos de formulários e descrição. Preservar o valor original.
- Separar rótulos que designam um **ativo identificável**, uma **área** ou são **ambíguos**. Montar tabela de equivalência versionada somente para casos confirmados; incluir justificativa, regra e responsável pela validação.
- Publicar rankings de rótulos originais e, se aprovado, rankings normalizados em separado. Não interpretar grupos de área como se fossem equipamentos individuais.
- Não usar “construção” ou “montagem” como sinônimos automáticos de desenvolvimento. Uma fabricação interna pode integrar a manutenção corretiva. Registrar separadamente finalidade da intervenção e modo de execução, com estado “não determinado” quando faltar evidência.
- `numero_controle` pode se repetir e não substitui `formulario_os` como chave. A soma de `qtd` em registros consolidados não deve ser interpretada como quantidade universal de peças.

## 5. SQL, DAX e Power BI

**SQL Server — cálculo principal:** criar scripts próprios em `sql/analise_manutencao_2022/` para (a) reconciliação do filtro `MANUTENÇÃO` com 93 e R$ 123.705,00; (b) inventário de rótulos; (c) views de O.S. de manutenção, grupos por rótulo/setor e série mensal; (d) ranking e Pareto; (e) extração dos formulários selecionados. Calcular mediana com função de janela, cuidando do grão e de duplicações em JOIN. Views não devem modificar a fato nem as views gerais. Conferir se o valor total de cada agrupamento reconstitui R$ 123.705,00.

**DAX — interação:** criar medidas explícitas para O.S. de manutenção, valor registrado, média por O.S., participação no total selecionado e classificação dos casos sob filtros do painel. Usar medidas SQL para comparar os totais sem filtro; DAX deve respeitar a semântica de filtro e não somar uma coluna de total repetida por grupo. Documentar fórmulas e a diferença entre o total global de manutenção e o total do contexto filtrado. Validar cartões e subtotais por setor contra as consultas SQL.

**Painel separado:** manter o PBIX geral intacto e criar um arquivo da análise em `powerbi/analise_manutencao_2022/diagnostico_manutencao_os_2022.pbix`, com páginas de panorama de manutenção, recorrência/valores e casos prioritários. Se a pasta `powerbi/` continuar ignorada no Git, revisar GH01 para incluir explicitamente **apenas** o novo PBIX autorizado antes de publicar; não usar `git add -f powerbi/` inteiro.

## 6. Organização e documentação

```text
docs/analise/manutencao_2022/
    README.md                         índice, objetivo, fontes e status
    contrato_e_criterios.md           filtro, grão, métricas e limites
    dicionario_rotulos.md             rótulos originais e decisões de equivalência
    resultados_e_validacao.md         consultas, reconciliação e evidências
    casos_prioritarios.md             formulários, hipóteses e perguntas de campo
    relatorio_tecnico_manutencao.md   método, consultas, resultados e limitações
    relatorio_executivo_manutencao.md síntese e prioridades condicionais
sql/analise_manutencao_2022/       scripts e views, sem alterar SQL01 original
powerbi/analise_manutencao_2022/   PBIX específico e documentação das medidas
docs/execucoes/                    evidências técnicas das rotinas existentes
```

Os documentos novos são versionáveis no mesmo repositório GitHub, respeitando `.gitignore`. Dados operacionais brutos, Parquet e evidências de execução continuam nos destinos já definidos; não copiar registros sensíveis para os relatórios públicos sem revisar o conteúdo. Criar um índice no README principal apontando para `docs/analise/manutencao_2022/README.md` **quando a análise estiver concluída**. Registrar hashes/IDs da Silver de origem, commit, data das consultas e validações no relatório técnico. A aprovação anterior FINAL01 pertence à análise geral; qualquer verificação final desta análise exige evidência própria, sem reescrever a anterior.

## 7. Critérios de aceite para encerrar em 29/09

- Filtro do SQL reproduz **93 O.S., 93 formulários distintos e R$ 123.705,00**; Power BI sem filtros mostra os mesmos totais.
- Soma dos grupos por setor, mês e rótulo reconcilia com a população definida, com tratamento explícito de valores nulos/ambíguos.
- Cada prioridade contém `formulario_os`, contexto de setor e rótulo, valor e motivo da seleção; achados de texto são separados de hipóteses operacionais.
- Consultas SQL, definições DAX, decisões de padronização e limitações estão documentadas. Os relatórios técnico e executivo não atribuem causalidade, taxa de falha, MTTR/MTBF, disponibilidade ou economia não medida.
- Arquivos novos estão em pastas separadas; links internos funcionam; eventual sincronização Azure e publicação GitHub têm resultado verificável. O encerramento da análise fica condicionado a esses resultados, não apenas à existência dos arquivos.

## 8. Ordem e limite de tempo

| Janela sugerida | Resultado mínimo |
| --- | --- |
| 0–1 h | Fixar versão Silver, conferir esquema e população de manutenção no SQL |
| 1–2 h | Inventário dos rótulos e regra para ativos/áreas ambíguos |
| 2–3,5 h | Views e consultas de recorrência, valor, mês e Pareto; reconciliação |
| 3,5–4,5 h | Revisão das O.S. selecionadas e perguntas operacionais |
| 4,5–5,5 h | Medidas DAX e painel específico, conferidos com SQL |
| 5,5–6,5 h | Relatórios, links, verificação e publicação dos documentos autorizados |

**Escopo mínimo se o tempo apertar:** consultas reconciliadas, lista rastreável de casos e relatórios. Formatação avançada do painel, fusão de nomes sem confirmação e análise de ML ficam para uma extensão explicitamente registrada.

## 9. Decisão sobre aprendizado de máquina

Não há necessidade demonstrada de ML para responder às perguntas principais: contagem, agrupamentos, distribuições, ranking, leitura dirigida e validação operacional são mais interpretáveis para 93 registros. Após a exploração, registrar se aparece uma pergunta nova que ML poderia responder, qual é a unidade de análise, o sinal disponível e como validar utilidade fora da amostra. Agrupamento automático de textos ou anomalias pode servir apenas como triagem exploratória; não substituirá identificação de ativo nem evidência de falha. Não treinar previsão de quebra sem eventos de falha confiáveis, exposição, histórico temporal e validação adequada.

## 10. Estudo complementar: fabricar versus comprar

Esta é uma **pergunta de decisão**, não uma conclusão dos dados atuais. Selecionar um subconjunto de O.S. de manutenção com peça de reposição claramente identificada e registrar, por caso:

| Evidência necessária | Uso na comparação |
| --- | --- |
| Formulário, equipamento e especificação funcional da peça | Assegurar que as alternativas resolvem a mesma necessidade |
| Material, desenho e características técnicas de cada opção | Registrar diferenças de qualidade e equivalência, por exemplo inox versus alumínio |
| Horas de trabalho, custo horário, insumos, energia, terceiros e retrabalho | Estimar custo completo da fabricação interna, não apenas material |
| Cotação datada, frete, impostos e prazo da peça pronta | Estimar custo e tempo reais de compra no momento da decisão |
| Datas de instalação, falhas posteriores e horas de operação/exposição | Comparar durabilidade somente entre peças e condições de uso comparáveis |
| Paradas e perda de produção, quando medidas | Avaliar impacto operacional separadamente do valor da O.S. |

Para alternativas tecnicamente equivalentes, calcular `diferença de custo = custo total de compra − custo total de fabricação`, informando os componentes e o período da cotação. Comparar também o prazo até a máquina voltar a operar. Só estimar custo por hora de uso ou diferença de durabilidade quando houver instalação, acompanhamento e exposição confiáveis; registros censurados ou sem falha não representam durabilidade infinita. Se dados faltarem, apresentar comparação qualitativa e campos a coletar, sem percentual de economia. O relato de uma peça em inox produzida por um terço do preço da alternativa em alumínio é **contexto operacional informado**, a ser relacionado a evidência documental antes de virar achado quantitativo.
