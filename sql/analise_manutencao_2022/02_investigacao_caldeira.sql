/*
Análise 02 — investigação da caldeira orbital.

Esta consulta lista O.S. candidatas ao retrofit informado pela equipe.
A presença de “caldeira” no rótulo não confirma, sozinha, que a O.S.
pertence ao retrofit. Revisar formulário e serviço antes de incluí-la.
*/

SELECT
    formulario_os,
    mes_numero,
    setor,
    area_equipamento_original,
    valor_total_brl,
    descricao_servico_realizado,
    pecas_equipamentos_necessarios
FROM dw.vw_manutencao_os_2022
WHERE setor = N'empanados'
  AND area_equipamento_original IN (
      N'CALDEIRA ORBITAL',
      N'MAQUINA CALDEIRA ORBITAL',
      N'CALDEIRA ORBITAL N1'
  )
ORDER BY mes_numero, area_equipamento_original, formulario_os;