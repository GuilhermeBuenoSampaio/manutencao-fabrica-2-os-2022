USE [manutencao-fabrica-2-os-2022];
GO

SELECT CONCAT(
    formulario_os COLLATE DATABASE_DEFAULT,
    ' | mês: ', mes_numero,
    ' | equipamento: ', area_equipamento_original COLLATE DATABASE_DEFAULT,
    ' | serviço: ', descricao_servico_realizado COLLATE DATABASE_DEFAULT,
    ' | peça: ', pecas_equipamentos_necessarios COLLATE DATABASE_DEFAULT
) AS resumo_os
FROM dw.vw_manutencao_os_2022
WHERE setor = N'empanados'
  AND area_equipamento_original IN (
      N'MAQUINA COXINHA',
      N'LINHA COXINHA',
      N'MAQUINA FORMADORA COXINHA N4',
      N'MAQUINA FORMADORA COXINHA'
  )
ORDER BY area_equipamento_original, mes_numero, formulario_os;