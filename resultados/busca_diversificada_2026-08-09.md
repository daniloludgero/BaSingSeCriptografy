# Busca diferencial diversificada — 2026-08-09

## Objetivo

Ampliar a busca branch-and-bound anterior em duas direções: estados de fundo
não nulos e transições iniciais da S-box com contagem DDT 2, além das quatro
testemunhas de contagem 4. A análise continua sendo aplicada à construção
RSD-S proposta por Danilo e não pressupõe uma estrutura inspirada em Shor ou
Grover.

## Configuração reproduzível

- chave fixa: `a5` repetido 32 vezes;
- sessão: `7`;
- quatro fundos determinísticos em `F_p²`, incluindo o fundo zero;
- 32 posições ativas;
- 32 diferenças: as 16 diferenças de um bit e 16 valores pseudoaleatórios
  determinísticos;
- por diferença: quatro testemunhas DDT de contagem 4 e quatro de contagem 2;
- 32.768 candidatos teóricos, dos quais 31.200 satisfizeram o domínio completo
  `F_p²` nos dois lados;
- os oito melhores candidatos por par fundo/posição foram mantidos após duas
  rodadas, totalizando 1.024 finalistas propagados pelas quatro rodadas.

Os fundos não nulos são gerados com as palavras superiores mascaradas para
ficarem abaixo de `2^254`, portanto estritamente abaixo de `p = 2^255 - 19`.
A validade é reavaliada depois de substituir a palavra ativa nos dois estados.
As testemunhas de contagem 2 são canônicas e sua multiplicidade exata foi
confirmada sobre as 65.536 entradas da S-box.

Comando:

```powershell
python implementacao/busca_diversificada.py
```

## Resultado

O menor custo encontrado permaneceu em 1.439 bits:

```text
background=0, slot=13, delta=0x0001
witness=0x015e ou 0x015f, contagem DDT inicial=4
perfil=((1,1,14),(32,0,480),(31,0,465),(32,0,480))
palavras ativas finais=32
```

Assim, a característica tem peso `2^-1439`. Nenhum fundo não nulo nem
transição inicial de contagem 2 superou o melhor resultado anterior. Uma
passagem preliminar com feixe 2 produziu apenas `2^-1453` porque descartou o
próprio candidato conhecido; por isso o resultado reportado usa feixe 8.

## Limites da conclusão

Esta é uma busca amostral sob uma chave e sessão fixas. O resultado não prova
que `2^-1439` seja o ótimo global, não agrega todas as características que
levam à mesma diferença final e não estabelece segurança da primitiva. Os
fundos, diferenças e testemunhas cobrem classes adicionais relevantes, mas
continuam sendo subconjuntos do espaço completo.

