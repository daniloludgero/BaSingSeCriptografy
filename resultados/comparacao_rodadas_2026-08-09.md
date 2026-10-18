# Comparação estrutural de 4, 6, 8 e 10 rodadas — 2026-08-09

## Objetivo

Separar três perguntas que não devem ser confundidas:

1. A rede já apresenta avalanche global?
2. Qual é o custo de rodadas adicionais?
3. Que limite conservador pode ser demonstrado para uma característica
   diferencial ou linear individual?

A API oficial de quatro rodadas e seus vetores conhecidos não foram
alterados. As demais contagens são variantes experimentais.

## Método

- 18 pares determinísticos por configuração;
- mesma chave e mesma sessão em toda a comparação;
- bits alterados nas posições 0, 63, 127, 128, 191 e 254;
- avalanche medida antes e depois do SHA-256;
- tempo apresentado como mediana por chamada;
- Python 3.12.13 e NumPy 2.3.5 no mesmo computador.

## Resultados empíricos

| Rodadas | Avalanche pré-SHA | Avalanche pós-SHA | Mediana por chamada |
|---:|---:|---:|---:|
| 4 | 50,02% (desvio 2,37%) | 50,22% (3,69%) | 44,29 ms |
| 6 | 49,88% (desvio 2,36%) | 50,89% (2,87%) | 64,81 ms |
| 8 | 48,72% (desvio 1,81%) | 49,44% (2,43%) | 76,62 ms |
| 10 | 48,96% (desvio 1,66%) | 50,02% (3,66%) | 93,87 ms |

Todas as configurações ficaram próximas de 50%. Isso mostra que a avalanche
já está saturada em quatro rodadas. A média de avalanche não fornece argumento
para escolher seis, oito ou dez rodadas; a razão para adicioná-las seria margem
contra criptoanálise estrutural.

## Limite wide-trail conservador

Premissas usadas:

- S-box de inversão bijetiva sobre GF(2^16);
- contagem diferencial máxima da S-box igual a 4, logo probabilidade máxima
  por S-box ativa de `2^-14`;
- magnitude Walsh máxima igual a 512, logo correlação máxima por S-box ativa
  de `2^-7`;
- matriz Cauchy MDS 32 por 32 com branch number 33;
- diferenças XOR e características individuais;
- XOR de chave não altera a propagação das diferenças.

Para cada par de rodadas, a soma dos pesos ativos é pelo menos 33. A fórmula
fechada foi conferida por programação dinâmica exata sobre todos os pesos de
palavra de 1 a 32.

| Rodadas | Mínimo de S-boxes ativas | Limite de característica diferencial | Limite de correlação linear |
|---:|---:|---:|---:|
| 4 | 66 | `2^-924` | `2^-462` |
| 6 | 99 | `2^-1386` | `2^-693` |
| 8 | 132 | `2^-1848` | `2^-924` |
| 10 | 165 | `2^-2310` | `2^-1155` |

## Limites da conclusão

Esses números limitam uma **característica individual** dentro da relaxação
por atividade de palavras. Eles não são uma alegação de segurança nesse número
de bits, pois não contabilizam:

- soma de muitas trilhas para o mesmo diferencial;
- dependências entre transições de S-box;
- ataques algébricos, integrais, invariantes ou de chave relacionada;
- efeitos específicos do key schedule;
- canais laterais;
- o SHA-256 final como construção completa.

Uma probabilidade de característica abaixo de `2^-512` não significa que a
construção tenha mais de 512 bits de segurança; indica apenas que esse limite
isolado deixou de ser o gargalo informativo.

## Recomendação

Manter quatro rodadas como **v4 compatível**. Para uma futura v5 de pesquisa,
se for necessário escolher agora, seis rodadas oferecem o melhor compromisso
observado: aumentam em 50% o limite de S-boxes ativas (66 para 99) com aumento
medido de aproximadamente 46% no custo mediano.

Essa recomendação é uma margem de engenharia, não uma certificação. Antes de
promover seis rodadas como versão segura, o próximo trabalho deve modelar
valores diferenciais e o key schedule com MILP/SAT/SMT e buscar ataques
estruturais que o modelo de atividade não representa.

## Reprodução

```powershell
python implementacao/analise_wide_trail.py
python testes/analise_rodadas.py --trials 18 --rounds 4 6 8 10
python -m unittest discover -s testes -p "test_*.py" -v
```
