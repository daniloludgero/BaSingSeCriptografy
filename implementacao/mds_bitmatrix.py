"""Representação booleana linear da MDS 32x32 sobre GF(2^16)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from rsd_s_v4_final import M_CAUCHY_32, W, B, gf_matrix_vector_mult

STATE_BITS = W * B


@lru_cache(maxsize=1)
def mds_bit_rows() -> tuple[tuple[int, ...], ...]:
    """Retorna fontes XOR de cada um dos 512 bits de saída."""
    rows: list[list[int]] = [[] for _ in range(STATE_BITS)]
    for source in range(STATE_BITS):
        vector = np.zeros(W, dtype=np.uint32)
        vector[source // B] = 1 << (source % B)
        output = gf_matrix_vector_mult(M_CAUCHY_32, vector, W)
        for output_word, value in enumerate(output):
            integer = int(value)
            for output_bit in range(B):
                if integer & (1 << output_bit):
                    rows[output_word * B + output_bit].append(source)
    return tuple(tuple(row) for row in rows)


def apply_mds_bitmatrix(vector: np.ndarray) -> np.ndarray:
    if len(vector) != W:
        raise ValueError(f"o vetor deve conter {W} palavras")
    source_bits = [
        (int(vector[word]) >> bit) & 1
        for word in range(W)
        for bit in range(B)
    ]
    output = np.zeros(W, dtype=np.uint32)
    for output_index, sources in enumerate(mds_bit_rows()):
        parity = 0
        for source in sources:
            parity ^= source_bits[source]
        if parity:
            output[output_index // B] |= np.uint32(1 << (output_index % B))
    return output


def verify_mds_bitmatrix(samples: int = 16) -> bool:
    generator = np.random.default_rng(0x525344)
    for _ in range(samples):
        vector = generator.integers(0, 1 << B, size=W, dtype=np.uint32)
        expected = gf_matrix_vector_mult(M_CAUCHY_32, vector, W)
        if not np.array_equal(apply_mds_bitmatrix(vector), expected):
            return False
    return True


if __name__ == "__main__":
    rows = mds_bit_rows()
    densities = [len(row) for row in rows]
    print(f"equivalencia: {verify_mds_bitmatrix(32)}")
    print(
        f"fontes XOR por bit: min={min(densities)}, "
        f"media={sum(densities)/len(densities):.1f}, max={max(densities)}"
    )
