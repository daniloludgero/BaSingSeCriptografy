# Validação reproduzível da RSD-S v4 — 2026-07-28

Ambiente usado:

- Python 3.12.13
- NumPy 2.3.5
- Windows

## Alterações de robustez avaliadas

- Validação explícita de `x`, `y`, `s` e `n_sess`.
- Rejeição de elementos fora de `F_p`, em vez de truncamento silencioso.
- Chave definida como exatamente 32 bytes.
- Sessão definida como inteiro sem sinal de 64 bits.
- S-box em cache marcada como somente leitura.
- Imports dos testes atualizados para os nomes reais dos módulos.
- Saída da suíte compatível com consoles Windows CP1252.
- Busca diferencial alterada para manter chave e sessão fixas.
- Quatro vetores de resposta conhecida adicionados.

## Resultados

### Suíte automatizada determinística

Comando:

```powershell
python -m unittest discover -s testes -p "test_*.py" -v
```

Resultado: **10 de 10 testes passaram**.

Foram verificados:

- vetores de resposta conhecida;
- determinismo;
- tipos e limites da API;
- reconstrução integral após fragmentação;
- separação entre chave e sessão;
- avalanche com chave fixa em bits baixos, centrais e altos;
- imutabilidade da S-box em cache.

### Suíte estatística básica

Comando:

```powershell
python testes/suite_testes_completa.py
```

Resultado: **5 de 5 testes passaram**.

- Matriz: rank 32/32 e nenhum menor singular entre 300 amostras.
- S-box: 65.536 de 65.536 valores únicos.
- Avalanche pós-hash: 49,06%, desvio de 3,32%.
- Linearidade XOR básica: não detectada.
- Bits 128, 150, 180, 200, 230 e 254 alteraram a saída.

### Branch number

Resultado observado em 50 ensaios de peso 1: **33**, o máximo possível
para uma matriz 32 por 32.

### S-box isolada

Resultados obtidos durante esta rodada de avaliação:

- Probabilidade diferencial máxima encontrada: `0,000061`
  (`4 / 65536`), duas vezes a referência mínima usada pelo teste.
- Maior viés linear encontrado entre 556 pares de máscaras:
  `0,003845`, aproximadamente 1,97 vez a referência usada pelo teste.

Ambos ficaram dentro dos critérios definidos pelos scripts.

### Busca diferencial reduzida com chave fixa

Foram usadas 100 amostras para cada bit de entrada 0, 128 e 254, mantendo
a mesma chave e a mesma sessão durante todo o experimento.

Resultado:

- bit 0: 100 diferenças únicas em 100;
- bit 128: 100 diferenças únicas em 100;
- bit 254: 100 diferenças únicas em 100.

Nenhuma diferença de saída se repetiu.

## Interpretação correta

Os resultados demonstram que a implementação é executável, determinística,
possui contrato de entrada verificável e não apresentou falhas nos testes
estatísticos realizados.

Eles **não demonstram segurança criptográfica**. Em particular, ainda faltam:

- busca formal de trilhas por MILP, SAT ou SMT;
- análise das quatro rodadas com limites prováveis demonstráveis;
- análise de chaves relacionadas e simetrias;
- avaliação de canal lateral;
- implementação de tempo constante;
- revisão independente por criptoanalistas.

O código Python também é lento e usa acesso à tabela da S-box indexado por
estado potencialmente secreto. Ele deve continuar classificado como protótipo
de pesquisa, não como implementação para produção.
