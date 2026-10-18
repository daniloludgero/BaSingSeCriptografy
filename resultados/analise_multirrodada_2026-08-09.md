# Análise diferencial concreta multirrodada — 2026-08-09

## Escopo

Foram enumeradas exaustivamente as quatro entradas que realizam a transição
DDT máxima `1 -> 1` na primeira S-box: `0`, `1`, `0x015e` e `0x015f`.

As demais 31 palavras da entrada foram fixadas em zero antes do whitening. A
chave foi fixada em 32 bytes `a5` e a sessão em `7`. Cada par foi executado
pela implementação real, incluindo chaves, constantes, inversões e MDS.

## Segunda rodada

Para todas as quatro testemunhas:

- 32 palavras estavam ativas na entrada da segunda S-box;
- nenhuma das 32 transições tinha contagem DDT 4;
- todas tinham contagem DDT 2;
- a saída da segunda MDS permaneceu com 32 palavras ativas;
- o peso da característica de duas rodadas foi `2^-494`.

As quatro testemunhas formaram duas classes distintas de diferença após a
segunda camada de S-box.

Uma CNF com 37.312 variáveis e 129.152 cláusulas validou uma classe:

- diferença correta da segunda camada: `SATISFIABLE`;
- mesma diferença com um bit invertido: `UNSATISFIABLE`.

## Quatro rodadas oficiais

O perfil foi idêntico para as quatro testemunhas:

| Rodada | S-boxes ativas | Transições DDT de contagem 4 | Custo em bits |
|---:|---:|---:|---:|
| 1 | 1 | 1 | 14 |
| 2 | 32 | 0 | 480 |
| 3 | 32 | 0 | 480 |
| 4 | 32 | 0 | 480 |
| **Total** | **97** | **1** | **1.454** |

Assim, cada uma dessas quatro características globalmente compatíveis tem
produto de probabilidades locais `2^-1454` e termina com 32 palavras ativas.

## Interpretação

`2^-1454` é o peso de uma característica específica, calculado pelo produto
das contagens DDT locais. Não é a probabilidade diferencial exata da cifra sob
chave fixa, porque muitas características podem contribuir para a mesma
diferença final e suas dependências não foram somadas.

O resultado é exaustivo somente para as quatro testemunhas máximas da
diferença inicial `1` com as outras palavras fixadas. Ele não prova que estas
são as melhores trilhas entre todas as diferenças e todos os estados.

## Artefatos

- `implementacao/analise_duas_rodadas.py`;
- `ferramentas/rsd_diff_round2_layer_sat.cnf`;
- `ferramentas/rsd_diff_round2_layer_unsat.cnf`.

O próximo passo é ampliar a busca para diferenças iniciais e palavras ativas
distintas, priorizando candidatos por branch-and-bound antes da confirmação
CNF.
