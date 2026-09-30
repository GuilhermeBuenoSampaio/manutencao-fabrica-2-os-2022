/*
Análise 02 — indicadores da avaliação operacional por setor e total.
Execute depois de 10_natureza_intervencoes_confirmadas.sql.
"Participação corretiva" usa somente O.S. cuja natureza foi CONFIRMADA.
Não é a taxa de corretivas entre todas as O.S. de 2022.
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF OBJECT_ID(N'dw.vw_manutencao_natureza_2022', N'V') IS NULL
    THROW 51212, 'Execute primeiro 10_natureza_intervencoes_confirmadas.sql.', 1;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_kpis_natureza_2022 AS
WITH agregados AS (
    SELECT
        CASE WHEN GROUPING(setor) = 1 THEN N'TODOS_OS_SETORES' ELSE setor END AS setor_analise,
        COUNT_BIG(*) AS os_total,
        SUM(valor_total_brl) AS valor_total_brl,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'CORRETIVA_CONFIRMADA'
                 THEN 1 ELSE 0 END) AS os_corretivas_confirmadas,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'CORRETIVA_CONFIRMADA'
                 THEN valor_total_brl ELSE 0 END) AS valor_corretivas_brl,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'PREVENTIVA_CONFIRMADA'
                 THEN 1 ELSE 0 END) AS os_preventivas_confirmadas,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'PREVENTIVA_CONFIRMADA'
                 THEN valor_total_brl ELSE 0 END) AS valor_preventivas_brl,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'PREVENTIVA_PROVAVEL_NAO_CONFIRMADA'
                 THEN 1 ELSE 0 END) AS os_preventivas_provaveis,
        SUM(CASE WHEN natureza_intervencao_avaliada = N'NAO_AVALIADA'
                 THEN 1 ELSE 0 END) AS os_nao_avaliadas
    FROM dw.vw_manutencao_natureza_2022
    GROUP BY GROUPING SETS ((setor), ())
)
SELECT *,
       os_corretivas_confirmadas + os_preventivas_confirmadas AS os_natureza_confirmada,
       CAST(100.0 * os_corretivas_confirmadas /
            NULLIF(os_corretivas_confirmadas + os_preventivas_confirmadas, 0)
            AS decimal(6,2)) AS pct_corretivas_entre_confirmadas
FROM agregados;
GO

SELECT *
FROM dw.vw_manutencao_kpis_natureza_2022
ORDER BY CASE WHEN setor_analise = N'TODOS_OS_SETORES' THEN 1 ELSE 0 END,
         setor_analise;
GO
