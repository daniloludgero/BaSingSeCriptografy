"""
suite_testes_completa.py

Suíte de testes reproduzível para o RSD-S v4 (versão final com as
três correções aplicadas). Roda:
  1. Verificação de propriedade MDS da matriz de difusão.
  2. Verificação de bijetividade da S-box.
  3. Teste de avalanche (critério de difusão estrita).
  4. Teste de ausência de linearidade residual básica.
  5. Teste de cobertura de bits (confirma que a fragmentação não
     descarta informação, ao contrário da v1 original).

Execute com: python3 suite_testes_completa.py
"""

from __future__ import annotations

import sys
import os
import secrets
import statistics
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "implementacao"))

import numpy as np
from mds_real import build_cauchy_mds, verify_mds_property
from rsd_s_v4_final import (
    diffuse_rsd_s_final, diffuse_rsd_s_final_PRE_SHA,
    get_base_inversion_sbox, M_CAUCHY_32, W,
)

P_CURVE25519 = 2**255 - 19


def hamming_bits_bytes(a: bytes, b: bytes) -> int:
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def hamming_state(s1, s2) -> int:
    return sum(bin(int(a) ^ int(b)).count("1") for a, b in zip(s1, s2))


def test_1_mds_property():
    print("=" * 70)
    print("TESTE 1 — Propriedade MDS da matriz de difusão (32x32)")
    print("=" * 70)
    result = verify_mds_property(M_CAUCHY_32, W, sample_minors=300)
    print(f"Rank da matriz: {result['full_matrix_rank']} de {result['expected_rank']}")
    print(f"Submatrizes singulares encontradas: {result['singular_submatrices_found']} "
          f"de {result['submatrices_tested']} testadas")
    passed = result["is_full_rank"] and result["singular_submatrices_found"] == 0
    print(f"RESULTADO: {'PASSOU' if passed else 'FALHOU'}")
    return passed


def test_2_sbox_bijection():
    print("\n" + "=" * 70)
    print("TESTE 2 — Bijetividade da S-box (inversão em GF(2^16))")
    print("=" * 70)
    sbox = get_base_inversion_sbox()
    unique_count = len(np.unique(sbox))
    print(f"Valores únicos: {unique_count} de 65536")
    passed = unique_count == 65536
    print(f"RESULTADO: {'PASSOU' if passed else 'FALHOU'}")
    return passed


def test_3_avalanche(n_trials: int = 40):
    print("\n" + "=" * 70)
    print("TESTE 3 — Efeito avalanche (critério de difusão estrita)")
    print("=" * 70)
    fractions = []
    for _ in range(n_trials):
        s = secrets.token_bytes(32)
        n_sess = secrets.randbits(63)
        x = secrets.randbits(255) % P_CURVE25519
        y = secrets.randbits(255) % P_CURVE25519

        z1 = diffuse_rsd_s_final(x, y, s, n_sess)
        bit_pos = secrets.randbelow(255)
        x_flip = x ^ (1 << bit_pos)
        z2 = diffuse_rsd_s_final(x_flip, y, s, n_sess)

        fractions.append(hamming_bits_bytes(z1, z2) / (len(z1) * 8))

    mean_f = statistics.mean(fractions)
    std_f = statistics.stdev(fractions)
    print(f"Difusão média: {mean_f*100:.2f}% (desvio {std_f*100:.2f}%), ideal ~50%")
    passed = 0.45 <= mean_f <= 0.55 and std_f < 0.10
    print(f"RESULTADO: {'PASSOU' if passed else 'FALHOU'}")
    return passed


def test_4_no_basic_linearity():
    print("\n" + "=" * 70)
    print("TESTE 4 — Ausência de linearidade básica (f(x1) XOR f(x2) vs f(x1 XOR x2))")
    print("=" * 70)
    s = secrets.token_bytes(32)
    n_sess = secrets.randbits(63)
    x1 = secrets.randbits(255) % P_CURVE25519
    x2 = secrets.randbits(255) % P_CURVE25519
    y = secrets.randbits(255) % P_CURVE25519

    out1 = diffuse_rsd_s_final_PRE_SHA(x1, y, s, n_sess)
    out2 = diffuse_rsd_s_final_PRE_SHA(x2, y, s, n_sess)
    out_xor_input = diffuse_rsd_s_final_PRE_SHA(x1 ^ x2, y, s, n_sess)

    out1_xor_out2 = np.array([int(a) ^ int(b) for a, b in zip(out1, out2)])
    is_linear = np.array_equal(out1_xor_out2, out_xor_input)

    print(f"f(x1) XOR f(x2) == f(x1 XOR x2)? {is_linear}")
    passed = not is_linear
    print(f"RESULTADO: {'PASSOU (não-linear, como esperado)' if passed else 'FALHOU (linearidade detectada!)'}")
    return passed


def test_5_full_bit_coverage():
    print("\n" + "=" * 70)
    print("TESTE 5 — Cobertura completa de bits (correção da v1, que descartava ~127 bits)")
    print("=" * 70)
    s = secrets.token_bytes(32)
    n_sess = secrets.randbits(63)
    x = secrets.randbits(255) % P_CURVE25519
    y = secrets.randbits(255) % P_CURVE25519

    z_original = diffuse_rsd_s_final(x, y, s, n_sess)

    # Testa bits em posições que a v1 original descartava (128-254)
    all_high_bits_matter = True
    for bit_pos in [128, 150, 180, 200, 230, 254]:
        x_flip = x ^ (1 << bit_pos)
        z_flip = diffuse_rsd_s_final(x_flip, y, s, n_sess)
        if z_flip == z_original:
            all_high_bits_matter = False
            print(f"  Bit {bit_pos}: NÃO afeta a saída (falha!)")
        else:
            print(f"  Bit {bit_pos}: afeta a saída corretamente")

    print(f"RESULTADO: {'PASSOU' if all_high_bits_matter else 'FALHOU'}")
    return all_high_bits_matter


if __name__ == "__main__":
    print("Pré-computando S-box de inversão (uma vez, ~5s)...")
    get_base_inversion_sbox()
    print()

    results = {
        "MDS da matriz de difusão": test_1_mds_property(),
        "Bijetividade da S-box": test_2_sbox_bijection(),
        "Efeito avalanche": test_3_avalanche(),
        "Ausência de linearidade básica": test_4_no_basic_linearity(),
        "Cobertura completa de bits": test_5_full_bit_coverage(),
    }

    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    for name, passed in results.items():
        status = "PASSOU" if passed else "FALHOU"
        print(f"  [{status}] {name}")

    all_passed = all(results.values())
    print(f"\nTodos os testes básicos passaram: {all_passed}")
    print("""
LEMBRETE IMPORTANTE: passar nestes testes é necessário, mas está longe
de ser suficiente para confiança criptográfica real. Não foram testados
aqui: criptoanálise diferencial/linear formal, ataques de chave
relacionada, ataques de canal lateral, ou qualquer prova de redução de
segurança a um problema difícil conhecido. Ver RELATORIO_FINAL.md.
""")
