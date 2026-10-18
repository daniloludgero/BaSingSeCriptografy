"""
rsd_s_corrected.py

Reimplementação do RSD-S idêntica à especificação original (S-boxes
espectrais, chaves de rodada via HMAC, 4 rodadas, SHA-256 final),
com UMA ÚNICA mudança: a matriz de difusão M é substituída pela
matriz de Cauchy MDS genuína (mds_real.py), no lugar da fórmula
H[i,j] = (i+1)(j+1) + (i^j) que se mostrou ter rank 5 de 16.

Isso isola precisamente o efeito da correção: se a difusão melhorar
substancialmente, confirma que o problema estava na matriz. Se não
melhorar o suficiente, indica que há mais de um problema estrutural.

NOTA IMPORTANTE: a matriz de Cauchy é construída sobre GF(2^16)
(aritmética de corpo finito, XOR para adição). Para a operação de
"permutação" da rede, isso significa trocar `(M @ state) & MASK`
(multiplicação inteira mod 2^16, incorreta para MDS) por uma
multiplicação matriz-vetor GENUÍNA em GF(2^16) -- outra imprecisão
da especificação original, que mistura as duas estruturas algébricas.
"""

from __future__ import annotations

import numpy as np
from hashlib import sha256
import hmac

from mds_real import build_cauchy_mds, gf_mult, gf_add

W = 16
B = 16
MASK = (1 << B) - 1
R = 4

M_CAUCHY = build_cauchy_mds(W)


def gf_matrix_vector_mult(M: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    """Multiplicação matriz-vetor CORRETA em GF(2^16): soma é XOR, produto é gf_mult."""
    result = np.zeros(n, dtype=np.uint32)
    for i in range(n):
        acc = 0
        for j in range(n):
            acc = gf_add(acc, gf_mult(int(M[i, j]), int(v[j])))
        result[i] = acc
    return result


def rol(x: int, k: int) -> int:
    return ((x << k) | (x >> (B - k))) & MASK


def chebyshev(k: int, t_float: float) -> float:
    return np.cos(k * np.arccos(np.clip(t_float, -1, 1)))


def generate_sbox(s: bytes, n_sess: int, r: int) -> np.ndarray:
    t_hash = hmac.new(s, n_sess.to_bytes(8, "big") + b"RSD-S" + r.to_bytes(1, "big"), sha256).digest()
    t_int = int.from_bytes(t_hash[:2], "big")
    t = (t_int / 65535.0) * 2 - 1
    sbox = np.zeros(65536, dtype=np.uint64)
    c = int.from_bytes(t_hash[2:4], "big")
    alpha = (r * 7) % 16
    for w in range(65536):
        k = (w * (r + 1) * 2654435761) % 16
        val = chebyshev(k, t - (w / 65535.0 * 2 - 1))
        sbox[w] = rol(int(abs(val) * 65535) & MASK, alpha) ^ c
    return sbox


def derive_keys(s: bytes, n_sess: int) -> list[bytes]:
    keys = []
    K0 = hmac.new(s, n_sess.to_bytes(8, "big") + b"\x00", sha256).digest()
    keys.append(K0)
    for r in range(1, R + 1):
        K = hmac.new(s, keys[-1] + r.to_bytes(1, "big"), sha256).digest()
        keys.append(K)
    return keys


_sbox_cache: dict[tuple, np.ndarray] = {}


def diffuse_rsd_s_corrected(x: int, y: int, s: bytes, n_sess: int) -> bytes:
    state = np.zeros(W, dtype=np.uint64)
    for i in range(8):
        state[i] = (x >> (i * B)) & MASK
        state[8 + i] = (y >> (i * B)) & MASK

    keys = derive_keys(s, n_sess)
    K0_words = np.frombuffer(keys[0][:32], dtype="<u2").astype(np.uint64)
    state ^= K0_words

    for r in range(1, R + 1):
        cache_key = (s, n_sess, r)
        if cache_key not in _sbox_cache:
            _sbox_cache[cache_key] = generate_sbox(s, n_sess, r)
        sbox = _sbox_cache[cache_key]

        for i in range(W):
            state[i] = sbox[state[i]]

        # CORREÇÃO: multiplicação matriz-vetor genuína em GF(2^16),
        # usando a matriz de Cauchy MDS (rank completo, MDS comprovado)
        state = gf_matrix_vector_mult(M_CAUCHY, state, W).astype(np.uint64)

        K_words = np.frombuffer(keys[r][:32], dtype="<u2").astype(np.uint64)
        state ^= K_words

    z = 0
    for i in range(W):
        z |= int(state[i]) << (i * B)
    return sha256(z.to_bytes(32, "big")).digest()


def diffuse_rsd_s_corrected_PRE_SHA(x: int, y: int, s: bytes, n_sess: int) -> np.ndarray:
    """Versão que retorna o estado pré-SHA-256, para isolar a difusão da rede em si."""
    state = np.zeros(W, dtype=np.uint64)
    for i in range(8):
        state[i] = (x >> (i * B)) & MASK
        state[8 + i] = (y >> (i * B)) & MASK

    keys = derive_keys(s, n_sess)
    K0_words = np.frombuffer(keys[0][:32], dtype="<u2").astype(np.uint64)
    state ^= K0_words

    for r in range(1, R + 1):
        cache_key = (s, n_sess, r)
        if cache_key not in _sbox_cache:
            _sbox_cache[cache_key] = generate_sbox(s, n_sess, r)
        sbox = _sbox_cache[cache_key]

        for i in range(W):
            state[i] = sbox[state[i]]

        state = gf_matrix_vector_mult(M_CAUCHY, state, W).astype(np.uint64)

        K_words = np.frombuffer(keys[r][:32], dtype="<u2").astype(np.uint64)
        state ^= K_words

    return state


if __name__ == "__main__":
    import secrets

    print("=" * 70)
    print("Teste funcional: RSD-S com matriz MDS corrigida (Cauchy)")
    print("=" * 70)

    s = secrets.token_bytes(32)
    n_sess = secrets.randbits(63)
    x, y = 123456789, 987654321

    z = diffuse_rsd_s_corrected(x, y, s, n_sess)
    print(f"\nSaída (hex): {z.hex()}")

    z2 = diffuse_rsd_s_corrected(x, y, s, n_sess)
    print(f"Determinístico: {z == z2}")
