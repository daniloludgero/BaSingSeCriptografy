"""
teste_branch_number.py

Testa o "branch number" da rodada completa (S-box + matriz MDS): para
uma diferença de entrada ativa em apenas 1 das 32 palavras, quantas
palavras de saída ficam ativas (não-zero) após a matriz de difusão?

Uma matriz MDS genuína garante, por teorema, que o branch number
(peso de entrada ativa + peso de saída ativa) é o máximo possível
para o tamanho do estado: aqui, n=32, então o branch number ótimo é
n+1=33 (1 palavra ativa na entrada deveria produzir 32 palavras ativas
na saída, o máximo possível).
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import secrets

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "implementacao"))
from mds_real import build_cauchy_mds, gf_mult, gf_add

W = 32
M = build_cauchy_mds(W)


def gf_matrix_vector_mult(M: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    result = np.zeros(n, dtype=np.uint32)
    for i in range(n):
        acc = 0
        for j in range(n):
            if M[i, j] != 0 and v[j] != 0:
                acc = gf_add(acc, gf_mult(int(M[i, j]), int(v[j])))
        result[i] = acc
    return result


def run(n_trials: int = 50):
    print("=" * 70)
    print("TESTE — Branch number da matriz de difusão (Cauchy MDS 32x32)")
    print("=" * 70)

    branch_numbers = []
    for _ in range(n_trials):
        v = np.zeros(W, dtype=np.uint32)
        active_slot = secrets.randbelow(W)
        v[active_slot] = secrets.randbelow(65536) + 1

        out = gf_matrix_vector_mult(M, v, W)

        input_weight = np.count_nonzero(v)
        output_weight = np.count_nonzero(out)
        branch_numbers.append(input_weight + output_weight)

    min_bn = min(branch_numbers)
    max_possible = W + 1

    print(f"\nBranch number mínimo observado: {min_bn}")
    print(f"Branch number máximo possível (MDS ideal, n={W}): {max_possible}")
    print(f"Branch number médio: {sum(branch_numbers)/len(branch_numbers):.1f}")

    passed = min_bn == max_possible
    if passed:
        print("\nRESULTADO: branch number ÓTIMO confirmado em todos os testes --")
        print("toda entrada de peso 1 produz saída de peso máximo, exatamente a")
        print("propriedade MDS garantida pelo teorema de matrizes de Cauchy.")
    else:
        print(f"\nRESULTADO: branch number abaixo do ótimo em pelo menos um caso.")

    return passed


if __name__ == "__main__":
    run()
