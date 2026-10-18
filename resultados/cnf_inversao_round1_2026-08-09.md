# CNF da inversão e da primeira rodada — 2026-08-09

## Relação de inversão

Foi criada uma codificação DIMACS exata para `y = inv(x)` em GF(2^16).
A relação usa `x*y=1` quando `x` é não nulo e força `y=0` quando `x=0`.

| Métrica | Resultado |
|---|---:|
| Variáveis | 575 |
| Cláusulas | 1.962 |
| Portas AND/XOR | 542 |
| Arquivo | 28.312 bytes |

Pares corretos foram aceitos e pares com um bit errado foram rejeitados pelo
avaliador de cláusulas.

## Primeira rodada completa

A composição sob chave fixa inclui:

- estado fragmentado de 512 bits;
- whitening;
- 32 relações de inversão;
- constante da primeira rodada;
- MDS sintetizada;
- primeira chave de rodada.

Configuração reproduzível:

- chave: 32 bytes `a5`;
- sessão: `7`;
- entrada do vetor conhecido: `x=1`, `y=2`.

| Métrica | Resultado |
|---|---:|
| Variáveis | 64.986 |
| Cláusulas livres | 246.056 |
| Tamanho | 5.292.842 bytes |

## Validação SAT

O executável Z3 foi usado diretamente em modo DIMACS:

- rodada com entradas livres: `SATISFIABLE`;
- entrada e saída Python corretas fixadas: `SATISFIABLE`;
- mesma entrada com um bit da saída invertido: `UNSATISFIABLE`.

Isso confirma a fidelidade do componente para o vetor conhecido testado. Não
é uma análise de segurança: a fórmula descreve funcionalidade, não procura
ainda uma trilha diferencial entre duas execuções.

## Artefatos

- `ferramentas/gf16_inverse.cnf`;
- `ferramentas/rsd_round1_fixed.cnf`;
- `ferramentas/rsd_round1_kat_sat.cnf`;
- `ferramentas/rsd_round1_kat_unsat.cnf`.

O próximo estágio é compor duas execuções, fixar uma diferença de entrada e
formular restrições sobre a diferença de saída ou transições DDT.
