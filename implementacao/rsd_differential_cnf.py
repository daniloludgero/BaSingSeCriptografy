"""Consulta diferencial CNF de duas execuções da primeira rodada RSD-S."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mds_real import gf_inv
from rsd_round_cnf import (
    CnfBuilder, _instantiate_inverse, _instantiate_mds,
    instantiate_fixed_first_round,
)
from rsd_s_v4_final import B, M_CAUCHY_32, W, gf_matrix_vector_mult


@dataclass(frozen=True)
class DifferentialCnf:
    builder: CnfBuilder
    left_inputs: tuple[int, ...]
    right_inputs: tuple[int, ...]
    left_outputs: tuple[int, ...]
    right_outputs: tuple[int, ...]
    input_bit: int
    expected_output_difference: tuple[int, ...]
    intentionally_wrong: bool


@dataclass(frozen=True)
class CompactDifferentialCnf:
    builder: CnfBuilder
    left_sbox_input: tuple[int, ...]
    right_sbox_input: tuple[int, ...]
    output_difference_vars: tuple[int, ...]
    input_difference: int
    intentionally_wrong: bool


def _constrain_difference(
    builder: CnfBuilder, left: tuple[int, ...] | list[int],
    right: tuple[int, ...] | list[int], difference_words
) -> None:
    for index, (left_var, right_var) in enumerate(zip(left, right)):
        word = index // B
        bit = index % B
        different = bool(int(difference_words[word]) & (1 << bit))
        builder.equivalence(right_var, left_var, inverted=different)


def build_max_transition_first_round(
    input_bit: int = 0,
    *,
    wrong_output_bit: int | None = None,
    key: bytes = bytes.fromhex("a5" * 32),
    session: int = 7,
    fix_inactive_words: bool = True,
) -> DifferentialCnf:
    if not 0 <= input_bit < W * B:
        raise ValueError("input_bit fora do estado de 512 bits")
    builder = CnfBuilder()
    left_inputs = builder.new_vars(W * B)
    right_inputs = builder.new_vars(W * B)

    input_difference = np.zeros(W, dtype=np.uint32)
    input_difference[input_bit // B] = 1 << (input_bit % B)
    _constrain_difference(builder, left_inputs, right_inputs, input_difference)

    # Subdomínio seguro: x,y < 2^254 nas duas execuções, portanto ambos < p.
    assert builder.clauses is not None
    for inputs in (left_inputs, right_inputs):
        builder.clauses.append((-inputs[254],))
        builder.clauses.append((-inputs[510],))

    if fix_inactive_words:
        active_word = input_bit // B
        for index, variable in enumerate(left_inputs):
            if index // B != active_word:
                builder.clauses.append((-variable,))

    left_trace = instantiate_fixed_first_round(builder, left_inputs, key, session)
    right_trace = instantiate_fixed_first_round(builder, right_inputs, key, session)

    # A transição DDT de contagem 4 é dout = inv(din).
    sbox_difference = np.zeros(W, dtype=np.uint32)
    active_word = input_bit // B
    active_value = 1 << (input_bit % B)
    sbox_difference[active_word] = gf_inv(active_value)
    _constrain_difference(
        builder, left_trace.after_inverse, right_trace.after_inverse, sbox_difference
    )

    output_difference = gf_matrix_vector_mult(
        M_CAUCHY_32, sbox_difference, W
    ).astype(np.uint32)
    intentionally_wrong = wrong_output_bit is not None
    if wrong_output_bit is not None:
        if not 0 <= wrong_output_bit < W * B:
            raise ValueError("wrong_output_bit fora do estado")
        output_difference[wrong_output_bit // B] ^= np.uint32(
            1 << (wrong_output_bit % B)
        )
    _constrain_difference(
        builder, left_trace.outputs, right_trace.outputs, output_difference
    )
    return DifferentialCnf(
        builder,
        tuple(left_inputs), tuple(right_inputs),
        left_trace.outputs, right_trace.outputs,
        input_bit, tuple(int(value) for value in output_difference), intentionally_wrong,
    )


def export_dimacs(model: DifferentialCnf, path: Path) -> None:
    clauses = model.builder.clauses or []
    lines = [
        "c RSD-S first-round two-execution differential query",
        f"c input_bit {model.input_bit}",
        f"c intentionally_wrong {str(model.intentionally_wrong).lower()}",
        "c domain restricted to x,y < 2^254",
        "c inactive input words fixed to zero",
        f"p cnf {model.builder.variable_count} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def build_compact_max_transition(
    input_difference: int = 1, *, wrong_output_bit: int | None = None
) -> CompactDifferentialCnf:
    if not 1 <= input_difference < (1 << B):
        raise ValueError("input_difference deve ser uma palavra não nula de 16 bits")
    builder = CnfBuilder()
    left = builder.new_vars(B)
    right = builder.new_vars(B)
    for bit, (left_var, right_var) in enumerate(zip(left, right)):
        builder.equivalence(
            right_var, left_var, inverted=bool(input_difference & (1 << bit))
        )

    left_inverse = _instantiate_inverse(builder, left)
    right_inverse = _instantiate_inverse(builder, right)
    difference_bits: list[int] = []
    for left_var, right_var in zip(left_inverse, right_inverse):
        output = builder.new_var()
        builder.xor_gate(left_var, right_var, output)
        difference_bits.append(output)

    expected_sbox_difference = gf_inv(input_difference)
    assert builder.clauses is not None
    for bit, variable in enumerate(difference_bits):
        value = bool(expected_sbox_difference & (1 << bit))
        builder.clauses.append((variable if value else -variable,))

    false_var = builder.new_var()
    builder.clauses.append((-false_var,))
    mds_input = difference_bits + [false_var] * (W * B - B)
    output_vars = _instantiate_mds(builder, mds_input)

    input_words = np.zeros(W, dtype=np.uint32)
    input_words[0] = expected_sbox_difference
    expected_output = gf_matrix_vector_mult(M_CAUCHY_32, input_words, W)
    intentionally_wrong = wrong_output_bit is not None
    if wrong_output_bit is not None:
        expected_output[wrong_output_bit // B] ^= np.uint32(1 << (wrong_output_bit % B))
    for index, variable in enumerate(output_vars):
        value = bool(int(expected_output[index // B]) & (1 << (index % B)))
        builder.clauses.append((variable if value else -variable,))
    return CompactDifferentialCnf(
        builder, tuple(left), tuple(right), tuple(output_vars),
        input_difference, intentionally_wrong,
    )


def export_compact_dimacs(model: CompactDifferentialCnf, path: Path) -> None:
    clauses = model.builder.clauses or []
    lines = [
        "c RSD-S compact exact first-round differential query",
        f"c input_difference {model.input_difference}",
        f"c intentionally_wrong {str(model.intentionally_wrong).lower()}",
        "c round constants and keys cancel in XOR difference",
        f"p cnf {model.builder.variable_count} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    sat_model = build_max_transition_first_round(0)
    unsat_model = build_max_transition_first_round(0, wrong_output_bit=0)
    export_dimacs(sat_model, root / "ferramentas" / "rsd_diff_round1_sat.cnf")
    export_dimacs(unsat_model, root / "ferramentas" / "rsd_diff_round1_unsat.cnf")
    compact_sat = build_compact_max_transition(1)
    compact_unsat = build_compact_max_transition(1, wrong_output_bit=0)
    export_compact_dimacs(
        compact_sat, root / "ferramentas" / "rsd_diff_round1_compact_sat.cnf"
    )
    export_compact_dimacs(
        compact_unsat, root / "ferramentas" / "rsd_diff_round1_compact_unsat.cnf"
    )
    print(f"SAT: vars={sat_model.builder.variable_count}, clauses={len(sat_model.builder.clauses or [])}")
    print(f"UNSAT controle: vars={unsat_model.builder.variable_count}, clauses={len(unsat_model.builder.clauses or [])}")
    print(f"Compacta SAT: vars={compact_sat.builder.variable_count}, clauses={len(compact_sat.builder.clauses or [])}")
