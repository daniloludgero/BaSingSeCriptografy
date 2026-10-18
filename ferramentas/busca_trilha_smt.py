"""Busca SMT de trilha globalmente compatível sob chave fixa.

Modela duas execuções reais antes do SHA-256, incluindo inversão, constantes,
MDS e chaves de rodada. A consulta exige a transição DDT de contagem 4 em
toda S-box ativa. Profundidades altas podem retornar UNKNOWN por timeout.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "_vendor"))
sys.path.insert(0, str(ROOT / "implementacao"))

import z3  # type: ignore  # noqa: E402
from rsd_s_v4_final import (  # noqa: E402
    W,
    _expand_key_words,
    derive_keys,
    round_constant,
)
from mds_xor_synthesis import build_mds_xor_circuit  # noqa: E402
from mds_bitmatrix import mds_bit_rows  # noqa: E402
from mds_real import gf_inv  # noqa: E402

BITS = 16
REDUCTION = 0x100B


def bv(value: int):
    return z3.BitVecVal(value, BITS)


def xtime(value):
    shifted = value << 1
    return z3.If(z3.Extract(15, 15, value) == 1, shifted ^ bv(REDUCTION), shifted)


def gf_mul(left, right):
    result = bv(0)
    value = left
    multiplier = right
    for _ in range(BITS):
        result = result ^ z3.If((multiplier & bv(1)) == bv(1), value, bv(0))
        value = xtime(value)
        multiplier = z3.LShR(multiplier, 1)
    return result


def inverse(solver, value, name: str):
    result = z3.BitVec(name, BITS)
    solver.add(
        z3.Or(
            z3.And(value == bv(0), result == bv(0)),
            z3.And(value != bv(0), gf_mul(value, result) == bv(1)),
        )
    )
    return result


def xor_balanced(bits):
    level = list(bits)
    while len(level) > 1:
        following = [z3.Xor(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
        if len(level) % 2:
            following.append(level[-1])
        level = following
    return level[0] if level else z3.BoolVal(False)


def mds_vector_dense(solver, vector, prefix: str):
    outputs = [z3.BitVec(f"{prefix}_{word}", BITS) for word in range(W)]
    for output_index, sources in enumerate(mds_bit_rows()):
        bits = [
            z3.Extract(source % BITS, source % BITS, vector[source // BITS]) == 1
            for source in sources
        ]
        target = z3.Extract(
            output_index % BITS, output_index % BITS, outputs[output_index // BITS]
        ) == 1
        solver.add(target == xor_balanced(bits))
    return outputs


def mds_vector_synthesized(solver, vector, prefix: str):
    """Instancia a rede XOR sintetizada e compartilhada da MDS."""
    outputs = [z3.BitVec(f"{prefix}_{word}", BITS) for word in range(W)]
    circuit = build_mds_xor_circuit()
    signals = [None] * circuit.signal_count
    for source in range(circuit.input_count):
        signals[source] = (
            z3.Extract(source % BITS, source % BITS, vector[source // BITS]) == 1
        )
    for gate_index, (left, right, output) in enumerate(circuit.gates):
        gate = z3.Bool(f"{prefix}_xor_{gate_index}")
        solver.add(gate == z3.Xor(signals[left], signals[right]))
        signals[output] = gate
    for output_index, signal in enumerate(circuit.outputs):
        target = z3.Extract(
            output_index % BITS, output_index % BITS, outputs[output_index // BITS]
        ) == 1
        solver.add(target == signals[signal])
    return outputs


def mds_vector(solver, vector, prefix: str, mode: str):
    if mode == "dense":
        return mds_vector_dense(solver, vector, prefix)
    return mds_vector_synthesized(solver, vector, prefix)


def build(rounds: int, bit_position: int, timeout_ms: int, mds_mode: str = "dense"):
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    key = bytes.fromhex("a5" * 32)
    session = 7
    keys = derive_keys(key, session, rounds)
    key_words = [_expand_key_words(item, W) for item in keys]

    left = [z3.BitVec(f"state_0_{index}", BITS) for index in range(W)]
    delta = [0] * W
    delta[bit_position // BITS] = 1 << (bit_position % BITS)
    right = [left[index] ^ bv(delta[index]) for index in range(W)]

    # Garante que os estados antes do whitening representam x,y válidos (<2^255-19).
    for side in (left, right):
        raw = [side[index] ^ bv(int(key_words[0][index])) for index in range(W)]
        x_value = z3.Concat(*reversed(raw[:16]))
        y_value = z3.Concat(*reversed(raw[16:]))
        field_limit = z3.BitVecVal(2**255 - 19, 256)
        solver.add(z3.ULT(x_value, field_limit), z3.ULT(y_value, field_limit))

    weights = []
    for round_index in range(1, rounds + 1):
        differences = [z3.simplify(left[i] ^ right[i]) for i in range(W)]
        weights.append(z3.Sum([z3.If(item != bv(0), 1, 0) for item in differences]))
        inv_left = []
        inv_right = []
        for index, din in enumerate(differences):
            if (
                round_index == rounds
                and z3.is_bv_value(din)
                and din.as_long() == 0
            ):
                # Na última camada, uma S-box inativa não afeta nenhuma
                # restrição posterior e pode ser eliminada integralmente.
                inv_left.append(bv(0))
                inv_right.append(bv(0))
                continue
            left_inverse = inverse(solver, left[index], f"li_{round_index}_{index}")
            inv_left.append(left_inverse)
            if z3.is_bv_value(din) and din.as_long() == 0:
                # Mesma entrada implica a mesma inversa; não duplica o circuito.
                right_inverse = left_inverse
            else:
                right_inverse = inverse(solver, right[index], f"ri_{round_index}_{index}")
            inv_right.append(right_inverse)

            # Exige a transição local de probabilidade máxima: dout = inv(din).
            if z3.is_bv_value(din):
                expected = bv(gf_inv(din.as_long()))
            else:
                expected = inverse(solver, din, f"di_{round_index}_{index}")
            solver.add((left_inverse ^ right_inverse) == expected)

        if round_index < rounds:
            rc = bv(round_constant(key, session, round_index))
            left = mds_vector(
                solver, [item ^ rc for item in inv_left], f"lm_{round_index}", mds_mode
            )
            right = mds_vector(
                solver, [item ^ rc for item in inv_right], f"rm_{round_index}", mds_mode
            )
            left = [left[i] ^ bv(int(key_words[round_index][i])) for i in range(W)]
            right = [right[i] ^ bv(int(key_words[round_index][i])) for i in range(W)]
    return solver, weights


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=1, choices=(1, 2, 3, 4))
    parser.add_argument("--bit", type=int, default=0, choices=range(255))
    parser.add_argument("--timeout", type=int, default=120, help="segundos")
    parser.add_argument("--mds-mode", choices=("dense", "synthesized"), default="dense")
    args = parser.parse_args()

    started = time.perf_counter()
    solver, weights = build(args.rounds, args.bit, args.timeout * 1000, args.mds_mode)
    built = time.perf_counter() - started
    result = solver.check()
    elapsed = time.perf_counter() - started
    print(
        f"modelo: {args.rounds} rodada(s), bit {args.bit}, MDS {args.mds_mode}; "
        f"construcao {built:.2f}s"
    )
    print(f"resultado: {result}; tempo total {elapsed:.2f}s")
    if result == z3.sat:
        model = solver.model()
        print("pesos ativos:", [model.eval(weight).as_long() for weight in weights])
        return 0
    if result == z3.unknown:
        print("inconclusivo:", solver.reason_unknown())
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
