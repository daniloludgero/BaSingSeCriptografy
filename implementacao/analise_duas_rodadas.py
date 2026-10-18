"""Enumeração concreta e CNF da segunda camada diferencial da RSD-S."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mds_real import gf_inv
from rsd_round_cnf import CnfBuilder, _instantiate_inverse
from rsd_s_v4_final import (
    M_CAUCHY_32, W, _expand_key_words, derive_keys,
    gf_matrix_vector_mult, round_constant,
)

FIRST_ROUND_WITNESSES = (0, 1, 0x015E, 0x015F)
DEFAULT_KEY = bytes.fromhex("a5" * 32)
DEFAULT_SESSION = 7


@dataclass(frozen=True)
class TwoRoundTrail:
    witness: int
    round_two_input_weight: int
    round_two_max_transitions: int
    probability_log2: int
    round_two_output_weight: int
    second_sbox_difference: tuple[int, ...]
    left_round_two_input: tuple[int, ...]
    right_round_two_input: tuple[int, ...]


@dataclass(frozen=True)
class MultiRoundTrail:
    witness: int
    round_stats: tuple[tuple[int, int, int], ...]
    characteristic_log2_weight: int
    final_active_words: int


def _round_step(state: np.ndarray, key: bytes, session: int, index: int, key_words):
    rc = round_constant(key, session, index)
    after_sbox = np.array([gf_inv(int(value)) ^ rc for value in state], dtype=np.uint32)
    return gf_matrix_vector_mult(M_CAUCHY_32, after_sbox, W).astype(np.uint64) ^ key_words[index]


def analyze_witness(
    witness: int, key: bytes = DEFAULT_KEY, session: int = DEFAULT_SESSION
) -> TwoRoundTrail:
    if witness not in FIRST_ROUND_WITNESSES:
        raise ValueError("witness não pertence às quatro soluções DDT máximas")
    keys = derive_keys(key, session, 2)
    key_words = [_expand_key_words(item, W) for item in keys]
    left_raw = np.zeros(W, dtype=np.uint64)
    left_raw[0] = witness ^ int(key_words[0][0])
    right_raw = left_raw.copy()
    right_raw[0] ^= 1

    left_state = left_raw ^ key_words[0]
    right_state = right_raw ^ key_words[0]
    left_round_two = _round_step(left_state, key, session, 1, key_words)
    right_round_two = _round_step(right_state, key, session, 1, key_words)
    input_difference = left_round_two ^ right_round_two

    rc2 = round_constant(key, session, 2)
    left_after_sbox = np.array(
        [gf_inv(int(value)) ^ rc2 for value in left_round_two], dtype=np.uint32
    )
    right_after_sbox = np.array(
        [gf_inv(int(value)) ^ rc2 for value in right_round_two], dtype=np.uint32
    )
    output_difference = left_after_sbox ^ right_after_sbox
    active = int(np.count_nonzero(input_difference))
    maximum = sum(
        int(output_difference[index]) == gf_inv(int(input_difference[index]))
        for index in range(W)
    )
    # Primeira S-box: 2^-14. Segunda camada: 2^-14 ou 2^-15 por palavra.
    exponent = 14 + maximum * 14 + (active - maximum) * 15
    after_mds = gf_matrix_vector_mult(M_CAUCHY_32, output_difference, W)
    return TwoRoundTrail(
        witness, active, maximum, -exponent, int(np.count_nonzero(after_mds)),
        tuple(int(value) for value in output_difference),
        tuple(int(value) for value in left_round_two),
        tuple(int(value) for value in right_round_two),
    )


def analyze_all_witnesses() -> list[TwoRoundTrail]:
    return [analyze_witness(witness) for witness in FIRST_ROUND_WITNESSES]


def analyze_full_witness(
    witness: int, rounds: int = 4,
    key: bytes = DEFAULT_KEY, session: int = DEFAULT_SESSION,
) -> MultiRoundTrail:
    if witness not in FIRST_ROUND_WITNESSES:
        raise ValueError("witness inválida")
    keys = derive_keys(key, session, rounds)
    key_words = [_expand_key_words(item, W) for item in keys]
    left_raw = np.zeros(W, dtype=np.uint64)
    left_raw[0] = witness ^ int(key_words[0][0])
    right_raw = left_raw.copy()
    right_raw[0] ^= 1
    left = left_raw ^ key_words[0]
    right = right_raw ^ key_words[0]
    stats: list[tuple[int, int, int]] = []
    total_cost = 0
    for index in range(1, rounds + 1):
        input_difference = left ^ right
        left_inverse = np.array([gf_inv(int(value)) for value in left], dtype=np.uint32)
        right_inverse = np.array([gf_inv(int(value)) for value in right], dtype=np.uint32)
        output_difference = left_inverse ^ right_inverse
        active = int(np.count_nonzero(input_difference))
        maximum = sum(
            int(output_difference[word]) == gf_inv(int(input_difference[word]))
            for word in range(W) if int(input_difference[word]) != 0
        )
        cost = active * 15 - maximum
        stats.append((active, maximum, cost))
        total_cost += cost
        rc = round_constant(key, session, index)
        left = gf_matrix_vector_mult(M_CAUCHY_32, left_inverse ^ rc, W).astype(np.uint64) ^ key_words[index]
        right = gf_matrix_vector_mult(M_CAUCHY_32, right_inverse ^ rc, W).astype(np.uint64) ^ key_words[index]
    return MultiRoundTrail(
        witness, tuple(stats), -total_cost, int(np.count_nonzero(left ^ right))
    )


def _fix_word(builder: CnfBuilder, variables: list[int], value: int) -> None:
    assert builder.clauses is not None
    for bit, variable in enumerate(variables):
        builder.clauses.append((variable if value & (1 << bit) else -variable,))


def build_second_sbox_cnf(
    witness: int = 0, *, wrong_difference_bit: int | None = None
):
    trail = analyze_witness(witness)
    builder = CnfBuilder()
    differences: list[int] = []
    for word in range(W):
        left_input = builder.new_vars(16)
        right_input = builder.new_vars(16)
        _fix_word(builder, left_input, trail.left_round_two_input[word])
        _fix_word(builder, right_input, trail.right_round_two_input[word])
        left_inverse = _instantiate_inverse(builder, left_input)
        right_inverse = _instantiate_inverse(builder, right_input)
        for left_var, right_var in zip(left_inverse, right_inverse):
            difference = builder.new_var()
            builder.xor_gate(left_var, right_var, difference)
            differences.append(difference)

    target = list(trail.second_sbox_difference)
    if wrong_difference_bit is not None:
        target[wrong_difference_bit // 16] ^= 1 << (wrong_difference_bit % 16)
    assert builder.clauses is not None
    for index, variable in enumerate(differences):
        value = bool(target[index // 16] & (1 << (index % 16)))
        builder.clauses.append((variable if value else -variable,))
    return builder, trail


def export_dimacs(builder: CnfBuilder, trail: TwoRoundTrail, path: Path, wrong: bool) -> None:
    clauses = builder.clauses or []
    lines = [
        "c RSD-S concrete second-S-box-layer compatibility query",
        f"c first_round_witness {trail.witness}",
        f"c intentionally_wrong {str(wrong).lower()}",
        f"p cnf {builder.variable_count} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    for trail in analyze_all_witnesses():
        print(
            f"witness=0x{trail.witness:04x} active={trail.round_two_input_weight} "
            f"max={trail.round_two_max_transitions} probability=2^{trail.probability_log2} "
            f"out_active={trail.round_two_output_weight}"
        )
    root = Path(__file__).resolve().parents[1] / "ferramentas"
    sat_builder, trail = build_second_sbox_cnf(0)
    unsat_builder, _ = build_second_sbox_cnf(0, wrong_difference_bit=0)
    export_dimacs(sat_builder, trail, root / "rsd_diff_round2_layer_sat.cnf", False)
    export_dimacs(unsat_builder, trail, root / "rsd_diff_round2_layer_unsat.cnf", True)
    print(f"CNF: vars={sat_builder.variable_count}, clauses={len(sat_builder.clauses or [])}")
