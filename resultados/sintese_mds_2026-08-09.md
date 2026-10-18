# Síntese XOR e exportação CNF da MDS — 2026-08-09

## Origem conceitual registrada

Conforme esclarecimento do autor, a técnica é de Danilo e sua motivação vem
de um teorema próprio, da linha zeta e da teoria analítica dos números primos,
com referências bibliográficas como Riemann e von Mangoldt. Grover e Shor não
são fontes de inspiração da construção; aparecem somente como modelos
externos de ataque quando uma análise quântica exige comparação.

## Síntese

A transformação MDS foi decomposta por coluna em formas lineares de 16 bits.
Um algoritmo guloso reutilizou pares XOR presentes em múltiplas saídas, e as
32 contribuições de cada bit final foram combinadas por árvores balanceadas.

| Métrica | Resultado |
|---|---:|
| Portas XOR sem compartilhamento | 130.848 |
| Portas XOR sintetizadas | 45.050 |
| Redução | 65,57% |
| Variáveis DIMACS | 45.562 |
| Cláusulas DIMACS | 180.200 |
| Tamanho do arquivo CNF | 3.834.970 bytes |

A rede foi comparada com a multiplicação original em GF(2^16) e com a matriz
booleana 512 por 512. A regressão inclui todos os 512 vetores de base e 16
vetores pseudoaleatórios para o circuito sintetizado.

## Uso por backend

Para SAT/CNF, a rede sintetizada é significativamente menor e está exportada
em `ferramentas/mds_512.cnf`.

No Z3, instanciar cada porta como variável booleana aumentou o tempo de
construção do modelo de duas rodadas de 76,18 s para 98,10 s. Ambos retornaram
`unknown` no timeout. O modo `dense` continua padrão para Z3; `synthesized` é
destinado à futura composição SAT nativa.

## Próximo passo

O arquivo atual representa somente a relação linear da MDS. Para uma busca
SAT completa ainda é necessário codificar inversões GF(2^16), dois estados,
chaves concretas, restrições diferenciais e ligações entre rodadas.
