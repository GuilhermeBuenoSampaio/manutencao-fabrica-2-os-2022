USE [manutencao-fabrica-2-os-2022];
GO

/* O.S. e valor de manutenção por setor */
SELECT
    setor,
    SUM(os_registradas) AS os_registradas,
    SUM(valor_registrado_brl) AS valor_registrado_brl
FROM dw.vw_manutencao_mes_setor_2022
GROUP BY setor
ORDER BY valor_registrado_brl DESC;

/* Evolução mensal, mantendo os setores separados */
SELECT
    ano,
    mes_numero,
    mes_nome,
    setor,
    os_registradas,
    valor_registrado_brl
FROM dw.vw_manutencao_mes_setor_2022
ORDER BY ano, mes_numero, setor;