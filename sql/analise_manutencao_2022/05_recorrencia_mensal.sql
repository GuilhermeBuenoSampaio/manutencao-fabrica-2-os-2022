USE [manutencao-fabrica-2-os-2022];
GO

/*
O.S. de manutenção por rótulo original e mês.
Exibe rótulos com pelo menos duas O.S. no ano.
Meses sem O.S. aparecem como zero.
Não une nomes semelhantes nem interpreta O.S. como falhas.
*/
SELECT
    setor,
    area_equipamento_original,
    COUNT_BIG(*) AS os_no_ano,
    COUNT(DISTINCT mes_numero) AS meses_com_os,
    SUM(valor_total_brl) AS valor_no_ano_brl,
    SUM(CASE WHEN mes_numero = 1  THEN 1 ELSE 0 END) AS jan,
    SUM(CASE WHEN mes_numero = 2  THEN 1 ELSE 0 END) AS fev,
    SUM(CASE WHEN mes_numero = 3  THEN 1 ELSE 0 END) AS mar,
    SUM(CASE WHEN mes_numero = 4  THEN 1 ELSE 0 END) AS abr,
    SUM(CASE WHEN mes_numero = 5  THEN 1 ELSE 0 END) AS mai,
    SUM(CASE WHEN mes_numero = 6  THEN 1 ELSE 0 END) AS jun,
    SUM(CASE WHEN mes_numero = 7  THEN 1 ELSE 0 END) AS jul,
    SUM(CASE WHEN mes_numero = 8  THEN 1 ELSE 0 END) AS ago,
    SUM(CASE WHEN mes_numero = 9 THEN 1 ELSE 0 END) AS setembro,
    SUM(CASE WHEN mes_numero = 10 THEN 1 ELSE 0 END) AS out,
    SUM(CASE WHEN mes_numero = 11 THEN 1 ELSE 0 END) AS nov,
    SUM(CASE WHEN mes_numero = 12 THEN 1 ELSE 0 END) AS dez
FROM dw.vw_manutencao_os_2022
GROUP BY setor, area_equipamento_original
HAVING COUNT_BIG(*) >= 2
ORDER BY meses_com_os DESC, os_no_ano DESC,
         valor_no_ano_brl DESC, setor, area_equipamento_original;