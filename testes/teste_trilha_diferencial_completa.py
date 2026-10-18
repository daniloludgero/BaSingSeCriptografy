"""
teste_trilha_diferencial_completa.py

Estima, empiricamente (via amostragem em larga escala, não prova
formal), a probabilidade de uma diferença de entrada específica levar
a uma diferença de saída específica APOS as 4 rodadas completas da
rede (S-box + matriz MDS + XOR de chave, repetido 4x).

Sob uma rede bem construída, a distribuição de diferenças de saída
deveria ser praticamente uniforme -- com milhares de amostras,
nenhuma diferença de saída específica deveria se repetir mais de
uma vez.
"""

from __future__ import annotations

import sys
from pathlib import Path
import secrets
import time
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "implementacao"))
from rsd_s_v4_final import diffuse_rsd_s_final_PRE_SHA, get_base_inversion_sbox

P = 2**255 - 19


def state_to_int(state) -> int:
    z = 0
    for i, v in enumerate(state):
        z |= int(v) << (i * 16)
    return z


def run_trail_search(
    n_samples: int = 2000,
    delta_in_bit: int = 0,
    *,
    s: bytes | None = None,
    n_sess: int | None = None,
):
    print("=" * 70)
    print(f"TESTE — Busca por trilha diferencial (delta_in = bit {delta_in_bit})")
    print("=" * 70)

    delta_in = 1 << delta_in_bit
    output_diffs: Counter = Counter()

    # Criptoanálise diferencial compara muitos pares sob a mesma chave.
    # Permitir injeção também torna o experimento integralmente reproduzível.
    fixed_s = s if s is not None else secrets.token_bytes(32)
    fixed_n_sess = n_sess if n_sess is not None else secrets.randbits(64)

    t0 = time.time()
    for i in range(n_samples):
        x = secrets.randbits(255) % P
        y = secrets.randbits(255) % P

        state1 = diffuse_rsd_s_final_PRE_SHA(x, y, fixed_s, fixed_n_sess)
        state2 = diffuse_rsd_s_final_PRE_SHA(x ^ delta_in, y, fixed_s, fixed_n_sess)

        delta_out = state_to_int(state1) ^ state_to_int(state2)
        output_diffs[delta_out] += 1

    elapsed = time.time() - t0

    most_common_diff, most_common_count = output_diffs.most_common(1)[0]
    total_unique = len(output_diffs)

    print(f"\n({n_samples} amostras, {elapsed:.1f}s)")
    print(f"Diferenças de saída únicas observadas: {total_unique} de {n_samples} amostras")
    print(f"Diferença de saída mais frequente ocorreu {most_common_count}x "
          f"(esperado ao acaso: ~1x, espaço de saída é de 2^512)")

    if most_common_count <= 2:
        print("RESULTADO: nenhuma repetição anormal -- consistente com boa difusão.")
    else:
        print(f"RESULTADO: repetição de {most_common_count}x -- merece investigação.")

    return most_common_count, total_unique


if __name__ == "__main__":
    print("Pré-computando S-box...")
    get_base_inversion_sbox()

    results = []
    for bit in [0, 64, 128, 200, 254]:
        count, unique = run_trail_search(n_samples=2000, delta_in_bit=bit)
        results.append((bit, count, unique))
        print()

    print("=" * 70)
    print("RESUMO — busca de trilha diferencial em múltiplas posições de bit")
    print("=" * 70)
    for bit, count, unique in results:
        print(f"  bit {bit:>4}: repeticao maxima = {count}x, "
              f"{unique} diferencas unicas de saida")
