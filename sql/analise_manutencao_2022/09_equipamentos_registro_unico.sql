USE [manutencao-fabrica-2-os-2022];
GO

WITH rotulos_unicos AS (
    SELECT
        setor,
        area_equipamento_original
    FROM dw.vw_manutencao_os_2022
    GROUP BY setor, area_equipamento_original
    HAVING COUNT(*) = 1
)
SELECT
    os.formulario_os,
    os.mes_numero,
    os.setor,
    os.area_equipamento_original,
    os.valor_total_brl,
    os.descricao_servico_realizado,
    os.pecas_equipamentos_necessarios
FROM dw.vw_manutencao_os_2022 AS os
INNER JOIN rotulos_unicos AS unicos
    ON os.setor = unicos.setor
   AND os.area_equipamento_original = unicos.area_equipamento_original
ORDER BY
    os.valor_total_brl DESC,
    os.setor,
    os.area_equipamento_original;