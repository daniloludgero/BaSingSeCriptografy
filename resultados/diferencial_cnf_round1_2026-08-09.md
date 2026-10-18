# Consulta diferencial CNF da primeira rodada — 2026-08-09

## Objetivo

Verificar, em nível de bits, a existência de duas execuções sob a mesma chave
com diferença de entrada `1` na primeira palavra, transição diferencial máxima
na S-box ativa e diferença de saída correspondente após a MDS.

## Formulação ampla

A primeira versão duplicou duas rodadas funcionais completas:

| Métrica | Resultado |
|---|---:|
| Variáveis | 129.972 |
| Cláusulas | 495.684 |
| Palavras inativas da entrada | Fixadas em zero |
| Z3, 180 segundos | Timeout/inconclusivo |

O timeout não constitui evidência de SAT ou UNSAT. A duplicação de duas MDS e
de S-boxes sem diferença ocultou relações diferenciais simples do solver.

## Formulação diferencial compacta

Para uma rodada, a redução abaixo é exata:

- chaves e constantes iguais cancelam no XOR;
- S-boxes com diferença zero têm diferença de saída zero;
- a MDS é linear e pode atuar uma única vez diretamente na diferença;
- somente as duas inversões reais da palavra ativa precisam permanecer.

| Métrica | Resultado |
|---|---:|
| Variáveis | 46.217 |
| Cláusulas | 184.749 |
| Diferença de entrada | `0x0001` |
| Diferença máxima da S-box | `inv(1) = 1` |

Resultados do Z3 em DIMACS:

- diferença de saída correta: `SATISFIABLE`;
- mesma diferença com o bit 0 invertido: `UNSATISFIABLE`.

Isso confirma a existência global da transição máxima através da primeira
rodada e confirma que sua diferença de saída é exatamente a prevista pela
MDS. Não é ainda uma busca de duas ou quatro rodadas: na camada seguinte, os
32 valores de estado concretos voltam a importar para as inversões.

## Artefatos

- `ferramentas/rsd_diff_round1_sat.cnf`: modelo amplo inconclusivo;
- `ferramentas/rsd_diff_round1_unsat.cnf`: controle amplo inconclusivo;
- `ferramentas/rsd_diff_round1_compact_sat.cnf`: consulta compacta SAT;
- `ferramentas/rsd_diff_round1_compact_unsat.cnf`: controle compacto UNSAT.

O próximo passo é ligar a saída concreta da primeira rodada à segunda camada
de 32 inversões e empregar restrições DDT/contagem de atividade para evitar a
duplicação integral de dois estados sempre que a diferença for suficiente.
