/*
Análise 02 — manutenção de 2022. Execute no SSMS após SQL01 aprovado.
Fonte: dw.vw_os_analitica (uma linha por formulario_os).
Cria views de leitura. Não modifica dados nem a análise geral.
Referência: Silver AB04 20260928_135101_841223.
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF OBJECT_ID(N'dw.vw_os_analitica', N'V') IS NULL
    THROW 51200, 'Execute primeiro sql/04_kpis_os_2022.sql.', 1;
IF (SELECT COUNT_BIG(*) FROM dw.vw_os_analitica) <> 337
   OR (SELECT SUM(valor_total_brl) FROM dw.vw_os_analitica) <> CONVERT(DECIMAL(18,2), 449367.51)
    THROW 51201, 'A base SQL nao corresponde a Silver de referencia.', 1;
IF (SELECT COUNT_BIG(*) FROM dw.vw_os_analitica WHERE tipo = N'MANUTENÇÃO') <> 93
   OR (SELECT SUM(valor_total_brl) FROM dw.vw_os_analitica WHERE tipo = N'MANUTENÇÃO') <> CONVERT(DECIMAL(18,2), 123705.00)
    THROW 51202, 'O recorte de manutencao nao reconcilia com a EDA.', 1;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_os_2022 AS
SELECT formulario_os, ano, mes_numero, mes_nome, setor,
       area_equipamento_original, prestador_solicitado, local, numero_controle,
       descricao_defeito, descricao_servico_realizado,
       pecas_equipamentos_necessarios, qtd, valor_unitario_brl, valor_total_brl
FROM dw.vw_os_analitica
WHERE tipo = N'MANUTENÇÃO' AND ano = 2022;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_rotulo_2022 AS
SELECT setor, area_equipamento_original,
       COUNT_BIG(*) AS os_registradas,
       SUM(valor_total_brl) AS valor_registrado_brl,
       CAST(AVG(CAST(valor_total_brl AS DECIMAL(19,4))) AS DECIMAL(18,2)) AS media_os_brl,
       MAX(valor_total_brl) AS maior_os_brl,
       COUNT(DISTINCT mes_numero) AS meses_com_os
FROM dw.vw_manutencao_os_2022
GROUP BY setor, area_equipamento_original;
GO

CREATE OR ALTER VIEW dw.vw_manutencao_mes_setor_2022 AS
SELECT ano, mes_numero, mes_nome, setor,
       COUNT_BIG(*) AS os_registradas,
       SUM(valor_total_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_os_2022
GROUP BY ano, mes_numero, mes_nome, setor;
GO

/* 1. Reconciliação: esperado 93 O.S. únicas, R$ 123705,00. */
SELECT COUNT_BIG(*) AS os_registradas,
       COUNT(DISTINCT formulario_os) AS formularios_distintos,
       SUM(valor_total_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_os_2022;

/* 2. Distribuição: grupos por rótulo original, sem presumir um ativo único. */
SELECT setor, area_equipamento_original, os_registradas, valor_registrado_brl,
       media_os_brl, maior_os_brl, meses_com_os
FROM dw.vw_manutencao_rotulo_2022
ORDER BY os_registradas DESC, valor_registrado_brl DESC, setor, area_equipamento_original;

/* 3. Maiores O.S. individuais. Ler descrições antes de propor causas. */
SELECT TOP (20) formulario_os, setor, mes_numero, area_equipamento_original,
       valor_total_brl, descricao_defeito, descricao_servico_realizado,
       pecas_equipamentos_necessarios
FROM dw.vw_manutencao_os_2022
ORDER BY valor_total_brl DESC, formulario_os;

/* 4. Pareto por rótulo original + setor. O percentual é do valor de manutenção. */
WITH grupos AS (
    SELECT setor, area_equipamento_original, os_registradas, valor_registrado_brl
    FROM dw.vw_manutencao_rotulo_2022
)
SELECT setor, area_equipamento_original, os_registradas, valor_registrado_brl,
       CAST(100.0 * SUM(valor_registrado_brl) OVER
         (ORDER BY valor_registrado_brl DESC, setor, area_equipamento_original
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
         / SUM(valor_registrado_brl) OVER () AS DECIMAL(9,2)) AS valor_acumulado_pct
FROM grupos
ORDER BY valor_registrado_brl DESC, setor, area_equipamento_original;

/* 5. Conferir agregações independentes: cada soma deve dar R$ 123705,00. */
SELECT 'rotulo_setor' AS agrupamento, SUM(os_registradas) AS os,
       SUM(valor_registrado_brl) AS valor_brl FROM dw.vw_manutencao_rotulo_2022
UNION ALL
SELECT 'mes_setor', SUM(os_registradas), SUM(valor_registrado_brl)
FROM dw.vw_manutencao_mes_setor_2022;
GO
