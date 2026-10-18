"""Limites conservadores de trilhas para a estrutura SPN da RSD-S.

Esta análise trata características individuais. Ela não soma todas as
trilhas que podem contribuir para um mesmo diferencial ou aproximação.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

WORD_BITS = 16
STATE_WORDS = 32
MDS_BRANCH_NUMBER = STATE_WORDS + 1
INVERSION_DDT_MAX_COUNT = 4
INVERSION_WALSH_MAX_ABS = 512


@dataclass(frozen=True)
class WideTrailBound:
    rounds: int
    min_active_sboxes: int
    differential_log2_probability_upper: int
    linear_log2_correlation_upper: int
    linear_log2_bias_upper: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


def min_active_sboxes(rounds: int) -> int:
    """Limite inferior derivado do branch number para uma trilha não nula.

    Como a S-box é bijetiva, uma diferença de palavra ativa continua ativa
    após a S-box. Para cada par de rodadas adjacentes, a MDS garante
    wt(entrada) + wt(saída) >= 33. Agrupar pares disjuntos produz o limite.
    """
    if isinstance(rounds, bool) or not isinstance(rounds, int):
        raise TypeError("rounds deve ser um inteiro")
    if rounds < 1:
        raise ValueError("rounds deve ser positivo")
    return (rounds // 2) * MDS_BRANCH_NUMBER + (rounds % 2)


def min_active_sboxes_dp(rounds: int) -> tuple[int, tuple[int, ...]]:
    """Resolve exatamente a relaxação por pesos de palavra.

    Cada peso de rodada está em [1, 32] e todo par adjacente deve somar
    pelo menos 33. O resultado serve como verificação computacional
    independente da fórmula fechada, mas não modela valores diferenciais.
    """
    min_active_sboxes(rounds)  # reutiliza a validação do argumento
    costs = {weight: (weight, (weight,)) for weight in range(1, STATE_WORDS + 1)}
    for _ in range(1, rounds):
        next_costs: dict[int, tuple[int, tuple[int, ...]]] = {}
        for current in range(1, STATE_WORDS + 1):
            candidates = (
                (cost + current, pattern + (current,))
                for previous, (cost, pattern) in costs.items()
                if previous + current >= MDS_BRANCH_NUMBER
            )
            next_costs[current] = min(candidates)
        costs = next_costs
    return min(costs.values())


def bound_for_rounds(rounds: int) -> WideTrailBound:
    active = min_active_sboxes(rounds)
    differential_cost = WORD_BITS - int(math.log2(INVERSION_DDT_MAX_COUNT))
    correlation_cost = int(
        math.log2((1 << WORD_BITS) / INVERSION_WALSH_MAX_ABS)
    )
    return WideTrailBound(
        rounds=rounds,
        min_active_sboxes=active,
        differential_log2_probability_upper=-(differential_cost * active),
        linear_log2_correlation_upper=-(correlation_cost * active),
        linear_log2_bias_upper=-(correlation_cost * active + 1),
    )


def comparison(round_counts: tuple[int, ...] = (4, 6, 8, 10)) -> list[WideTrailBound]:
    return [bound_for_rounds(rounds) for rounds in round_counts]


if __name__ == "__main__":
    print(
        "rodadas | S-boxes ativas | padrao de pesos | limite diferencial | "
        "limite correlacao linear"
    )
    for item in comparison():
        _, pattern = min_active_sboxes_dp(item.rounds)
        print(
            f"{item.rounds:>7} | {item.min_active_sboxes:>15} | "
            f"{','.join(map(str, pattern)):<24} | "
            f"2^{item.differential_log2_probability_upper:<17} | "
            f"2^{item.linear_log2_correlation_upper}"
        )
