"""Síntese de uma rede XOR compartilhada para a MDS de 512 bits."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path

import numpy as np

from mds_real import gf_mult
from mds_bitmatrix import STATE_BITS, apply_mds_bitmatrix, mds_bit_rows
from rsd_s_v4_final import B, M_CAUCHY_32, W


@dataclass(frozen=True)
class XorTemplate:
    gates: tuple[tuple[int, int, int], ...]
    outputs: tuple[int, ...]
    signal_count: int
    direct_gate_count: int


@dataclass(frozen=True)
class XorCircuit:
    input_count: int
    gates: tuple[tuple[int, int, int], ...]
    outputs: tuple[int, ...]
    signal_count: int
    direct_gate_count: int


def _coefficient_forms(column: int) -> list[set[int]]:
    forms: list[set[int]] = []
    for output_word in range(W):
        coefficient = int(M_CAUCHY_32[output_word, column])
        for output_bit in range(B):
            sources = {
                input_bit
                for input_bit in range(B)
                if gf_mult(1 << input_bit, coefficient) & (1 << output_bit)
            }
            forms.append(sources)
    return forms


def _xor_pair(gates: list[tuple[int, int, int]], left: int, right: int) -> int:
    output = B + len(gates)
    gates.append((left, right, output))
    return output


@lru_cache(maxsize=W)
def synthesize_column(column: int) -> XorTemplate:
    if not 0 <= column < W:
        raise ValueError(f"column deve estar entre 0 e {W - 1}")
    forms = _coefficient_forms(column)
    direct = sum(max(0, len(form) - 1) for form in forms)
    gates: list[tuple[int, int, int]] = []

    while True:
        frequencies: Counter[tuple[int, int]] = Counter()
        for form in forms:
            frequencies.update(combinations(sorted(form), 2))
        if not frequencies:
            break
        pair, frequency = frequencies.most_common(1)[0]
        if frequency < 2:
            break
        new_signal = _xor_pair(gates, pair[0], pair[1])
        for form in forms:
            if pair[0] in form and pair[1] in form:
                form.remove(pair[0])
                form.remove(pair[1])
                form.add(new_signal)

    outputs: list[int] = []
    completed: dict[tuple[int, ...], int] = {}
    for form in forms:
        key = tuple(sorted(form))
        if key in completed:
            outputs.append(completed[key])
            continue
        if not key:
            raise RuntimeError("forma linear nula inesperada")
        result = key[0]
        for signal in key[1:]:
            result = _xor_pair(gates, result, signal)
        completed[key] = result
        outputs.append(result)
    return XorTemplate(tuple(gates), tuple(outputs), B + len(gates), direct)


def _balanced_xor(
    signals: list[int], gates: list[tuple[int, int, int]], next_signal: int
) -> tuple[int, int]:
    level = list(signals)
    while len(level) > 1:
        following: list[int] = []
        for index in range(0, len(level) - 1, 2):
            gates.append((level[index], level[index + 1], next_signal))
            following.append(next_signal)
            next_signal += 1
        if len(level) % 2:
            following.append(level[-1])
        level = following
    return level[0], next_signal


@lru_cache(maxsize=1)
def build_mds_xor_circuit() -> XorCircuit:
    gates: list[tuple[int, int, int]] = []
    contributions: list[list[int]] = [[] for _ in range(STATE_BITS)]
    next_signal = STATE_BITS
    direct = sum(max(0, len(row) - 1) for row in mds_bit_rows())

    for column in range(W):
        template = synthesize_column(column)
        mapping = {bit: column * B + bit for bit in range(B)}
        for left, right, output in template.gates:
            mapping[output] = next_signal
            gates.append((mapping[left], mapping[right], next_signal))
            next_signal += 1
        for output_bit, signal in enumerate(template.outputs):
            contributions[output_bit].append(mapping[signal])

    outputs: list[int] = []
    for signals in contributions:
        output, next_signal = _balanced_xor(signals, gates, next_signal)
        outputs.append(output)
    return XorCircuit(STATE_BITS, tuple(gates), tuple(outputs), next_signal, direct)


def evaluate_circuit(circuit: XorCircuit, vector: np.ndarray) -> np.ndarray:
    values = [0] * circuit.signal_count
    for word in range(W):
        for bit in range(B):
            values[word * B + bit] = (int(vector[word]) >> bit) & 1
    for left, right, output in circuit.gates:
        values[output] = values[left] ^ values[right]
    result = np.zeros(W, dtype=np.uint32)
    for index, signal in enumerate(circuit.outputs):
        if values[signal]:
            result[index // B] |= np.uint32(1 << (index % B))
    return result


def verify_circuit(samples: int = 16) -> bool:
    circuit = build_mds_xor_circuit()
    generator = np.random.default_rng(0x44414E494C4F)
    for _ in range(samples):
        vector = generator.integers(0, 1 << B, size=W, dtype=np.uint32)
        if not np.array_equal(evaluate_circuit(circuit, vector), apply_mds_bitmatrix(vector)):
            return False
    return True


def export_dimacs(path: Path) -> None:
    circuit = build_mds_xor_circuit()
    clauses: list[tuple[int, int, int]] = []
    for left, right, output in circuit.gates:
        a, b, z = left + 1, right + 1, output + 1
        clauses.extend(((-a, -b, -z), (a, b, -z), (a, -b, z), (-a, b, z)))
    lines = [
        "c RSD-S MDS 512-bit XOR circuit",
        "c inputs " + " ".join(str(index + 1) for index in range(circuit.input_count)),
        "c outputs " + " ".join(str(index + 1) for index in circuit.outputs),
        f"p cnf {circuit.signal_count} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    circuit = build_mds_xor_circuit()
    print(f"equivalencia: {verify_circuit(32)}")
    print(f"XORs diretos: {circuit.direct_gate_count}")
    print(f"XORs sintetizados: {len(circuit.gates)}")
    reduction = 1 - len(circuit.gates) / circuit.direct_gate_count
    print(f"reducao: {reduction * 100:.2f}%")
