# Investigação — linha e máquinas de coxinha

**Contexto operacional informado:** em 2022, a linha de empanados foi transferida da Fábrica 1 (F1) para a Fábrica 2 (F2), com instalação e necessidade de ajustes e reparos. Essa informação ajuda a interpretar a sequência temporal, sem demonstrar que cada intervenção foi causada pela transferência.

**Fonte:** saída da consulta de `dw.vw_manutencao_os_2022` compartilhada em 29/09/2026. São 10 O.S. de quatro rótulos originais. Os rótulos não foram fundidos como um único equipamento.

| Formulário | Mês | Rótulo original | Serviço e componente registrados |
| --- | ---: | --- | --- |
| `OSM.MQ/EQ-500F2` | 1 | `MAQUINA COXINHA` | Construção do eixo do rolo da esteira; eixo |
| `OSM.MQ/EQ-501F2` | 1 | `MAQUINA COXINHA` | Calibração da bucha do rotor da bomba da coxinha N4; bucha |
| `OSM.MQ/EQ-528F2` | 2 | `LINHA COXINHA` | Corte e ajuste da altura da coifa da fritadeira N2; coifa |
| `OSM.MQ/EQ-538F2` | 3 | `LINHA COXINHA` | Montagem, ajuste e soldagem da estrutura do forro de gesso; estrutura superior |
| `OSM.MQ/EQ-615F2` | 7 | `MAQUINA COXINHA` | Bucha do conjunto do eixo cortado; bucha |
| `OSM.MQ/EQ-633F2` | 7 | `MAQUINA FORMADORA COXINHA N4` | Pé da base da estrutura; pé |
| `OSM.MQ/EQ-654F2` | 8 | `MAQUINA FORMADORA COXINHA` | Construção de base de policarbonato para apoio da mandíbula |
| `OSM.MQ/EQ-669F2` | 8 | `MAQUINA COXINHA` | Ajuste/furação dos guias de rolos da placa disco; disco |
| `OSM.MQ/EQ-751F2` | 10 | `MAQUINA FORMADORA COXINHA` | Limpeza e aperto das conexões eletrônicas |
| `OSM.MQ/EQ-798F2` | 11 | `MAQUINA FORMADORA COXINHA N4` | Troca de correia, eixo e rolamento; manutenção e lubrificação da corrente |

**Leitura:** fevereiro e março exibem ajustes estruturais de coifa e forro da linha; janeiro a novembro incluem serviços em componentes mecânicos e conexões. A repetição do termo “bucha” em janeiro e julho não comprova defeito repetido da mesma peça: os textos mencionam rotor da bomba e conjunto de eixo, respectivamente. “MAQUINA COXINHA” e as formadoras podem designar equipamentos relacionados ou diferentes; confirmar identificação física antes de somar intervenções por ativo.

**Limite:** o modelo tem mês, não datas completas verificadas nem horas de operação. Não calcular intervalo exato, taxa de falha, MTBF, MTTR ou atribuição causal da transferência. Registrar valores destas 10 O.S. somente quando vinculados à mesma saída SQL ou somados de forma reconciliada; esta evidência textual não traz os valores individuais.
