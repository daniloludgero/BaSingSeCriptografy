"""Propagação concreta de transições diferenciais máximas da RSD-S.

Para a inversão em GF(2^16), a transição de contagem 4 é
delta_out = inv(delta_in). Este módulo segue essas transições reais pela
matriz MDS, em vez de trabalhar apenas com pesos abstratos.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mds_real import gf_inv
from rsd_s_v4_final import M_CAUCHY_32, W, gf_matrix_vector_mult


@dataclass(frozen=True)
class ConcreteTrail:
    input_slot: int
    rounds: int
    active_weights: tuple[int, ...]

    @property
    def active_sboxes(self) -> int:
        return sum(self.active_weights)

    @property
    def differential_log2_probability(self) -> int:
        return -14 * self.active_sboxes


def maximum_probability_sbox_transition(delta: np.ndarray) -> np.ndarray:
    return np.array([gf_inv(int(word)) for word in delta], dtype=np.uint32)


def propagate_maximum_transitions(
    input_difference: np.ndarray, rounds: int
) -> tuple[int, ...]:
    if len(input_difference) != W:
        raise ValueError(f"a diferença deve conter {W} palavras")
    if rounds < 1:
        raise ValueError("rounds deve ser positivo")
    difference = input_difference.astype(np.uint32, copy=True)
    if not np.any(difference):
        raise ValueError("a diferença de entrada deve ser não nula")

    weights: list[int] = []
    for _ in range(rounds):
        weights.append(int(np.count_nonzero(difference)))
        after_sbox = maximum_probability_sbox_transition(difference)
        difference = gf_matrix_vector_mult(M_CAUCHY_32, after_sbox, W)
    return tuple(weights)


def analyze_single_active(rounds: int) -> list[ConcreteTrail]:
    trails: list[ConcreteTrail] = []
    for slot in range(W):
        difference = np.zeros(W, dtype=np.uint32)
        difference[slot] = 1
        trails.append(
            ConcreteTrail(slot, rounds, propagate_maximum_transitions(difference, rounds))
        )
    return trails


if __name__ == "__main__":
    print("rodadas | padrao concreto | S-boxes ativas | prob. caracteristica")
    for count in (4, 6, 8, 10):
        trails = analyze_single_active(count)
        patterns = {trail.active_weights for trail in trails}
        if len(patterns) != 1:
            raise RuntimeError(f"posições produziram padrões distintos: {patterns}")
        representative = trails[0]
        pattern = ",".join(map(str, representative.active_weights))
        print(
            f"{count:>7} | {pattern:<29} | {representative.active_sboxes:>15} | "
            f"2^{representative.differential_log2_probability}"
        )
