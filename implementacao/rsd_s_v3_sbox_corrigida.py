"""
rsd_s_fully_corrected.py

Versão com AMBAS as correções aplicadas:
  1. Matriz de difusão: Cauchy MDS genuína (já validada em mds_real.py).
  2. S-box: inversão em GF(2^16) + XOR de constante de rodada (mesma
     família da S-box do AES, adaptada para 16 bits), no lugar da
     construção via Chebyshev que se mostrou ter apenas 35.7% de
     valores únicos e 25% de avalanche isolada.

Mantém idêntico o resto da estrutura: fragmentação, chaves de rodada
via HMAC hierárquico, 4 rodadas, SHA-256 final -- para isolar
precisamente o efeito de corrigir os dois componentes de segurança
mais importantes (substituição não-linear e difusão linear).
"""

from __future__ import annotations

import numpy as np
from hashlib import sha256
import hmac

from mds_real import build_cauchy_mds, gf_mult, gf_add, gf_inv, GF16_POLY

W = 16
B = 16
MASK = (1 << B) - 1
R = 4

M_CAUCHY = build_cauchy_mds(W)

_INVERSION_SBOX_CACHE: np.ndarray | None = None


def get_base_inversion_sbox() -> np.ndarray:
    """S-box de inversão em GF(2^16), calculada uma única vez (é cara: ~6s)."""
    global _INVERSION_SBOX_CACHE
    if _INVERSION_SBOX_CACHE is None:
        size = 1 << B
        sbox = np.zeros(size, dtype=np.uint32)
        for w in range(size):
            sbox[w] = gf_inv(w, GF16_POLY, B)
        _INVERSION_SBOX_CACHE = sbox
    return _INVERSION_SBOX_CACHE


def gf_matrix_vector_mult(M: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    result = np.zeros(n, dtype=np.uint32)
    for i in range(n):
        acc = 0
        for j in range(n):
            acc = gf_add(acc, gf_mult(int(M[i, j]), int(v[j])))
        result[i] = acc
    return result


def derive_keys(s: bytes, n_sess: int) -> list[bytes]:
    keys = []
    K0 = hmac.new(s, n_sess.to_bytes(8, "big") + b"\x00", sha256).digest()
    keys.append(K0)
    for r in range(1, R + 1):
        K = hmac.new(s, keys[-1] + r.to_bytes(1, "big"), sha256).digest()
        keys.append(K)
    return keys


_round_constant_cache: dict[tuple, int] = {}


def round_constant(s: bytes, n_sess: int, r: int) -> int:
    """
    Constante de rodada (substitui o papel do 't' de Chebyshev): ainda
    derivada de (s, n_sess, r) via HMAC, mas usada apenas como XOR
    pós-inversão -- não mais controlando a forma da S-box em si, já
    que a inversão GF(2^16) já é fixa e criptograficamente boa por
    construção, independente de t.
    """
    cache_key = (s, n_sess, r)
    if cache_key not in _round_constant_cache:
        h = hmac.new(s, n_sess.to_bytes(8, "big") + b"RC" + r.to_bytes(1, "big"), sha256).digest()
        _round_constant_cache[cache_key] = int.from_bytes(h[:2], "big")
    return _round_constant_cache[cache_key]


def diffuse_rsd_s_fully_corrected(x: int, y: int, s: bytes, n_sess: int) -> bytes:
    state = np.zeros(W, dtype=np.uint64)
    for i in range(8):
        state[i] = (x >> (i * B)) & MASK
        state[8 + i] = (y >> (i * B)) & MASK

    keys = derive_keys(s, n_sess)
    K0_words = np.frombuffer(keys[0][:32], dtype="<u2").astype(np.uint64)
    state ^= K0_words

    base_sbox = get_base_inversion_sbox()

    for r in range(1, R + 1):
        rc = round_constant(s, n_sess, r)

        for i in range(W):
            state[i] = base_sbox[state[i]] ^ rc

        state = gf_matrix_vector_mult(M_CAUCHY, state, W).astype(np.uint64)

        K_words = np.frombuffer(keys[r][:32], dtype="<u2").astype(np.uint64)
        state ^= K_words

    z = 0
    for i in range(W):
        z |= int(state[i]) << (i * B)
    return sha256(z.to_bytes(32, "big")).digest()


def diffuse_rsd_s_fully_corrected_PRE_SHA(x: int, y: int, s: bytes, n_sess: int) -> np.ndarray:
    state = np.zeros(W, dtype=np.uint64)
    for i in range(8):
        state[i] = (x >> (i * B)) & MASK
        state[8 + i] = (y >> (i * B)) & MASK

    keys = derive_keys(s, n_sess)
    K0_words = np.frombuffer(keys[0][:32], dtype="<u2").astype(np.uint64)
    state ^= K0_words

    base_sbox = get_base_inversion_sbox()

    for r in range(1, R + 1):
        rc = round_constant(s, n_sess, r)
        for i in range(W):
            state[i] = base_sbox[state[i]] ^ rc
        state = gf_matrix_vector_mult(M_CAUCHY, state, W).astype(np.uint64)
        K_words = np.frombuffer(keys[r][:32], dtype="<u2").astype(np.uint64)
        state ^= K_words

    return state


if __name__ == "__main__":
    import secrets
    import time

    print("=" * 70)
    print("Teste funcional: RSD-S com S-box de inversão + matriz Cauchy MDS")
    print("=" * 70)

    print("\nPré-computando S-box de inversão (uma vez, ~6s)...")
    t0 = time.time()
    get_base_inversion_sbox()
    print(f"Concluído em {time.time()-t0:.1f}s (cacheada para chamadas seguintes)")

    s = secrets.token_bytes(32)
    n_sess = secrets.randbits(63)
    x, y = 123456789, 987654321

    z = diffuse_rsd_s_fully_corrected(x, y, s, n_sess)
    print(f"\nSaída (hex): {z.hex()}")

    z2 = diffuse_rsd_s_fully_corrected(x, y, s, n_sess)
    print(f"Determinístico: {z == z2}")
