# Investigação da caldeira orbital — evidência parcial

**Fonte:** consulta `sql/analise_manutencao_2022/02_investigacao_caldeira.sql`, resultado compartilhado em 29/09/2026. A fonte SQL contém 12 O.S. nos rótulos `CALDEIRA ORBITAL`, `MAQUINA CALDEIRA ORBITAL` e `CALDEIRA ORBITAL N1`, totalizando R$ 9.060,00. A seleção por rótulo não equivale ao escopo confirmado do retrofit.

## O.S. identificadas como ajustes para NR

O responsável com conhecimento operacional identificou **as linhas 3, 10 e 11 da saída da consulta** como ajustes para atender à NR. A identificação abaixo usa `formulario_os`, para não depender da ordem em que uma consulta futura apresentar as linhas.

| Formulário | Mês | Serviço resumido | Valor registrado |
| --- | ---: | --- | ---: |
| `OSM.MQ/EQ-504F2` | 1 | Ajuste e polimento da proteção da caldeira orbital | R$ 470,00 |
| `OSM.MQ/EQ-622F2` | 7 | Construção de proteção de mancal e montagem | R$ 760,00 |
| `OSM.MQ/EQ-740F2` | 10 | Montagem e construção das proteções de partes quentes | R$ 1.200,00 |
| **Subtotal identificado** | | **3 O.S.** | **R$ 2.430,00** |

Esse subtotal é **1,96%** dos R$ 123.705,00 registrados nas 93 O.S. de manutenção. Não é o custo total da adequação: as outras nove O.S. da consulta (R$ 6.630,00) não foram classificadas por finalidade nesta revisão. A norma específica e eventual vínculo de `CALDEIRA ORBITAL N1` ao mesmo ativo ainda devem ser documentados; não atribuir NR com base apenas em palavras como “adequação”, “proteção” ou “montagem”.

**Regra analítica:** preservar `tipo = MANUTENÇÃO` e o valor original das 12 O.S.; marcar somente estes três formulários como `ajuste_NR_confirmado_contexto_operacional` em documentação derivada. Não alterar a Silver, a fato ou os nomes originais. O estado de classificação dos demais formulários permanece `não avaliado para NR`, não “fora da NR”.
