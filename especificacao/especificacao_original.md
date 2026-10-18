# Especificação Original — Contexto e Histórico

Este documento resume o contexto das propostas originais (v0 e v1)
que motivaram o trabalho de teste e correção documentado no
RELATORIO_FINAL.md.

## v0 — Riemann Spectral Diffusion (RSD)

Proposta inicial: uma camada de "difusão espectral" para dois
escalares (x, y), inspirada em invariância de gauge e na fase da
função zeta de Riemann. Componentes principais:

- Fragmentação de x, y em `w` fatias de `b` bits.
- Modulação por polinômios ortogonais (Chebyshev, Hermite ou
  Laguerre) avaliados em um ponto secreto `t`, derivado de uma
  semente compartilhada `s` e um nonce de sessão.
- Rotação por uma matriz `R`, construída via decomposição QR de uma
  matriz gaussiana aleatória (determinística a partir de `s`),
  escalada e reduzida módulo `2^b`.

Alegações de segurança (Seção 5 da proposta original):
- Resistência a Shor: alegada por ausência de estrutura de grupo
  abeliano explorável.
- Resistência a Grover: alegada via Proof-of-Work com parâmetro `d`.
- Difusão estrita (~50% de bits alterados por 1 bit de entrada).
- Dependência da semente: segurança alegada como decorrente do
  sigilo de `s`.

## v1 — RSD-S (refinamento com S-boxes e matriz MDS)

Refinamento da proposta v0, adicionando:
- S-boxes dinâmicas por rodada, construídas a partir de polinômios
  de Chebyshev avaliados no ponto secreto `t` (uma S-box diferente
  por rodada, dependente de `s`, nonce de sessão, e número da rodada).
- Uma matriz de difusão pública `M`, alegada como MDS (Maximum
  Distance Separable), construída "a partir de um código Reed-Solomon
  sistemático" (a fórmula de implementação de referência fornecida,
  porém, não corresponde a uma construção Reed-Solomon genuína).
- Estrutura de rede de 4 rodadas: substituição (S-box) -> permutação
  (matriz M) -> adição de chave de rodada (XOR), seguida de SHA-256
  final.
- Chaves de rodada derivadas via HMAC-SHA256 hierárquico a partir de
  uma semente `s` e nonce de sessão.

## O que este pacote faz com essas propostas

Cada componente alegado (resistência a Shor, difusão estrita,
propriedade MDS da matriz, bijetividade da S-box) foi implementado
fielmente e testado empiricamente. Os resultados de cada teste, os
problemas encontrados, e as correções aplicadas estão documentados em
`RELATORIO_FINAL.md` e nos arquivos de `implementacao/` (versões v1
a v4, refletindo a evolução real do processo de teste e correção).

Os textos completos e formais das propostas originais (com toda a
notação matemática, algoritmos formais, e fórmulas detalhadas) fazem
parte do histórico da conversa em que este trabalho foi desenvolvido
e não estão reproduzidos aqui na íntegra; este documento preserva o
contexto essencial para entender as decisões de implementação e teste
registradas no restante deste pacote.
