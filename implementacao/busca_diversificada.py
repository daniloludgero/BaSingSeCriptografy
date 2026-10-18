"""Busca diferencial amostral com fundos e classes DDT diversificados."""

from __future__ import annotations

import random

from busca_branch_bound import (
    Candidate,
    SearchResult,
    TwoRoundEvaluator,
    deterministic_deltas,
    expand_candidate,
    maximum_transition_witnesses,
)
from rsd_s_v4_final import P_CURVE25519, W, get_base_inversion_sbox


def count_two_transition_witnesses(
    delta: int,
    limit: int = 4,
    seed: int = 0x4849454D414E4E,
) -> tuple[int, ...]:
    """Obtém testemunhas canônicas de transições DDT com contagem exatamente 2."""
    if not 1 <= delta < (1 << 16):
        raise ValueError("delta deve ser uma palavra não nula de 16 bits")
    if not 0 <= limit <= 32766:
        raise ValueError("limit deve estar entre 0 e 32766")
    sbox = get_base_inversion_sbox()
    maximum_output = int(sbox[delta])
    generator = random.Random(seed ^ delta)
    witnesses: list[int] = []
    seen_outputs: set[int] = set()
    while len(witnesses) < limit:
        value = generator.randrange(1 << 16)
        canonical = min(value, value ^ delta)
        output_delta = int(sbox[canonical]) ^ int(sbox[canonical ^ delta])
        if output_delta == maximum_output or output_delta in seen_outputs:
            continue
        seen_outputs.add(output_delta)
        witnesses.append(canonical)
    return tuple(witnesses)


def _words_to_field(words: tuple[int, ...], offset: int) -> int:
    return sum(words[offset + index] << (16 * index) for index in range(16))


def deterministic_backgrounds(
    count: int = 4,
    seed: int = 0x44414E494C4F,
) -> tuple[tuple[int, ...], ...]:
    """Cria fundos reproduzíveis; o primeiro é zero e todos pertencem a F_p²."""
    if count < 1:
        raise ValueError("count deve ser positivo")
    generator = random.Random(seed)
    backgrounds: list[tuple[int, ...]] = [(0,) * W]
    while len(backgrounds) < count:
        words = [generator.randrange(1 << 16) for _ in range(W)]
        # Cada metade fica abaixo de 2^254, logo estritamente abaixo de p.
        words[15] &= 0x3FFF
        words[31] &= 0x3FFF
        background = tuple(words)
        if background not in backgrounds:
            backgrounds.append(background)
    assert all(
        _words_to_field(background, offset) < P_CURVE25519
        for background in backgrounds for offset in (0, 16)
    )
    return tuple(backgrounds)


def search_diversified(
    deltas: tuple[int, ...] | None = None,
    positions: tuple[int, ...] = tuple(range(W)),
    backgrounds: tuple[tuple[int, ...], ...] | None = None,
    count_two_per_delta: int = 4,
    beam_per_background_position: int = 8,
) -> tuple[list[SearchResult], int]:
    """Filtra em duas rodadas e expande os melhores candidatos até quatro."""
    selected_deltas = deltas or deterministic_deltas(random_count=16)
    selected_backgrounds = backgrounds or deterministic_backgrounds()
    transition_sets = {
        delta: (
            tuple((witness, 4) for witness in maximum_transition_witnesses(delta))
            + tuple(
                (witness, 2)
                for witness in count_two_transition_witnesses(
                    delta, limit=count_two_per_delta
                )
            )
        )
        for delta in selected_deltas
    }
    finalists: list[tuple[Candidate, TwoRoundEvaluator]] = []
    evaluated = 0
    for background_id, background in enumerate(selected_backgrounds):
        evaluator = TwoRoundEvaluator(
            background_words=background, background_id=background_id
        )
        for slot in positions:
            local: list[Candidate] = []
            for delta in selected_deltas:
                for witness, transition_count in transition_sets[delta]:
                    candidate = evaluator.candidate(
                        slot, delta, witness,
                        first_transition_count=transition_count,
                    )
                    if candidate is not None:
                        local.append(candidate)
                        evaluated += 1
            local.sort(
                key=lambda item: (
                    item.two_round_cost,
                    -item.round_two_max,
                    -item.first_transition_count,
                    item.delta,
                    item.witness,
                )
            )
            finalists.extend(
                (candidate, evaluator)
                for candidate in local[:beam_per_background_position]
            )
    results = [
        expand_candidate(candidate, evaluator)
        for candidate, evaluator in finalists
    ]
    results.sort(
        key=lambda item: (
            item.total_cost, item.background_id, item.slot,
            item.delta, item.witness,
        )
    )
    return results, evaluated


if __name__ == "__main__":
    results, evaluated = search_diversified()
    print(f"candidatos válidos avaliados até 2 rodadas: {evaluated}")
    print(f"finalistas propagados por 4 rodadas: {len(results)}")
    for item in results[:10]:
        print(
            f"cost={item.total_cost} background={item.background_id} "
            f"slot={item.slot} delta=0x{item.delta:04x} "
            f"witness=0x{item.witness:04x} count={item.first_transition_count} "
            f"stats={item.round_stats} final_active={item.final_active_words}"
        )
