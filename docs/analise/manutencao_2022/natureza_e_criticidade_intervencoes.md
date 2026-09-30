# Análise 02 — Natureza e criticidade das intervenções de manutenção

**Data da avaliação operacional:** 29/09/2026. **População:** 93 O.S. de manutenção de 2022, 93 formulários distintos, R$ 123.705,00 registrados. Fonte analítica: `dw.vw_manutencao_os_2022`; classificação parcial em `dw.vw_manutencao_natureza_2022`, criada pelo script `sql/analise_manutencao_2022/11_natureza_intervencoes_confirmadas.sql` (nome adotado no projeto pelo responsável). A classificação é complementar e não modifica a fonte.

## Pergunta operacional

Quais intervenções ocorreram após uma falha e poderiam comprometer o fluxo de produção? O custo registrado da O.S. mede o serviço; não mede produção perdida, urgência ou tempo parado. Frequência por rótulo também não mede sozinha criticidade: uma O.S. única pode envolver uma máquina essencial, e rótulos distintos podem se referir ao mesmo ativo ou conjunto.

## Evidências confirmadas pelo responsável operacional

| Natureza | Formulários | Justificativa contextual |
|---|---|---|
| Corretiva | `531F2`, `738F2` | Duas quebras do picador de queijo, componente relevante para o ritmo da linha de pão de queijo. |
| Corretiva | `539F2`, `557F2`, `569F2` | Quebras envolvendo embaladoras e seus mordentes/batente. `557F2` cita N1 e N2; não há prova de parada simultânea. A identidade da “embaladora antiga” em relação a N1/N2 ainda não foi confirmada. |
| Corretiva | `764F2`, `766F2` | Intervenções em esteira/corrente da formadora e redutor de tração da empanadeira. |
| Corretiva | `780F2`, `513F2` | Intervenções na modeladora de pão de queijo e no medidor de vazão de óleo. |
| Preventiva | `506F2`, `714F2` | Intervenções nos túneis de congelamento. Não foi confirmada a identidade entre os dois rótulos. |
| Preventiva | `665F2`, `756F2` | Revisão/limpeza de painéis das fritadeiras e da masseira orbital. |
| Preventiva provável, sem confirmação | `602F2` | Memória operacional sugere prevenção, mas não permite afirmar. Excluída das contagens confirmadas. |

Todos os identificadores abreviados na tabela têm prefixo `OSM.MQ/EQ-`. A avaliação foi fornecida em conversa pelo responsável operacional, não inferida automaticamente das palavras da descrição. Construir ou montar uma peça pode ser manutenção corretiva executada com fabricação interna; “limpeza” isolada também não prova prevenção.

## Reconciliação SQL

| Classe avaliada | O.S. | Valor registrado |
|---|---:|---:|
| Corretiva confirmada | 9 | R$ 20.030,00 |
| Preventiva confirmada | 4 | R$ 4.800,00 |
| Preventiva provável, não confirmada | 1 | R$ 1.650,00 |
| Não avaliada | 79 | R$ 97.225,00 |
| **Total** | **93** | **R$ 123.705,00** |

Consultas de validação executadas no SQL Server retornaram 93 registros, 93 formulários distintos e R$ 123.705,00, com soma idêntica entre as quatro classes. Portanto, **9/93 não é a taxa de manutenção corretiva da operação**: 79 O.S. ainda não foram avaliadas quanto à natureza. “Não avaliada” não significa preventiva, corretiva ou sem importância.

## Criticidade e interpretação

- O maior problema de uma falha corretiva, segundo a avaliação operacional, é a interrupção ou redução de produção e a urgência da resposta. Esse efeito pode superar o valor direto da O.S.; não foi quantificado nesta base.
- Os equipamentos de pão de queijo são em geral mais antigos, e as embaladoras são sensíveis. A linha de pão de queijo tem grande importância comercial. A linha de coxinha é mais nova e foi transferida da F1 para a F2 em 2022, gerando ajustes de instalação. Essas informações dão contexto, mas não provam causalidade para cada O.S.
- A intervenção `818F2`, de R$ 12.400,00, atende a um conjunto de 40 carrinhos de formas para túneis de congelamento. A O.S. única não representa falha de um único carrinho. A `821F2` integra a reforma documentada do mesmo conjunto de gôndolas; não é um caso isolado.
- Nos rótulos únicos, a avaliação operacional identificou diversos pontos de maior potencial de interrupção, mas também intervenções preventivas e projetos/conjuntos. Não se deve generalizar a todos os rótulos únicos.

## Limitações e próximos dados úteis

As O.S. disponíveis não trazem confirmação consistente de início/fim da parada, horas de operação, volume planejado/realizado, sucata ou custo indireto. Sem isso, não calcular MTBF, MTTR, perdas financeiras de parada ou economia de uma estratégia preditiva. Para uma próxima coleta: ID estável de ativo, máquina substituta, modalidade da intervenção registrada na abertura, data/hora da falha e retomada, produção esperada e efetiva, peça usada e estoque. A análise atual serve para selecionar riscos e melhorar o registro, sem alegar que as 79 O.S. restantes já foram classificadas.
