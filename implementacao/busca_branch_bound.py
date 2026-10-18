"""Busca diferencial amostral com filtragem branch-and-bound para a RSD-S."""

from __future__ import annotations

from dataclasses import dataclass
import random

import numpy as np

from mds_real import gf_mult
from rsd_s_v4_final import (
    M_CAUCHY_32, P_CURVE25519, W, _expand_key_words, derive_keys,
    get_base_inversion_sbox, gf_matrix_vector_mult, round_constant,
)

DEFAULT_KEY = bytes.fromhex("a5" * 32)
DEFAULT_SESSION = 7
OMEGA = 0x015E
OMEGA_PLUS_ONE = 0x015F


@dataclass(frozen=True)
class Candidate:
    slot: int
    delta: int
    witness: int
    two_round_cost: int
    round_two_max: int
    left_round_two: tuple[int, ...]
    right_round_two: tuple[int, ...]
    background_id: int = 0
    first_transition_count: int = 4


@dataclass(frozen=True)
class SearchResult:
    slot: int
    delta: int
    witness: int
    round_stats: tuple[tuple[int, int, int], ...]
    total_cost: int
    final_active_words: int
    background_id: int = 0
    first_transition_count: int = 4


def maximum_transition_witnesses(delta: int) -> tuple[int, int, int, int]:
    if not 1 <= delta < (1 << 16):
        raise ValueError("delta deve ser uma palavra não nula de 16 bits")
    return (0, delta, gf_mult(delta, OMEGA), gf_mult(delta, OMEGA_PLUS_ONE))


def deterministic_deltas(random_count: int = 48, seed: int = 0x44414E494C4F):
    values = {1 << bit for bit in range(16)}
    generator = random.Random(seed)
    while len(values) < 16 + random_count:
        values.add(generator.randrange(1, 1 << 16))
    return tuple(sorted(values))


def _words_to_field(words: tuple[int, ...] | list[int], offset: int) -> int:
    return sum(int(words[offset + index]) << (16 * index) for index in range(16))


def _raw_pair_is_valid(
    background_words: tuple[int, ...], slot: int, raw_value: int, delta: int
) -> bool:
    left_words = list(background_words)
    right_words = list(background_words)
    left_words[slot] = raw_value
    right_words[slot] = raw_value ^ delta
    return all(
        value < P_CURVE25519
        for value in (
            _words_to_field(left_words, 0), _words_to_field(left_words, 16),
            _words_to_field(right_words, 0), _words_to_field(right_words, 16),
        )
    )


class TwoRoundEvaluator:
    def __init__(
        self,
        key: bytes = DEFAULT_KEY,
        session: int = DEFAULT_SESSION,
        background_words: tuple[int, ...] | None = None,
        background_id: int = 0,
    ):
        self.key = key
        self.session = session
        self.background_words = background_words or (0,) * W
        if len(self.background_words) != W:
            raise ValueError("o fundo deve conter exatamente 32 palavras")
        if any(not 0 <= int(value) < (1 << 16) for value in self.background_words):
            raise ValueError("cada palavra do fundo deve ter 16 bits")
        if any(
            _words_to_field(self.background_words, offset) >= P_CURVE25519
            for offset in (0, 16)
        ):
            raise ValueError("o fundo deve representar dois elementos de F_p")
        self.background_id = background_id
        keys = derive_keys(key, session, 4)
        self.key_words = [_expand_key_words(item, W) for item in keys]
        self.sbox = get_base_inversion_sbox()
        rc1 = round_constant(key, session, 1)
        prewhite = np.array(self.background_words, dtype=np.uint64) ^ self.key_words[0]
        self.baseline_after_sbox = np.array(
            [int(self.sbox[int(value)]) ^ rc1 for value in prewhite],
            dtype=np.uint32,
        )
        self.baseline_round_two = (
            gf_matrix_vector_mult(M_CAUCHY_32, self.baseline_after_sbox, W).astype(np.uint64)
            ^ self.key_words[1]
        )

    def _modify_baseline(self, slot: int, sbox_input: int) -> np.ndarray:
        rc1 = round_constant(self.key, self.session, 1)
        replacement = int(self.sbox[sbox_input]) ^ rc1
        change = replacement ^ int(self.baseline_after_sbox[slot])
        state = self.baseline_round_two.copy()
        if change:
            for row in range(W):
                state[row] ^= gf_mult(int(M_CAUCHY_32[row, slot]), change)
        return state

    def candidate(
        self, slot: int, delta: int, witness: int, first_transition_count: int = 4
    ) -> Candidate | None:
        if first_transition_count not in (2, 4):
            raise ValueError("a contagem DDT inicial deve ser 2 ou 4")
        raw_value = witness ^ int(self.key_words[0][slot])
        if not _raw_pair_is_valid(self.background_words, slot, raw_value, delta):
            return None
        left = self._modify_baseline(slot, witness)
        right = self._modify_baseline(slot, witness ^ delta)
        difference = left ^ right
        left_output = self.sbox[left.astype(np.uint32)]
        right_output = self.sbox[right.astype(np.uint32)]
        output_difference = left_output ^ right_output
        active = int(np.count_nonzero(difference))
        maximum = sum(
            int(output_difference[index]) == int(self.sbox[int(difference[index])])
            for index in range(W) if int(difference[index]) != 0
        )
        first_cost = 16 - (first_transition_count.bit_length() - 1)
        cost = first_cost + active * 15 - maximum
        return Candidate(
            slot, delta, witness, cost, maximum,
            tuple(int(value) for value in left), tuple(int(value) for value in right),
            self.background_id, first_transition_count,
        )


def expand_candidate(
    candidate: Candidate, evaluator: TwoRoundEvaluator
) -> SearchResult:
    left = np.array(candidate.left_round_two, dtype=np.uint64)
    right = np.array(candidate.right_round_two, dtype=np.uint64)
    first_cost = 16 - (candidate.first_transition_count.bit_length() - 1)
    first_maximum = int(candidate.first_transition_count == 4)
    stats: list[tuple[int, int, int]] = [(1, first_maximum, first_cost)]
    total = first_cost
    for round_index in range(2, 5):
        input_difference = left ^ right
        left_inverse = evaluator.sbox[left.astype(np.uint32)]
        right_inverse = evaluator.sbox[right.astype(np.uint32)]
        output_difference = left_inverse ^ right_inverse
        active = int(np.count_nonzero(input_difference))
        maximum = sum(
            int(output_difference[index]) == int(evaluator.sbox[int(input_difference[index])])
            for index in range(W) if int(input_difference[index]) != 0
        )
        cost = active * 15 - maximum
        stats.append((active, maximum, cost))
        total += cost
        rc = round_constant(evaluator.key, evaluator.session, round_index)
        left = (
            gf_matrix_vector_mult(M_CAUCHY_32, left_inverse ^ rc, W).astype(np.uint64)
            ^ evaluator.key_words[round_index]
        )
        right = (
            gf_matrix_vector_mult(M_CAUCHY_32, right_inverse ^ rc, W).astype(np.uint64)
            ^ evaluator.key_words[round_index]
        )
    return SearchResult(
        candidate.slot, candidate.delta, candidate.witness,
        tuple(stats), total, int(np.count_nonzero(left ^ right)),
        candidate.background_id, candidate.first_transition_count,
    )


def search(
    deltas: tuple[int, ...] | None = None,
    positions: tuple[int, ...] = tuple(range(W)),
    beam_per_position: int = 8,
) -> tuple[list[SearchResult], int]:
    selected_deltas = deltas or deterministic_deltas()
    evaluator = TwoRoundEvaluator()
    finalists: list[Candidate] = []
    evaluated = 0
    for slot in positions:
        local: list[Candidate] = []
        for delta in selected_deltas:
            for witness in maximum_transition_witnesses(delta):
                candidate = evaluator.candidate(slot, delta, witness)
                if candidate is not None:
                    local.append(candidate)
                    evaluated += 1
        local.sort(key=lambda item: (item.two_round_cost, -item.round_two_max, item.delta, item.witness))
        finalists.extend(local[:beam_per_position])
    results = [expand_candidate(candidate, evaluator) for candidate in finalists]
    results.sort(key=lambda item: (item.total_cost, item.slot, item.delta, item.witness))
    return results, evaluated


if __name__ == "__main__":
    results, evaluated = search()
    print(f"candidatos avaliados ate 2 rodadas: {evaluated}")
    print(f"finalistas propagados por 4 rodadas: {len(results)}")
    for item in results[:10]:
        print(
            f"cost={item.total_cost} slot={item.slot} delta=0x{item.delta:04x} "
            f"witness=0x{item.witness:04x} stats={item.round_stats} "
            f"final_active={item.final_active_words}"
        )
