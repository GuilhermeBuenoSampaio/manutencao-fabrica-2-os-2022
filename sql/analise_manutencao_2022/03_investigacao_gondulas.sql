USE [manutencao-fabrica-2-os-2022];
GO

/*
Análise 02 — O.S. relacionadas a gôndolas.
Mantém os rótulos originais separados.
*/
SELECT
    formulario_os,
    mes_numero,
    setor,
    area_equipamento_original,
    valor_total_brl,
    descricao_servico_realizado,
    pecas_equipamentos_necessarios
FROM dw.vw_os_analitica
WHERE ano = 2022
  AND tipo = N'MANUTENÇÃO'
  AND setor = N'geral'
  AND area_equipamento_original IN (
      N'GONDULA',
      N'GÔNDOLA DEPÓSITO',
      N'MONTAGEM GONDOLA'
  )
ORDER BY mes_numero, area_equipamento_original, formulario_os;