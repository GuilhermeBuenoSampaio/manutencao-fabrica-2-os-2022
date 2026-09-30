/*
Análise 02 — casos documentados por formulário.
Execute no SSMS após 01_base_e_diagnostico.sql e a revisão dos formulários.
Esta view de leitura não altera Silver, fato, Gold nem classificações originais.
Cada vínculo foi informado/confirmado em 29/09/2026 e documentado em
docs/analise/manutencao_2022/investigacao_*.md.
As demais O.S. permanecem SEM_VINCULO_DOCUMENTADO, não "sem importância".
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF OBJECT_ID(N'dw.vw_manutencao_os_2022', N'V') IS NULL
    THROW 51210, 'Execute primeiro 01_base_e_diagnostico.sql no banco correto.', 1;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_casos_2022 AS
SELECT f.*,
       CASE
         WHEN f.formulario_os IN (N'OSM.MQ/EQ-504F2', N'OSM.MQ/EQ-622F2', N'OSM.MQ/EQ-740F2')
           THEN N'CALDEIRA_AJUSTE_NR_CONFIRMADO'
         WHEN f.formulario_os IN (N'OSM.MQ/EQ-545F2', N'OSM.MQ/EQ-546F2',
                                  N'OSM.MQ/EQ-731F2', N'OSM.MQ/EQ-732F2',
                                  N'OSM.MQ/EQ-733F2', N'OSM.MQ/EQ-821F2')
           THEN N'GONDOLA_REFORMA_CONJUNTO_CONFIRMADO'
         WHEN f.formulario_os = N'OSM.MQ/EQ-818F2'
           THEN N'CARRINHOS_CONGELAMENTO_CONJUNTO_40'
         WHEN f.formulario_os IN (N'OSM.MQ/EQ-531F2', N'OSM.MQ/EQ-738F2')
           THEN N'PICADOR_QUEIJO_QUEBRA_CONFIRMADA'
         ELSE N'SEM_VINCULO_DOCUMENTADO'
       END AS caso_documentado
FROM dw.vw_manutencao_os_2022 AS f;
GO

/* Esperado: 93 O.S. e R$ 123705,00; 12 formulários nos quatro casos. */
SELECT caso_documentado, COUNT_BIG(*) AS os_registradas,
       SUM(valor_total_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_casos_2022
GROUP BY caso_documentado
ORDER BY caso_documentado;

/* Controle: não há duplicação de O.S.; subtotais somam a população. */
SELECT COUNT_BIG(*) AS os_registradas,
       COUNT(DISTINCT formulario_os) AS formularios_distintos,
       SUM(valor_total_brl) AS valor_registrado_brl,
       SUM(CASE WHEN caso_documentado <> N'SEM_VINCULO_DOCUMENTADO' THEN 1 ELSE 0 END)
           AS os_vinculadas_a_caso
FROM dw.vw_manutencao_casos_2022;
GO
