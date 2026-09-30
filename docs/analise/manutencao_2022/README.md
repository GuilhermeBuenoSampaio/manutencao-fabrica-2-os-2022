# Análise 02 — aprofundamento da manutenção 2022

Diagnóstico e dashboard conferidos pelo responsável em 29/09/2026. Publicação independente: consulte a evidência da pipeline para saber se o envio foi aprovado.

População: 93 O.S., 93 formulários, R$ 123.705,00. Mesma fonte aprovada, banco SQL e contêiner da EDA. O detalhe do DW sustenta os casos; a Gold agregada da EDA não possui os textos por O.S.

- [Relatório técnico](relatorio_tecnico_manutencao_2022.md)
- [Relatório executivo](relatorio_executivo_manutencao_2022.md)
- [Natureza e criticidade](natureza_e_criticidade_intervencoes.md)
- [Escopo](escopo_analise_manutencao_2022.md)

SQL em `sql/analise_manutencao_2022/`; painel em `powerbi/bi_analise_manutencao_2022/analise_manutencao_2022.pbix`. Classificação parcial: 9 corretivas, 4 preventivas, 1 preventiva provável e 79 não avaliadas. Cobertura confirmada: 13,98%.

A EDA ignora as pastas exclusivas desta análise. Execute somente a pipeline de manutenção para publicá-la:

```powershell
python -u .\src\run_pipeline_manutencao_2022.py . --simular
python -u .\src\run_pipeline_manutencao_2022.py .
```

SIMULADO apenas confere inventário e pré-condições Git. A execução real publica Azure e GitHub e aciona o finalizador como última etapa. Nenhuma delas executa SQL nem recalcula o PBIX. Evidências locais: `docs/execucoes/analise_manutencao_2022/<run_id>/`.
