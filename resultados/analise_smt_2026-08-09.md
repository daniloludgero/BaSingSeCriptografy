# Análise algébrica e SMT — 2026-08-09

## Uniformidade diferencial da S-box

A equação diferencial da inversão, para diferenças não nulas `a` e `b`, é:

```text
inv(x) XOR inv(x XOR a) = b
```

Fora dos casos especiais `x=0` e `x=a`, ela equivale a:

```text
b * x * (x + a) = a
```

Essa é uma equação quadrática em `x`, portanto tem no máximo duas raízes no
corpo. Os dois casos especiais só são soluções simultâneas quando
`b=inv(a)`. Assim, a contagem DDT é no máximo 4.

Para `a=1` e `b=1`, o Z3 validou as quatro testemunhas concretas
`0`, `1`, `350` e `351`. Logo a uniformidade diferencial é exatamente 4 e a
probabilidade máxima de uma transição da S-box é `4/65536 = 2^-14`.

Comando:

```powershell
python ferramentas/prova_ddt_smt.py
```

## Propagação de transições máximas

Seguir localmente `delta_out=inv(delta_in)` por todas as 32 posições de uma
entrada com uma única palavra ativa produziu o mesmo padrão em todos os casos:

| Rodadas | Pesos ativos | Total ativo | Probabilidade característica local |
|---:|---|---:|---:|
| 4 | 1, 32, 31, 32 | 96 | `2^-1344` |
| 6 | 1, 32, 31, 32, 32, 32 | 160 | `2^-2240` |
| 8 | 1, 32, 31, 32, 32, 32, 32, 32 | 224 | `2^-3136` |
| 10 | 1, 32, 31, 32, 32, 32, 32, 32, 32, 32 | 288 | `2^-4032` |

Isso mostra que o padrão relaxado de quatro rodadas `1,32,1,32` não é
realizado por essa classe de transições. Entretanto, viabilidade local de
cada S-box não prova compatibilidade global com um mesmo par de estados.

## Modelo global sob chave fixa

Foi criado um modelo SMT de duas execuções reais que inclui:

- entradas válidas em `F_p`;
- whitening e chaves de rodada concretas;
- inversão algébrica em GF(2^16);
- constantes de rodada;
- matriz MDS 32 por 32;
- exigência de transição máxima em toda S-box ativa.

Comando experimental:

```powershell
python ferramentas/busca_trilha_smt.py --rounds 1 --bit 0 --timeout 30
```

Uma primeira codificação direta levou aproximadamente 20 segundos para montar
uma rodada e retornou `unknown`. Ela foi substituída por:

- matriz booleana 512 por 512 pré-calculada;
- circuitos de paridade balanceados;
- compartilhamento da inversão em palavras sem diferença;
- eliminação de S-boxes inativas na última camada observada.

A matriz booleana foi comparada com a implementação GF em todos os 512 vetores
de base e produziu resultados idênticos. Cada bit de saída depende de 245 a
272 bits de entrada, com média 256,6.

Resultados após a otimização:

| Rodadas modeladas | Construção | Timeout | Resultado |
|---:|---:|---:|---|
| 1 | 0,30 s | 30 s | `sat`, peso ativo `[1]` |
| 2 | 76,18 s | 90 s | `unknown` |

Assim, foi confirmada uma transição globalmente compatível na primeira
camada. Para duas rodadas, **nenhuma conclusão de existência ou inexistência
foi obtida**.

O gargalo restante é a combinação das 32 inversões ativas na segunda camada
com as paridades densas da MDS. O próximo refinamento deve sintetizar uma rede
XOR com eliminação de subexpressões comuns e exportar CNF/AIG para um solver
SAT nativo. O gerador atual permanece útil como especificação executável e
teste de fidelidade do modelo.
