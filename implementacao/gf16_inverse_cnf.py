"""Relação CNF exata y = inv(x) em GF(2^16)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path

from mds_real import gf_inv, gf_mult

BITS = 16


@dataclass(frozen=True)
class InverseCnf:
    x_vars: tuple[int, ...]
    y_vars: tuple[int, ...]
    nonzero_var: int
    gates: tuple[tuple[str, int, int, int], ...]
    product_vars: tuple[int, ...]
    clauses: tuple[tuple[int, ...], ...]
    variable_count: int


def _add_and(clauses: list[tuple[int, ...]], a: int, b: int, z: int) -> None:
    clauses.extend(((-a, -b, z), (a, -z), (b, -z)))


def _add_xor(clauses: list[tuple[int, ...]], a: int, b: int, z: int) -> None:
    clauses.extend(((-a, -b, -z), (a, b, -z), (a, -b, z), (-a, b, z)))


@lru_cache(maxsize=1)
def build_inverse_cnf() -> InverseCnf:
    clauses: list[tuple[int, ...]] = []
    gates: list[tuple[str, int, int, int]] = []
    x_vars = tuple(range(1, BITS + 1))
    y_vars = tuple(range(BITS + 1, 2 * BITS + 1))
    next_var = 2 * BITS + 1

    # Todos os 256 produtos bilineares x_i AND y_j são compartilhados.
    partials: dict[tuple[int, int], int] = {}
    for left_bit in range(BITS):
        for right_bit in range(BITS):
            output = next_var
            next_var += 1
            _add_and(clauses, x_vars[left_bit], y_vars[right_bit], output)
            gates.append(("and", x_vars[left_bit], y_vars[right_bit], output))
            partials[left_bit, right_bit] = output

    forms: list[set[int]] = [set() for _ in range(BITS)]
    for (left_bit, right_bit), signal in partials.items():
        product = gf_mult(1 << left_bit, 1 << right_bit)
        for output_bit in range(BITS):
            if product & (1 << output_bit):
                forms[output_bit].add(signal)

    # Reutiliza pares XOR comuns entre os 16 bits do produto reduzido.
    while True:
        frequencies: Counter[tuple[int, int]] = Counter()
        for form in forms:
            frequencies.update(combinations(sorted(form), 2))
        if not frequencies:
            break
        pair, frequency = frequencies.most_common(1)[0]
        if frequency < 2:
            break
        output = next_var
        next_var += 1
        _add_xor(clauses, pair[0], pair[1], output)
        gates.append(("xor", pair[0], pair[1], output))
        for form in forms:
            if pair[0] in form and pair[1] in form:
                form.remove(pair[0])
                form.remove(pair[1])
                form.add(output)

    product_vars: list[int] = []
    for form in forms:
        signals = sorted(form)
        result = signals[0]
        for signal in signals[1:]:
            output = next_var
            next_var += 1
            _add_xor(clauses, result, signal, output)
            gates.append(("xor", result, signal, output))
            result = output
        product_vars.append(result)

    # nz <-> OR(x). Se x=0, também força y=0.
    nonzero = next_var
    next_var += 1
    for x_var in x_vars:
        clauses.append((-x_var, nonzero))
    clauses.append(tuple(x_vars) + (-nonzero,))
    for y_var in y_vars:
        clauses.append((-y_var, nonzero))

    # x*y = 1 quando x!=0; x*y = 0 quando x=0.
    clauses.extend(((-product_vars[0], nonzero), (product_vars[0], -nonzero)))
    for product_var in product_vars[1:]:
        clauses.append((-product_var,))

    return InverseCnf(
        x_vars,
        y_vars,
        nonzero,
        tuple(gates),
        tuple(product_vars),
        tuple(clauses),
        next_var - 1,
    )


def assignment_for_pair(circuit: InverseCnf, x: int, y: int) -> list[bool]:
    values = [False] * (circuit.variable_count + 1)
    for bit, variable in enumerate(circuit.x_vars):
        values[variable] = bool(x & (1 << bit))
    for bit, variable in enumerate(circuit.y_vars):
        values[variable] = bool(y & (1 << bit))
    for operation, left, right, output in circuit.gates:
        if operation == "and":
            values[output] = values[left] and values[right]
        else:
            values[output] = values[left] ^ values[right]
    values[circuit.nonzero_var] = x != 0
    return values


def clauses_hold(circuit: InverseCnf, values: list[bool]) -> bool:
    return all(
        any(values[abs(literal)] == (literal > 0) for literal in clause)
        for clause in circuit.clauses
    )


def accepts_pair(x: int, y: int) -> bool:
    circuit = build_inverse_cnf()
    return clauses_hold(circuit, assignment_for_pair(circuit, x, y))


def export_dimacs(path: Path) -> None:
    circuit = build_inverse_cnf()
    lines = [
        "c RSD-S GF(2^16) inverse relation y=inv(x)",
        "c x_bits_lsb_first " + " ".join(map(str, circuit.x_vars)),
        "c y_bits_lsb_first " + " ".join(map(str, circuit.y_vars)),
        f"p cnf {circuit.variable_count} {len(circuit.clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in circuit.clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    circuit = build_inverse_cnf()
    samples = list(range(256)) + [0x1234, 0x8000, 0xFFFE, 0xFFFF]
    correct = all(accepts_pair(value, gf_inv(value)) for value in samples)
    wrong = all(
        not accepts_pair(value, gf_inv(value) ^ 1)
        for value in samples
        if (gf_inv(value) ^ 1) != gf_inv(value)
    )
    print(f"pares corretos aceitos: {correct}")
    print(f"pares incorretos rejeitados: {wrong}")
    print(f"variaveis: {circuit.variable_count}")
    print(f"clausulas: {len(circuit.clauses)}")
    print(f"portas: {len(circuit.gates)}")
