"""
teste_avalanche_rsd_s.py

Testa o critério de avalanche (Seção 5.3 do documento anterior, mesmo
critério se aplica aqui) na implementação COMPLETA do RSD-S, que agora
inclui S-boxes não-lineares -- a correção estrutural mais importante
em relação à versão anterior (RSD puro, que era inteiramente linear).

A pergunta que este teste responde: mesmo com a matriz MDS
comprovadamente degenerada (rank 5 de 16, ver investigação anterior),
as S-boxes não-lineares sozinhas conseguem compensar e ainda produzir
avalanche aceitável?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "implementacao"))
import secrets
import statistics
from rsd_s_v1_original import diffuse_rsd_s


def hamming_distance_bits(a: bytes, b: bytes) -> int:
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def run_avalanche_test(n_trials: int = 30):
    print("=" * 70)
    print("TESTE — Efeito avalanche na implementação RSD-S completa")
    print("(com S-boxes não-lineares + matriz MDS, apesar de degenerada)")
    print("=" * 70)

    fractions = []
    p = 2**255 - 19

    for trial in range(n_trials):
        s = secrets.token_bytes(32)
        n_sess = secrets.randbits(63)
        x = secrets.randbits(255) % p
        y = secrets.randbits(255) % p

        z_original = diffuse_rsd_s(x, y, s, n_sess)

        bit_to_flip = secrets.randbelow(255)
        x_flipped = x ^ (1 << bit_to_flip)

        z_flipped = diffuse_rsd_s(x_flipped, y, s, n_sess)

        hamming = hamming_distance_bits(z_original, z_flipped)
        fraction = hamming / (len(z_original) * 8)
        fractions.append(fraction)

    mean_fraction = statistics.mean(fractions)
    stdev_fraction = statistics.stdev(fractions)

    print(f"\nNúmero de testes: {n_trials}")
    print(f"Tamanho de saída: 256 bits (após SHA-256 final)")
    print(f"Fração média de bits alterados: {mean_fraction*100:.2f}%")
    print(f"Desvio padrão: {stdev_fraction*100:.2f}%")
    print(f"Ideal criptográfico: ~50.00% com baixa variância")

    if 0.45 <= mean_fraction <= 0.55 and stdev_fraction < 0.10:
        print("\nRESULTADO: passa no critério de avalanche.")
    else:
        print("\nRESULTADO: não atinge o critério de avalanche esperado.")

    return mean_fraction, stdev_fraction


if __name__ == "__main__":
    run_avalanche_test()
