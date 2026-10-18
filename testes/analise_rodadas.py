"""Compara avalanche e custo das variantes experimentais de rodadas."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "implementacao"))

from analise_wide_trail import bound_for_rounds  # noqa: E402
from rsd_s_v4_final import (  # noqa: E402
    diffuse_rsd_s_rounds_PRE_SHA,
    get_base_inversion_sbox,
)


def hamming_distance(a: bytes, b: bytes) -> int:
    return sum((left ^ right).bit_count() for left, right in zip(a, b))


def hamming_state(left, right) -> int:
    return sum((int(a) ^ int(b)).bit_count() for a, b in zip(left, right))


def hash_state(state) -> bytes:
    encoded = b"".join(int(word).to_bytes(2, "big") for word in state)
    return sha256(encoded).digest()


def deterministic_input(index: int) -> tuple[int, int]:
    x = int.from_bytes(sha256(f"x:{index}".encode()).digest(), "big") >> 2
    y = int.from_bytes(sha256(f"y:{index}".encode()).digest(), "big") >> 2
    return x, y


def measure(rounds: int, trials: int) -> dict[str, float | int]:
    key = bytes.fromhex("a5" * 32)
    session = 0x0123456789ABCDEF
    pre_sha_fractions: list[float] = []
    post_sha_fractions: list[float] = []
    positions = (0, 63, 127, 128, 191, 254)

    pair_durations: list[float] = []
    for trial in range(trials):
        x, y = deterministic_input(trial)
        bit = positions[trial % len(positions)]
        started = time.perf_counter()
        base_state = diffuse_rsd_s_rounds_PRE_SHA(x, y, key, session, rounds)
        changed_state = diffuse_rsd_s_rounds_PRE_SHA(
            x ^ (1 << bit), y, key, session, rounds
        )
        pair_durations.append(time.perf_counter() - started)
        pre_sha_fractions.append(hamming_state(base_state, changed_state) / 512)
        post_sha_fractions.append(
            hamming_distance(hash_state(base_state), hash_state(changed_state)) / 256
        )
    bound = bound_for_rounds(rounds)
    return {
        "rounds": rounds,
        "trials": trials,
        "pre_sha_avalanche_mean": statistics.mean(pre_sha_fractions),
        "pre_sha_avalanche_stdev": statistics.stdev(pre_sha_fractions),
        "post_sha_avalanche_mean": statistics.mean(post_sha_fractions),
        "post_sha_avalanche_stdev": statistics.stdev(post_sha_fractions),
        "milliseconds_per_call": statistics.median(pair_durations) * 1000 / 2,
        "min_active_sboxes": bound.min_active_sboxes,
        "differential_log2_bound": bound.differential_log2_probability_upper,
        "linear_log2_correlation_bound": bound.linear_log2_correlation_upper,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--rounds", type=int, nargs="+", default=[4, 6, 8, 10])
    args = parser.parse_args()
    if args.trials < 2:
        parser.error("--trials deve ser pelo menos 2")

    get_base_inversion_sbox()
    print(
        "rodadas | pre-SHA (desvio) | pos-SHA (desvio) | ms/chamada | ativas min. | "
        "limite diferencial"
    )
    for rounds in args.rounds:
        result = measure(rounds, args.trials)
        print(
            f"{rounds:>7} | {result['pre_sha_avalanche_mean'] * 100:>6.2f}% "
            f"({result['pre_sha_avalanche_stdev'] * 100:>5.2f}%) | "
            f"{result['post_sha_avalanche_mean'] * 100:>6.2f}% "
            f"({result['post_sha_avalanche_stdev'] * 100:>5.2f}%) | "
            f"{result['milliseconds_per_call']:>10.2f} | "
            f"{result['min_active_sboxes']:>11} | "
            f"2^{result['differential_log2_bound']}"
        )


if __name__ == "__main__":
    main()
