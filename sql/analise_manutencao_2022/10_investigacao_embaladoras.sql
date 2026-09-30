USE [manutencao-fabrica-2-os-2022];
GO

SELECT
    formulario_os,
    mes_numero,
    setor,
    area_equipamento_original,
    valor_total_brl,
    descricao_servico_realizado,
    pecas_equipamentos_necessarios
FROM dw.vw_manutencao_os_2022
WHERE setor = N'pão de queijo'
  AND area_equipamento_original COLLATE DATABASE_DEFAULT
      LIKE N'%EMBALADORA%' COLLATE DATABASE_DEFAULT
ORDER BY mes_numero, formulario_os;