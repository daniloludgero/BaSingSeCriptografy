# Testes do RSD-S

Os testes automatizados usam apenas `unittest` da biblioteca padrão, além do
NumPy já exigido pela implementação.

## Suíte rápida e determinística

Execute a partir da raiz do pacote:

```powershell
python -m unittest discover -s testes -p "test_*.py" -v
```

Essa suíte verifica contrato de entrada, vetores de resposta conhecida,
determinismo, fragmentação, separação entre chave/sessão e avalanche com
chave fixa.

## Suíte estatística original

```powershell
python testes/suite_testes_completa.py
```

## Análises adicionais

```powershell
python testes/teste_branch_number.py
python testes/teste_diferencial.py
python testes/teste_linear.py
python testes/teste_trilha_diferencial_completa.py
python implementacao/analise_wide_trail.py
python testes/analise_rodadas.py --trials 18 --rounds 4 6 8 10
python ferramentas/prova_ddt_smt.py
python implementacao/analise_trilhas_concretas.py
python implementacao/mds_bitmatrix.py
python implementacao/mds_xor_synthesis.py
python implementacao/gf16_inverse_cnf.py
python implementacao/rsd_round_cnf.py
python implementacao/rsd_differential_cnf.py
python implementacao/analise_duas_rodadas.py
python implementacao/busca_branch_bound.py
python implementacao/busca_diversificada.py
```

Os testes diferencial e linear da S-box são amostrais quanto às diferenças
ou máscaras escolhidas, embora cada escolha percorra exaustivamente as 65.536
entradas. A busca de trilhas também é empírica e não substitui uma busca
formal por MILP, SAT ou SMT. A configuração completa da busca de trilhas é
intencionalmente demorada na implementação Python.

`analise_wide_trail.py` produz um limite conservador para características
individuais a partir do branch number e das cotas da S-box. A fórmula é
conferida por programação dinâmica no modelo relaxado de pesos de palavra.
Ela não soma trilhas nem substitui um modelo de valores diferenciais.

A rede sintetizada da MDS está em `ferramentas/mds_512.cnf`. Ela contém apenas
o componente linear; ainda não é um modelo CNF completo das rodadas.

A primeira rodada funcional completa está em
`ferramentas/rsd_round1_fixed.cnf`; os arquivos `*_kat_sat.cnf` e
`*_kat_unsat.cnf` verificam um vetor conhecido correto e um incorreto.

As consultas diferenciais compactas estão em
`ferramentas/rsd_diff_round1_compact_*.cnf`; a correta é SAT e o controle com
um bit de diferença alterado é UNSAT.

A análise concreta das quatro testemunhas máximas por quatro rodadas está em
`implementacao/analise_duas_rodadas.py`.

A busca ampliada e reproduzível está em
`implementacao/busca_branch_bound.py`; ela é amostral e não prova ótimo global.

A busca diversificada em `implementacao/busca_diversificada.py` acrescenta
quatro fundos determinísticos e testemunhas DDT de contagem 2. Sua execução
completa também é amostral e mantém a mesma ressalva de não provar ótimo.

O Z3 está instalado de forma isolada em `ferramentas/_vendor`. Após a
otimização booleana, o modelo global experimental retorna `sat` para uma
rodada; duas rodadas ainda podem retornar `unknown` por timeout.

## Contrato da API v4

- `x` e `y`: inteiros em `0 <= valor < 2^255 - 19`;
- `s`: objeto `bytes` com exatamente 32 bytes;
- `n_sess`: inteiro em `0 <= valor < 2^64`;
- saída pública: 32 bytes.

Entradas fora desse contrato geram `TypeError` ou `ValueError`; não são
reduzidas nem truncadas silenciosamente.
