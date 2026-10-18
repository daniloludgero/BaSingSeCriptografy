# Restrições de projeto e modelo de ameaça quântico

## Autoria e origem conceitual

A técnica RSD-S apresentada neste pacote é atribuída a **Danilo**. Segundo o
autor, ela não foi inspirada nos algoritmos de Grover ou Shor. Sua motivação
declarada vem de um teorema próprio e de uma linha bibliográfica ligada à
função zeta e à teoria analítica dos números primos, incluindo referências
como Bernhard Riemann, Hans von Mangoldt e outros autores desse campo.

Essas referências registram a origem conceitual informada pelo autor. Elas não
devem ser interpretadas, sem demonstração adicional, como validação do
teorema próprio ou como prova de segurança criptográfica.

## Premissa estrutural registrada pelo autor

A RSD-S não deve depender de uma construção geométrica circular, de uma
estrutura periódica análoga à usada na descoberta de período, nem de
fatoração ou logaritmo discreto como fundamento de segurança. Essa restrição
deve ser preservada em evoluções futuras do projeto.

## Modelos externos de ataque

O algoritmo de Shor é um algoritmo quântico para fatoração e logaritmo
discreto baseado em descoberta de período e transformada quântica de Fourier.
A ausência de uma representação circular explícita não é, isoladamente, uma
prova de resistência a Shor: periodicidades e estruturas de grupo podem estar
presentes sem aparecer geometricamente como círculos.

Grover e Shor são mencionados neste pacote somente como modelos externos de
criptoanálise quântica conhecidos, não como inspiração da técnica.

Na forma atual, a RSD-S é uma primitiva simétrica de difusão/hash com chave;
ela não define um esquema público baseado em fatoração ou logaritmo discreto.
Assim, Shor não é o ataque genérico mais direto contra esta primitiva isolada.
Para uma chave ideal de 256 bits, a referência quântica genérica mais próxima
é Grover, que sugere aproximadamente 128 bits de custo de busca — antes de
considerar ataques estruturais específicos.

## Regra para alegações futuras

O projeto pode declarar que **não se baseia nos problemas atacados por Shor**.
Não deve declarar que “supera Shor”, que é “pós-quântico” ou que oferece um
nível específico de segurança quântica sem:

- modelo formal do objetivo de segurança;
- análise de oráculos e consultas quânticas;
- limites contra busca, colisão e preimagem quânticas;
- análise de possíveis períodos ou subgrupos ocultos na construção;
- revisão independente.
