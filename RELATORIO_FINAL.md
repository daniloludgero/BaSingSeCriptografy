# RSD-S — Riemann Spectral Diffusion (Refinado)
## Relatório Final de Desenvolvimento e Testes

**Status: protótipo de pesquisa que passa em testes estatísticos básicos.
NÃO auditado, NÃO revisado por pares, NÃO recomendado para uso em produção.**

---

## 1. Linha do tempo do projeto

Este pacote documenta a evolução de uma proposta de primitiva
criptográfica original ("Riemann Spectral Diffusion"), da concepção
inicial até uma versão que passa nos testes estatísticos básicos de
uma função de difusão. A honestidade sobre cada etapa — incluindo
os erros encontrados — é parte deliberada deste relatório.

### v0 — RSD original (linear, sem S-box)
Proposta inicial: fragmentação de dois escalares, modulação por
polinômios de Chebyshev, rotação por matriz derivada de QR de uma
matriz gaussiana. **Resultado: 9-14% de avalanche** (muito abaixo do
critério de ~50%). Causa: toda a transformação era linear — sem
substituição não-linear, e uma transformação estritamente linear é
recuperável por álgebra linear elementar (demonstrado: matriz de
rotação R recuperada por completo com 8 observações simples).

### v1 — RSD-S (com S-boxes espectrais e matriz MDS declarada)
Adição de S-boxes por rodada (baseadas em polinômios de Chebyshev
avaliados em um ponto secreto `t`) e uma matriz de difusão alegada
como MDS (Maximum Distance Separable). **Resultado: 18.65% de
avalanche.** Dois problemas graves encontrados:
- A matriz de difusão fornecida tinha **rank 5 de 16** — não
  invertível, não MDS, apesar de alegado o contrário.
- A S-box, construída via `cos(k·arccos(t - w_norm))`, tinha apenas
  **23.393 de 65.536 valores únicos** (não é bijeção) e apenas 25%
  de avalanche isolada, por saturação do domínio de `arccos` e
  insuficiente diversidade de graus polinomiais (só 16 valores
  possíveis de `k`).

### v2 — Matriz de difusão corrigida
Substituição da matriz original por uma matriz de Cauchy sobre
GF(2^16), MDS por construção matemática (teorema: toda matriz de
Cauchy sobre corpo finito é MDS). Verificado: rank completo (16/16),
0 de 300 submatrizes testadas são singulares. **Resultado: 19.90% de
avalanche** — melhora real, mas marginal. Isso revelou que a matriz
não era a causa dominante do problema.

### v3 — S-box corrigida
Substituição da S-box Chebyshev por uma S-box de inversão em
GF(2^16) (mesma família da S-box do AES, generalizada de 8 para 16
bits) + XOR de constante de rodada. Verificado: bijeção completa
(65.536/65.536 valores únicos), 49.27% de avalanche isolada.
**Resultado combinado com v2: 23.79% de avalanche** — ainda
insuficiente, apesar de ambos os componentes serem individualmente
corretos.

### v4 — Fragmentação corrigida (correção final)
Investigação revelou a causa raiz real: a especificação original
fragmentava `x` e `y` (elementos de F_p, `p = 2^255-19`, até 255
bits) em apenas **8 fatias de 16 bits = 128 bits** — descartando
silenciosamente **~127 bits (49.8%) de cada entrada**. Isso causava
colisões massivas (2^127 valores diferentes de `x` produzindo a
mesma saída) independentemente de quão boas fossem a S-box e a
matriz. Corrigido para 16 fatias de 16 bits por entrada (256 bits,
cobertura completa), com estado expandido para 32 palavras e matriz
Cauchy MDS 32×32. **Resultado: 50.31% de avalanche pré-hash, 49.53%
pós-hash, desvio padrão baixo (1.87% e 3.34%)** — critério de
avalanche atingido.

---

## 2. O que os testes confirmam (v4)

| Propriedade testada | Resultado |
|---|---|
| Matriz de difusão é MDS (rank completo, nenhum menor singular) | Confirmado |
| S-box é bijeção completa | Confirmado |
| Efeito avalanche (~50% ± baixo desvio) | Confirmado (50.31% / 49.53%) |
| Ausência de linearidade básica (f(x1) XOR f(x2) != f(x1 XOR x2)) | Confirmado |
| Cobertura completa de bits (nenhum bit descartado) | Confirmado |

Todos os testes são reproduzíveis via `testes/suite_testes_completa.py`.

---

## 3. O que NÃO foi testado — limites reais deste trabalho

Esta seção é tão importante quanto a anterior. Passar nos testes
acima é o requisito **mínimo e mais básico** que qualquer proposta de
primitiva de difusão/hash deve satisfazer — é o equivalente a um
programa passar em "compila sem erros", não a "está correto".

**Não testado, e necessário antes de qualquer confiança real:**

- **Criptoanálise diferencial formal**: busca sistemática por trilhas
  diferenciais de alta probabilidade através das 4 rodadas. Isso
  exige análise matemática dedicada (não apenas testes estatísticos
  amostrais) da S-box e da matriz em conjunto.
- **Criptoanálise linear formal**: busca por aproximações lineares
  com viés estatisticamente significativo entre entrada e saída.
- **Ataques de chave relacionada**: como o esquema de chaves de
  rodada (via HMAC hierárquico) se comporta sob chaves relacionadas.
- **Ataques de canal lateral**: tempo de execução, uso de cache,
  possivelmente vazando informação sobre `s` ou o estado interno.
- **Ataques algébricos estruturados**: equações sobre GF(2^16) que
  explorem a estrutura específica de "inversão + Cauchy" (esse tipo
  de ataque quebrou variantes anteriores de cifras baseadas em
  inversão pura antes de ajustes finais em designs reais).
- **Prova de segurança formal**: nenhuma redução a um problema
  difícil conhecido e estudado (diferente de ML-DSA, que reduz a
  Module-LWE, ou SLH-DSA, que reduz a resistência de hash).

**Contexto histórico para calibrar expectativa**: AES levou mais de
uma década de criptoanálise ativa por centenas de pesquisadores antes
de ganhar confiança ampla. SHA-3/Keccak passou por 5 anos de
competição pública NIST. Isso não é burocracia — é o tempo real que
leva para descobrir fraquezas sutis que testes automatizados como os
daqui não capturam.

---

## 4. Recomendação de uso

**Não usar em produção ou para proteger dados sensíveis reais.**

Usos apropriados para este estágio do trabalho:
- Material de estudo sobre construção de cifras (S-box, MDS, rodadas).
- Ponto de partida para submissão a criptoanalistas ou comunidade de
  pesquisa em criptografia para revisão por pares.
- Demonstração de processo de depuração criptográfica rigorosa (a
  jornada v0 -> v4 é, em si, um exemplo pedagógico de como identificar
  e corrigir falhas estruturais em uma proposta de cifra).

---

## 5. Estrutura deste pacote

```
rsd_final_package/
├── RELATORIO_FINAL.md              — este documento
├── especificacao/
│   └── especificacao_original.md   — histórico e contexto das propostas (v0, v1)
├── implementacao/
│   ├── mds_real.py                 — construção e verificação de matriz Cauchy MDS
│   ├── rsd_s_v1_original.py        — implementação fiel da especificação original
│   ├── rsd_s_v2_matriz_corrigida.py
│   ├── rsd_s_v3_sbox_corrigida.py
│   └── rsd_s_v4_final.py           — versão final, todas as correções aplicadas
├── testes/
│   ├── teste_avalanche_v1.py       — teste que expôs a fraqueza original
│   └── suite_testes_completa.py    — suíte reproduzível para v4 (5 testes)
└── resultados/
    └── evolucao_avalanche.md       — tabela resumida de todos os resultados medidos
```

## 6. Como reproduzir

```bash
pip install numpy
cd testes/
python3 suite_testes_completa.py
```

## 7. Validação automatizada da API

A v4 agora inclui validação explícita de entradas, vetores de resposta
conhecida e uma suíte determinística baseada em `unittest`.

Contrato público:

- `x` e `y` são elementos de `F_p`, com `0 <= valor < 2^255 - 19`;
- `s` possui exatamente 32 bytes;
- `n_sess` é um inteiro sem sinal de 64 bits;
- a saída pública possui 32 bytes.

Execute a partir da raiz do pacote:

```bash
python -m unittest discover -s testes -p "test_*.py" -v
```

Os resultados reproduzidos em 2026-07-28 estão documentados em
`resultados/validacao_2026-07-28.md`.

## 8. Comparação experimental de número de rodadas

A API oficial permanece fixada em quatro rodadas e conserva todos os vetores
de resposta conhecida. Funções experimentais permitem comparar de 1 a 255
rodadas sem alterar essa compatibilidade.

Uma comparação pré-SHA e pós-SHA entre 4, 6, 8 e 10 rodadas mostrou avalanche
próxima de 50% em todas as configurações. Portanto, avalanche não diferencia
as variantes: quatro rodadas já saturam essa métrica.

Uma análise wide-trail conservadora, baseada no branch number 33 e nas cotas
da S-box de inversão, fornece pelo menos 66, 99, 132 e 165 S-boxes ativas para
4, 6, 8 e 10 rodadas, respectivamente. Esses são limites para características
individuais, não níveis de segurança da construção.

Os métodos, números completos, ressalvas e comandos de reprodução estão em
`resultados/comparacao_rodadas_2026-08-09.md`.

## 9. Análise algébrica e modelo SMT

A uniformidade diferencial da S-box foi elevada de observação amostral para
resultado algébrico verificável: a equação diferencial reduz a um polinômio
quadrático, limitando a DDT a quatro soluções, e o Z3 validou quatro
testemunhas que atingem essa cota. A probabilidade diferencial máxima da S-box
é, portanto, exatamente `2^-14`.

Também foi construído um modelo SMT global sob chave fixa, incluindo entradas
em `F_p`, key schedule concreto, inversão e MDS. No ambiente atual, até a
consulta de uma rodada retornou `unknown` após o timeout; isso é registrado
como resultado inconclusivo, não como prova de segurança.

Detalhes e comandos estão em `resultados/analise_smt_2026-08-09.md`.

## 10. Síntese XOR da MDS

A MDS booleana foi sintetizada de 130.848 para 45.050 portas XOR, redução de
65,57%, e exportada como componente DIMACS CNF. A equivalência foi testada
contra a implementação GF(2^16). Resultados e limitações estão documentados
em `resultados/sintese_mds_2026-08-09.md`.

## 11. CNF da inversão e da primeira rodada

A inversão GF(2^16) foi codificada em 575 variáveis e 1.962 cláusulas. A
primeira rodada completa sob chave fixa foi exportada com 64.986 variáveis e
246.056 cláusulas. Um vetor correto foi SAT e a mesma saída com um bit
invertido foi UNSAT, confirmando fidelidade funcional para esse caso.

Detalhes estão em `resultados/cnf_inversao_round1_2026-08-09.md`.

## 12. Consulta diferencial CNF de uma rodada

Uma formulação diferencial compacta com 46.217 variáveis e 184.749 cláusulas
foi resolvida pelo Z3. A transição máxima correta foi SAT e a diferença de
saída com um bit alterado foi UNSAT. A versão que duplicava duas execuções
completas expirou e permanece registrada como inconclusiva.

Método e limitações estão em
`resultados/diferencial_cnf_round1_2026-08-09.md`.

## 13. Restrição estrutural e ameaça quântica

Foi registrada a intenção do autor de não basear o projeto em uma construção
circular/periódica análoga à descoberta de período. Isso é tratado como
restrição de projeto, não como prova de resistência quântica.

Como a RSD-S atual é uma primitiva simétrica e não um esquema de fatoração ou
logaritmo discreto, Grover é a referência quântica genérica mais direta. A
formulação cuidadosa e as condições necessárias para alegações futuras estão
em `especificacao/RESTRICOES_DE_PROJETO.md`.

## 14. Análise diferencial concreta multirrodada

As quatro testemunhas máximas da diferença inicial `1` foram propagadas pelas
quatro rodadas oficiais sob chave fixa. Todas apresentaram perfil de atividade
`1,32,32,32`, apenas uma transição DDT de contagem 4 e peso de característica
`2^-1454`. A segunda camada foi validada por CNF SAT/UNSAT.

Esse é o peso de características específicas, não a probabilidade diferencial
exata agregada. Escopo, método e artefatos estão em
`resultados/analise_multirrodada_2026-08-09.md`.

## 15. Busca diferencial branch-and-bound

Uma busca amostral avaliou 7.744 candidatos válidos entre 32 posições, 64
diferenças e quatro testemunhas iniciais. Os 256 melhores candidatos foram
propagados pelas quatro rodadas. A melhor característica encontrada possui
perfil `1,32,31,32` e peso `2^-1439`, sem alegação de ótimo global.

Cobertura, método e limitações estão em
`resultados/branch_bound_2026-08-09.md`.

## 16. Busca diferencial com fundos e classes DDT diversificados

A busca foi ampliada para quatro estados de fundo determinísticos em `F_p²` e
para transições iniciais de contagem DDT 2 e 4. Foram avaliados 31.200
candidatos válidos; 1.024 finalistas passaram pela propagação completa de
quatro rodadas. O melhor peso permaneceu `2^-1439`, no fundo zero. Nenhum
fundo não nulo ou transição inicial de contagem 2 melhorou esse resultado.

Trata-se de evidência amostral sob chave e sessão fixas, não de prova de
otimalidade ou segurança. Configuração, controles e ressalvas estão em
`resultados/busca_diversificada_2026-08-09.md`.
