# Evolução dos Resultados — Efeito Avalanche

Tabela completa de todos os testes de avalanche realizados ao longo
do desenvolvimento, na ordem em que foram executados.

| Versão | Componentes | Difusão medida | Status |
|---|---|---|---|
| v0 (RSD linear) | Fragmentação + modulação Chebyshev + rotação matricial (sem S-box) | 9.34% (escala original), 13.69% (escala corrigida) | Falhou — linear, recuperável por álgebra linear |
| v1 (RSD-S original) | + S-box Chebyshev + matriz M (alegada MDS) | 18.65% | Falhou — matriz rank 5/16, S-box com 35.7% de valores únicos |
| v2 (matriz corrigida) | + matriz Cauchy MDS (rank 16/16 comprovado) | 19.90% | Falhou — S-box ainda com baixa avalanche isolada (25%) |
| v3 (S-box corrigida) | + S-box de inversão GF(2^16) (bijeção, ~49% avalanche isolada) | 23.79% | Falhou — fragmentação descartava 127 de 255 bits |
| v4 (fragmentação corrigida) | + fragmentação completa (16 fatias x 16 bits = 256 bits, estado de 32 palavras) | **50.31% (pré-hash) / 49.53% (pós-hash)** | **Passou no critério de avalanche** |

## Testes adicionais na v4

| Teste | Resultado |
|---|---|
| Matriz MDS (rank completo, 0 menores singulares em 300 testados) | Confirmado |
| S-box bijetora (65536/65536 valores únicos) | Confirmado |
| Ausência de linearidade básica (f(x1)⊕f(x2) ≠ f(x1⊕x2)) | Confirmado |
| Cobertura completa de bits (bits 128-254, antes descartados, agora afetam a saída) | Confirmado |

## Interpretação

A melhora não foi linear ao longo das correções — cada correção
resolveu exatamente o problema que a investigação identificou, mas
o ganho real só apareceu quando os TRÊS problemas estruturais
(matriz, S-box, fragmentação) foram corrigidos simultaneamente. Isso
ilustra bem por que testes de criptoanálise precisam avaliar o
sistema como um todo, não apenas componentes isolados: um componente
individualmente correto (ex: matriz MDS válida) pode não produzir
nenhuma melhora visível se outro componente (fragmentação) estiver
descartando a maior parte da informação de entrada antes mesmo do
processamento começar.
