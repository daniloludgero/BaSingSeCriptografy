"""
mds_real.py

Construção de uma matriz MDS genuína, usando a técnica clássica de
matriz de Cauchy sobre GF(2^16). Toda matriz de Cauchy sobre um corpo
finito é MDS por construção (todo menor é não-singular) -- este é um
resultado padrão da teoria de códigos, usado em construções reais
(ex: partes do design de Whirlpool e de algumas variantes de AES-like
permutations).

Isso corrige a falha encontrada na matriz M do documento anterior, que
tinha rank 5 de 16 (longe de invertível, muito menos MDS).
"""

from __future__ import annotations

import numpy as np


GF16_POLY = 0x1100B  # x^16 + x^12 + x^3 + x + 1 (polinômio primitivo padrão)
GF16_BITS = 16


def gf_mult(a: int, b: int, poly: int = GF16_POLY, bits: int = GF16_BITS) -> int:
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << bits):
            a ^= poly
    return result & ((1 << bits) - 1)


def gf_inv(a: int, poly: int = GF16_POLY, bits: int = GF16_BITS) -> int:
    if a == 0:
        return 0
    result = 1
    base = a
    exp = (1 << bits) - 2
    while exp:
        if exp & 1:
            result = gf_mult(result, base, poly, bits)
        base = gf_mult(base, base, poly, bits)
        exp >>= 1
    return result


def gf_add(a: int, b: int) -> int:
    return a ^ b  # adição em GF(2^n) é XOR


def build_cauchy_mds(n: int = 16) -> np.ndarray:
    """
    Constrói uma matriz de Cauchy n x n sobre GF(2^16):
        M[i][j] = 1 / (x_i XOR y_j)
    onde {x_i} e {y_j} são 2n elementos distintos de GF(2^16), com
    {x_i} disjunto de {y_j}. Essa construção garante MDS por teorema.
    """
    xs = list(range(n))          # 0, 1, ..., n-1
    ys = list(range(n, 2 * n))   # n, n+1, ..., 2n-1 (disjunto de xs)

    M = np.zeros((n, n), dtype=np.uint32)
    for i in range(n):
        for j in range(n):
            denom = gf_add(xs[i], ys[j])  # x_i XOR y_j, sempre != 0 (conjuntos disjuntos)
            M[i, j] = gf_inv(denom)
    return M


def verify_mds_property(M: np.ndarray, n: int, sample_minors: int = 200) -> dict:
    """
    Verifica a propriedade MDS de forma amostral: toda submatriz
    quadrada deveria ser invertível sobre GF(2^16). Testar TODOS os
    menores é caro (2^n combinações) -- amostramos submatrizes
    aleatórias de tamanhos variados e verificamos invertibilidade via
    eliminação gaussiana em GF(2^16).
    """
    import random

    def gf_matrix_rank(mat: np.ndarray, size: int) -> int:
        """Eliminação gaussiana em GF(2^16) para calcular rank."""
        mat = mat.copy().astype(np.int64)
        rank = 0
        for col in range(size):
            pivot_row = None
            for row in range(rank, size):
                if mat[row, col] != 0:
                    pivot_row = row
                    break
            if pivot_row is None:
                continue
            mat[[rank, pivot_row]] = mat[[pivot_row, rank]]
            pivot_val = mat[rank, col]
            pivot_inv = gf_inv(int(pivot_val))
            for row in range(size):
                if row != rank and mat[row, col] != 0:
                    factor = gf_mult(int(mat[row, col]), pivot_inv)
                    for k in range(col, size):
                        mat[row, k] ^= gf_mult(factor, int(mat[rank, k]))
            rank += 1
        return rank

    full_rank = gf_matrix_rank(M, n)

    singular_submatrices = 0
    tested = 0
    for _ in range(sample_minors):
        size = random.randint(2, n)
        rows = random.sample(range(n), size)
        cols = random.sample(range(n), size)
        sub = M[np.ix_(rows, cols)]
        r = gf_matrix_rank(sub, size)
        tested += 1
        if r < size:
            singular_submatrices += 1

    return {
        "full_matrix_rank": full_rank,
        "expected_rank": n,
        "is_full_rank": full_rank == n,
        "submatrices_tested": tested,
        "singular_submatrices_found": singular_submatrices,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Construção e verificação de matriz MDS via Cauchy sobre GF(2^16)")
    print("=" * 70)

    n = 16
    M = build_cauchy_mds(n)
    print(f"\nMatriz Cauchy MDS {n}x{n} construída (primeiras 3 linhas):")
    print(M[:3])

    result = verify_mds_property(M, n, sample_minors=300)
    print(f"\nRank da matriz completa: {result['full_matrix_rank']} de {result['expected_rank']}")
    print(f"Matriz é de rank completo: {result['is_full_rank']}")
    print(f"\nTeste amostral de menores (submatrizes quadradas):")
    print(f"  Submatrizes testadas: {result['submatrices_tested']}")
    print(f"  Submatrizes singulares encontradas: {result['singular_submatrices_found']}")
    print(f"\n(Para MDS verdadeiro, esperado: 0 submatrizes singulares -- toda")
    print(f"submatriz quadrada de uma matriz de Cauchy sobre corpo finito é")
    print(f"invertível por teorema, então 0 é o resultado matematicamente")
    print(f"garantido, não apenas empírico.)")

    # Comparação direta com a matriz do documento anterior
    print("\n" + "=" * 70)
    print("COMPARAÇÃO com a matriz M original do documento (H[i,j]=(i+1)(j+1)+(i^j))")
    print("=" * 70)
    W = 16
    MASK = (1 << 16) - 1
    H_original = np.zeros((W, W), dtype=np.uint64)
    for i in range(W):
        for j in range(W):
            H_original[i, j] = ((i + 1) * (j + 1) + (i ^ j)) & MASK
    rank_original = np.linalg.matrix_rank(H_original.astype(np.float64))
    print(f"\nMatriz original do documento: rank {rank_original} de {W} (NÃO invertível)")
    print(f"Matriz Cauchy MDS construída aqui: rank {result['full_matrix_rank']} de {W} "
          f"({'invertível, MDS' if result['is_full_rank'] else 'ainda problemática'})")
