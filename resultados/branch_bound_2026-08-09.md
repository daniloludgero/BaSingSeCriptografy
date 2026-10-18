# Busca diferencial branch-and-bound — 2026-08-09

## Cobertura

A busca avaliou:

- todas as 32 posições de palavra;
- as 16 diferenças de um bit;
- 48 diferenças multibit pseudoaleatórias determinísticas;
- as quatro testemunhas DDT máximas de cada diferença;
- chave fixa de 32 bytes `a5` e sessão `7`;
- demais palavras da entrada fixadas em zero.

Dos 8.192 candidatos teóricos, 7.744 produziram pares dentro de `F_p`. Os
demais foram descartados pelo filtro de domínio nas palavras mais altas.

## Método

A primeira fase calcula duas rodadas por atualização incremental de uma coluna
da MDS, usando a S-box pré-calculada. Os oito melhores candidatos de cada
posição são mantidos. A segunda fase propaga os 256 finalistas pelas quatro
rodadas completas.

Essa seleção é branch-and-bound heurística: candidatos são classificados pelo
custo após duas rodadas. O feixe de oito reduz, mas não elimina, o risco de
descartar uma trilha que só se tornaria melhor depois.

## Melhor característica encontrada

| Campo | Resultado |
|---|---|
| Posição ativa | 13 |
| Diferença | `0x0001` |
| Testemunhas | `0x015e`, `0x015f` |
| Perfil ativo | `1, 32, 31, 32` |
| Custo DDT | 1.439 bits |
| Peso da característica | `2^-1439` |
| Palavras finais ativas | 32 |

Perfil detalhado:

| Rodada | Ativas | Transições de contagem 4 | Custo |
|---:|---:|---:|---:|
| 1 | 1 | 1 | 14 |
| 2 | 32 | 0 | 480 |
| 3 | 31 | 0 | 465 |
| 4 | 32 | 0 | 480 |

Ela melhora em 15 bits a classe inicial `2^-1454`, porque uma palavra se torna
inativa na terceira rodada.

Um segundo padrão de interesse foi encontrado na posição 0, diferença
`0xa2ef`: uma das 32 transições da segunda rodada conserva contagem 4, gerando
custo total `1453`.

## Limitações

- A busca não percorreu todas as 65.535 diferenças por posição.
- Apenas transições máximas foram usadas na primeira S-box.
- As demais palavras da entrada foram fixadas em zero.
- O peso é de característica; não soma trilhas convergentes.
- A melhor característica encontrada não é prova de ótimo global.

## Reprodução

```powershell
python implementacao/busca_branch_bound.py
```

O próximo passo é diversificar valores das palavras inativas e incluir
transições iniciais de contagem 2, usando limites parciais para controlar a
expansão combinatória.
