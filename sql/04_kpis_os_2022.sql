/*
Indicadores da Silver AB04 20260928_135101_841223.
Execute no SSMS depois de SQL01 APROVADO. Cria apenas views; não altera fatos.
Grão: uma linha por formulario_os. Valores em BRL; ano 2022; local F2.
*/
USE [manutencao-fabrica-2-os-2022];
GO

IF (SELECT COUNT_BIG(*) FROM dw.fato_os) <> 337
   OR (SELECT SUM(valor_total_brl) FROM dw.fato_os) <> CONVERT(DECIMAL(18,2), 449367.51)
    THROW 51001, 'Silver esperada nao encontrada: confira SQL01 antes de criar KPIs.', 1;
GO

CREATE OR ALTER VIEW dw.vw_os_analitica AS
SELECT
    f.formulario_os,
    t.ano, t.mes_numero, t.mes_nome,
    s.setor_nome AS setor,
    y.tipo_nome AS tipo,
    p.prestador_nome_original AS prestador_solicitado,
    a.rotulo_original AS area_equipamento_original,
    f.local_original AS local,
    f.numero_controle,
    f.descricao_defeito,
    f.descricao_servico_realizado,
    f.pecas_equipamentos_necessarios,
    f.qtd, f.valor_unitario_brl, f.valor_total_brl
FROM dw.fato_os AS f
JOIN dw.dim_tempo AS t ON t.mes_chave = f.mes_chave
JOIN dw.dim_setor AS s ON s.setor_chave = f.setor_chave
JOIN dw.dim_tipo AS y ON y.tipo_chave = f.tipo_chave
JOIN dw.dim_prestador_solicitado AS p ON p.prestador_chave = f.prestador_chave
JOIN dw.dim_area_equipamento AS a ON a.area_equipamento_chave = f.area_equipamento_chave;
GO

CREATE OR ALTER VIEW dw.vw_kpis_gerais AS
WITH mediana AS (
    SELECT DISTINCT PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY valor_total_brl) OVER () AS mediana_brl
    FROM dw.fato_os
)
SELECT
    COUNT_BIG(*) AS os_registradas,
    SUM(f.valor_total_brl) AS valor_registrado_brl,
    CAST(AVG(CAST(f.valor_total_brl AS DECIMAL(19,4))) AS DECIMAL(18,2)) AS valor_medio_os_brl,
    CAST(MAX(m.mediana_brl) AS DECIMAL(18,2)) AS mediana_valor_os_brl,
    SUM(CASE WHEN y.tipo_nome = N'MANUTENÇÃO' THEN 1 ELSE 0 END) AS os_manutencao,
    SUM(CASE WHEN y.tipo_nome = N'MANUTENÇÃO' THEN f.valor_total_brl ELSE CONVERT(DECIMAL(18,2), 0) END) AS valor_manutencao_brl
FROM dw.fato_os AS f
JOIN dw.dim_tipo AS y ON y.tipo_chave = f.tipo_chave
CROSS JOIN mediana AS m;
GO

CREATE OR ALTER VIEW dw.vw_kpis_mes AS
SELECT
    t.ano, t.mes_numero, t.mes_nome,
    COUNT_BIG(*) AS os_registradas,
    SUM(f.valor_total_brl) AS valor_registrado_brl,
    CAST(AVG(CAST(f.valor_total_brl AS DECIMAL(19,4))) AS DECIMAL(18,2)) AS valor_medio_os_brl,
    SUM(CASE WHEN y.tipo_nome = N'MANUTENÇÃO' THEN 1 ELSE 0 END) AS os_manutencao,
    SUM(CASE WHEN y.tipo_nome = N'MANUTENÇÃO' THEN f.valor_total_brl ELSE CONVERT(DECIMAL(18,2), 0) END) AS valor_manutencao_brl
FROM dw.fato_os AS f
JOIN dw.dim_tempo AS t ON t.mes_chave = f.mes_chave
JOIN dw.dim_tipo AS y ON y.tipo_chave = f.tipo_chave
GROUP BY t.ano, t.mes_numero, t.mes_nome;
GO

CREATE OR ALTER VIEW dw.vw_kpis_tipo_setor AS
WITH grupos AS (
    SELECT y.tipo_nome AS tipo, s.setor_nome AS setor,
           COUNT_BIG(*) AS os_registradas,
           SUM(f.valor_total_brl) AS valor_registrado_brl
    FROM dw.fato_os AS f
    JOIN dw.dim_tipo AS y ON y.tipo_chave = f.tipo_chave
    JOIN dw.dim_setor AS s ON s.setor_chave = f.setor_chave
    GROUP BY y.tipo_nome, s.setor_nome
)
SELECT tipo, setor, os_registradas, valor_registrado_brl,
       CAST(valor_registrado_brl / CAST(os_registradas AS DECIMAL(18,2)) AS DECIMAL(18,2)) AS valor_medio_os_brl,
       CAST(100.0 * os_registradas / SUM(os_registradas) OVER () AS DECIMAL(9,2)) AS participacao_os_pct_total,
       CAST(100.0 * valor_registrado_brl / SUM(valor_registrado_brl) OVER () AS DECIMAL(9,2)) AS participacao_valor_pct_total
FROM grupos;
GO

/* Consulta de conferência: 337 O.S.; R$ 449367,51; manutenção 93 e R$ 123705,00. */
SELECT * FROM dw.vw_kpis_gerais;
SELECT ano, mes_numero, mes_nome, os_registradas, valor_registrado_brl,
       valor_medio_os_brl, os_manutencao, valor_manutencao_brl
FROM dw.vw_kpis_mes ORDER BY ano, mes_numero;
SELECT tipo, setor, os_registradas, valor_registrado_brl,
       valor_medio_os_brl, participacao_os_pct_total, participacao_valor_pct_total
FROM dw.vw_kpis_tipo_setor ORDER BY tipo, setor;
GO
