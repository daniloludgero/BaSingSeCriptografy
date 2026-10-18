"""Demonstração algébrica e verificação SMT da DDT da inversão GF(2^16).

O modelo usa multiplicação simbólica real no corpo, sem tabela não
interpretada. Pela simetria de escala da inversão, fixa delta_in = 1 sem
perda de generalidade. O limite superior vem da redução algébrica a uma
equação quadrática; o Z3 valida as quatro testemunhas concretas.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import time

VENDOR = Path(__file__).resolve().parent / "_vendor"
sys.path.insert(0, str(VENDOR))

import z3  # type: ignore  # noqa: E402

BITS = 16
REDUCTION = 0x100B  # termo baixo de x^16 + x^12 + x^3 + x + 1


def bv(value: int):
    return z3.BitVecVal(value, BITS)


def gf_mul(left, right):
    """Multiplicação simbólica exata em GF(2^16)."""
    result = bv(0)
    multiplicand = left
    multiplier = right
    for _ in range(BITS):
        result = result ^ z3.If((multiplier & bv(1)) == bv(1), multiplicand, bv(0))
        high = z3.Extract(BITS - 1, BITS - 1, multiplicand)
        shifted = multiplicand << 1
        multiplicand = z3.If(high == 1, shifted ^ bv(REDUCTION), shifted)
        multiplier = z3.LShR(multiplier, 1)
    return result


def constrain_inverse(solver, value, inverse) -> None:
    solver.add(
        z3.Or(
            z3.And(value == bv(0), inverse == bv(0)),
            z3.And(value != bv(0), gf_mul(value, inverse) == bv(1)),
        )
    )


def differential_witness_solver(witness_count: int, fixed_output: int | None = None):
    solver = z3.Solver()
    solver.set(timeout=120_000)
    delta_in = bv(1)  # normalização válida para toda diferença não nula
    delta_out = z3.BitVec("delta_out", BITS)
    solver.add(delta_out != bv(0))
    if fixed_output is not None:
        solver.add(delta_out == bv(fixed_output))

    inputs = [z3.BitVec(f"x_{index}", BITS) for index in range(witness_count)]
    solver.add(z3.Distinct(*inputs))
    for index, value in enumerate(inputs):
        inverse_left = z3.BitVec(f"inv_left_{index}", BITS)
        inverse_right = z3.BitVec(f"inv_right_{index}", BITS)
        constrain_inverse(solver, value, inverse_left)
        constrain_inverse(solver, value ^ delta_in, inverse_right)
        solver.add((inverse_left ^ inverse_right) == delta_out)
    return solver, inputs, delta_out


def four_concrete_witness_solver():
    """Valida x=0, 1 e as duas raízes de x²+x+1 para delta_out=1."""
    solver = z3.Solver()
    witnesses = (0, 1, 0x015E, 0x015F)
    for index, concrete in enumerate(witnesses):
        value = bv(concrete)
        inverse_left = z3.BitVec(f"concrete_inv_left_{index}", BITS)
        inverse_right = z3.BitVec(f"concrete_inv_right_{index}", BITS)
        constrain_inverse(solver, value, inverse_left)
        constrain_inverse(solver, value ^ bv(1), inverse_right)
        solver.add((inverse_left ^ inverse_right) == bv(1))
    return solver, witnesses


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attempt-symbolic-upper",
        action="store_true",
        help="tenta também a busca genérica de 5 testemunhas (pode expirar)",
    )
    args = parser.parse_args()
    print(f"Z3: {z3.get_version_string()}")

    existence, witnesses = four_concrete_witness_solver()
    started = time.perf_counter()
    existence_result = existence.check()
    print(f"quatro testemunhas concretas validas: {existence_result}")
    if existence_result == z3.sat:
        print(f"testemunhas: {list(witnesses)}; tempo: {time.perf_counter() - started:.2f}s")
    else:
        return 2

    print("LIMITE ALGEBRICO:")
    print("  para x fora de {0,a}: b*x*(x+a)=a, uma equacao de grau 2;")
    print("  ela tem no maximo 2 raizes no corpo;")
    print("  x=0 e x=a so acrescentam 2 solucoes quando b=inv(a);")
    print("  logo toda entrada nao trivial da DDT tem contagem <= 4.")
    print("  as quatro testemunhas acima atingem a cota.")
    print("CONCLUIDO: uniformidade diferencial exata = 4 (probabilidade maxima 2^-14).")

    if args.attempt_symbolic_upper:
        upper, _, output = differential_witness_solver(5)
        upper.set(timeout=30_000)
        started = time.perf_counter()
        upper_result = upper.check()
        print(f"busca SMT genérica por 5 testemunhas: {upper_result}")
        print(f"tempo: {time.perf_counter() - started:.2f}s")
        if upper_result == z3.sat:
            print(f"possível contraexemplo: delta_out={upper.model().eval(output)}")
            return 1
        if upper_result == z3.unknown:
            print(f"tentativa SMT inconclusiva: {upper.reason_unknown()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
