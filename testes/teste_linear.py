"""
teste_linear.py

Criptoanálise linear real: constrói a TABELA DE APROXIMAÇÃO LINEAR
(LAT) da S-box. Para cada máscara de entrada `a` e máscara de saída
`b`, mede o VIÉS da aproximação linear:

    Pr[ a·x == b·S(x) ] - 1/2

sobre todo x em [0, 2^16). Uma S-box "boa" tem viés máximo (excluindo
a=0, b=0) próximo do mínimo teórico -- para S-box de inversão em
GF(2^n), a cota conhecida (Nyberg 1993) é da ordem de 2^(-n/2).

Isso é o teste padrão que qualquer S-box nova precisa passar antes de
qualquer consideração séria -- é o mesmo tipo de tabela calculada e
publicada para a S-box do AES.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import time
import secrets

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "implementacao"))
from rsd_s_v4_final import get_base_inversion_sbox


def popcount(x: int) -> int:
    return bin(x).count("1")


def linear_bias(sbox: np.ndarray, mask_in: int, mask_out: int, bits: int = 16) -> float:
    """Calcula o viés |Pr[a.x = b.S(x)] - 1/2| para máscaras fixas, exaustivo sobre 2^16."""
    size = 1 << bits
    count = 0
    for x in range(size):
        a_dot_x = popcount(x & mask_in) & 1
        b_dot_sx = popcount(int(sbox[x]) & mask_out) & 1
        if a_dot_x == b_dot_sx:
            count += 1
    prob = count / size
    return abs(prob - 0.5)


def run(n_mask_samples: int = 300):
    print("=" * 70)
    print("TESTE — Criptoanálise linear da S-box (viés de aproximação linear)")
    print("=" * 70)

    sbox = get_base_inversion_sbox()
    bits = 16

    print(f"\nTestando {n_mask_samples} pares aleatórios de máscaras (a, b),")
    print("cada teste exaustivo sobre as 65536 entradas...")

    max_bias = 0.0
    max_pair = None

    t0 = time.time()
    # Sempre inclui máscaras de 1 bit (mais relevantes), completa com aleatórias
    masks_to_test = []
    for i in range(bits):
        for j in range(bits):
            masks_to_test.append((1 << i, 1 << j))
    for _ in range(n_mask_samples):
        masks_to_test.append((secrets.randbelow(1 << bits), secrets.randbelow(1 << bits)))

    for mask_in, mask_out in masks_to_test:
        if mask_in == 0 or mask_out == 0:
            continue
        bias = linear_bias(sbox, mask_in, mask_out, bits)
        if bias > max_bias:
            max_bias = bias
            max_pair = (mask_in, mask_out)

    elapsed = time.time() - t0

    theoretical_bound = 2 ** (-bits / 2) / 2  # cota aproximada de Nyberg para inversão

    print(f"\nConcluído em {elapsed:.1f}s ({len(masks_to_test)} pares de máscaras testados)")
    print(f"\nViés linear MÁXIMO encontrado: {max_bias:.6f}")
    print(f"  (máscaras a={max_pair[0]}, b={max_pair[1]})")
    print(f"Cota teórica aproximada esperada (Nyberg, S-box de inversão): ~{theoretical_bound:.6f}")

    ratio = max_bias / theoretical_bound if theoretical_bound > 0 else float("inf")
    print(f"Razão (encontrado / esperado): {ratio:.2f}x")

    if ratio < 10:
        print("\nRESULTADO: viés linear na faixa esperada para S-box de inversão.")
    else:
        print("\nRESULTADO: viés mais alto que o esperado -- possível fraqueza linear.")


if __name__ == "__main__":
    run(n_mask_samples=300)
