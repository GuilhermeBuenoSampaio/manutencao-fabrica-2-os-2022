/*
Análise 02 — natureza das intervenções avaliadas em 29/09/2026.
Execute após 08_casos_documentados.sql. Esta view acrescenta uma avaliação
operacional a um subconjunto das 93 O.S.; não altera a classificação da fonte.
"NÃO AVALIADA" não significa preventiva nem ausência de falha.
Corretiva informa a natureza da intervenção, não comprova parada ou sua duração.
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF OBJECT_ID(N'dw.vw_manutencao_casos_2022', N'V') IS NULL
    THROW 51211, 'Execute primeiro 08_casos_documentados.sql no banco correto.', 1;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_natureza_2022 AS
SELECT c.*,
       CASE
         WHEN c.formulario_os IN (
              N'OSM.MQ/EQ-531F2', N'OSM.MQ/EQ-738F2', -- picador: quebras
              N'OSM.MQ/EQ-539F2', N'OSM.MQ/EQ-557F2', N'OSM.MQ/EQ-569F2', -- embaladoras: quebras
              N'OSM.MQ/EQ-764F2', N'OSM.MQ/EQ-766F2', -- tração: corretivas
              N'OSM.MQ/EQ-780F2', N'OSM.MQ/EQ-513F2'  -- modeladora e medidor: corretivas
         ) THEN N'CORRETIVA_CONFIRMADA'
         WHEN c.formulario_os IN (
              N'OSM.MQ/EQ-506F2', N'OSM.MQ/EQ-714F2', -- túneis
              N'OSM.MQ/EQ-665F2', N'OSM.MQ/EQ-756F2'  -- painéis
         ) THEN N'PREVENTIVA_CONFIRMADA'
         WHEN c.formulario_os = N'OSM.MQ/EQ-602F2'
           THEN N'PREVENTIVA_PROVAVEL_NAO_CONFIRMADA'
         ELSE N'NAO_AVALIADA'
       END AS natureza_intervencao_avaliada
FROM dw.vw_manutencao_casos_2022 AS c;
GO

SELECT natureza_intervencao_avaliada,
       COUNT_BIG(*) AS os_registradas,
       SUM(valor_total_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_natureza_2022
GROUP BY natureza_intervencao_avaliada
ORDER BY natureza_intervencao_avaliada;

SELECT COUNT_BIG(*) AS os_registradas,
       COUNT(DISTINCT formulario_os) AS formularios_distintos,
       SUM(valor_total_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_natureza_2022;
GO
