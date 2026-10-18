"""
rsd_s_v4_final.py

Versão com AS TRÊS correções aplicadas:
  1. Fragmentação: 16 fatias de 16 bits por entrada (x e y), cobrindo
     os 255 bits completos de F_p -- em vez das 8 fatias (128 bits)
     originais, que descartavam ~127 bits silenciosamente.
  2. S-box: inversão em GF(2^16), bijeção comprovada, ~49% de
     avalanche isolada.
  3. Matriz de difusão: Cauchy MDS 32x32 (rank completo, MDS
     comprovado por teorema).

Estado agora tem 32 palavras de 16 bits = 512 bits internos (16 para
x, 16 para y), reduzidos a 256 bits apenas na saída final via SHA-256.
"""

from __future__ import annotations

import numpy as np
from hashlib import sha256
import hmac

from mds_real import build_cauchy_mds, gf_mult, gf_add, gf_inv, GF16_POLY

W = 32
B = 16
MASK = (1 << B) - 1
R = 4
MAX_ROUNDS = 255
P_CURVE25519 = 2**255 - 19
KEY_SIZE = 32
MAX_SESSION = 2**64 - 1

M_CAUCHY_32 = build_cauchy_mds(W)

_INVERSION_SBOX_CACHE: np.ndarray | None = None


def get_base_inversion_sbox() -> np.ndarray:
    global _INVERSION_SBOX_CACHE
    if _INVERSION_SBOX_CACHE is None:
        size = 1 << B
        sbox = np.zeros(size, dtype=np.uint32)
        for w in range(size):
            sbox[w] = gf_inv(w, GF16_POLY, B)
        sbox.flags.writeable = False
        _INVERSION_SBOX_CACHE = sbox
    return _INVERSION_SBOX_CACHE


def _validate_field_element(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} deve ser um inteiro")
    if not 0 <= value < P_CURVE25519:
        raise ValueError(f"{name} deve satisfazer 0 <= {name} < 2^255 - 19")


def _validate_key(s: bytes) -> None:
    if not isinstance(s, bytes):
        raise TypeError("s deve ser bytes")
    if len(s) != KEY_SIZE:
        raise ValueError(f"s deve ter exatamente {KEY_SIZE} bytes")


def _validate_session(n_sess: int) -> None:
    if isinstance(n_sess, bool) or not isinstance(n_sess, int):
        raise TypeError("n_sess deve ser um inteiro")
    if not 0 <= n_sess <= MAX_SESSION:
        raise ValueError("n_sess deve satisfazer 0 <= n_sess < 2^64")


def _validate_rounds(rounds: int) -> None:
    if isinstance(rounds, bool) or not isinstance(rounds, int):
        raise TypeError("rounds deve ser um inteiro")
    if not 1 <= rounds <= MAX_ROUNDS:
        raise ValueError(f"rounds deve satisfazer 1 <= rounds <= {MAX_ROUNDS}")


def validate_inputs(x: int, y: int, s: bytes, n_sess: int) -> None:
    """Valida o contrato público da primitiva antes de processar o estado."""
    _validate_field_element(x, "x")
    _validate_field_element(y, "y")
    _validate_key(s)
    _validate_session(n_sess)


def gf_matrix_vector_mult(M: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    result = np.zeros(n, dtype=np.uint32)
    for i in range(n):
        acc = 0
        row = M[i]
        for j in range(n):
            if row[j] != 0 and v[j] != 0:
                acc = gf_add(acc, gf_mult(int(row[j]), int(v[j])))
        result[i] = acc
    return result


def derive_keys(s: bytes, n_sess: int, rounds: int = R) -> list[bytes]:
    _validate_key(s)
    _validate_session(n_sess)
    _validate_rounds(rounds)
    keys = []
    K0 = hmac.new(s, n_sess.to_bytes(8, "big") + b"\x00", sha256).digest()
    keys.append(K0)
    for r in range(1, rounds + 1):
        K = hmac.new(s, keys[-1] + r.to_bytes(1, "big"), sha256).digest()
        keys.append(K)
    return keys


def round_constant(s: bytes, n_sess: int, r: int) -> int:
    _validate_key(s)
    _validate_session(n_sess)
    if isinstance(r, bool) or not isinstance(r, int):
        raise TypeError("r deve ser um inteiro")
    if not 1 <= r <= MAX_ROUNDS:
        raise ValueError(f"r deve satisfazer 1 <= r <= {MAX_ROUNDS}")
    h = hmac.new(s, n_sess.to_bytes(8, "big") + b"RC" + r.to_bytes(1, "big"), sha256).digest()
    return int.from_bytes(h[:2], "big")


def fragment_full(x: int, y: int, w_per_input: int = 16, b: int = 16) -> np.ndarray:
    """Fragmentação CORRIGIDA: 16 fatias de 16 bits por entrada = 256 bits cobertos."""
    _validate_field_element(x, "x")
    _validate_field_element(y, "y")
    if w_per_input != 16 or b != 16:
        raise ValueError("a v4 exige exatamente 16 palavras de 16 bits por entrada")
    mask = (1 << b) - 1
    x_slices = [(x >> (j * b)) & mask for j in range(w_per_input)]
    y_slices = [(y >> (j * b)) & mask for j in range(w_per_input)]
    return np.array(x_slices + y_slices, dtype=np.uint64)


def _expand_key_words(key_bytes: bytes, n_words: int) -> np.ndarray:
    needed_bytes = n_words * 2
    material = key_bytes
    counter = 0
    while len(material) < needed_bytes:
        counter += 1
        material += hmac.new(key_bytes, counter.to_bytes(4, "big"), sha256).digest()
    return np.frombuffer(material[:needed_bytes], dtype="<u2").astype(np.uint64)


def _diffuse_state(x: int, y: int, s: bytes, n_sess: int, rounds: int) -> np.ndarray:
    validate_inputs(x, y, s, n_sess)
    _validate_rounds(rounds)
    state = fragment_full(x, y)

    keys = derive_keys(s, n_sess, rounds)
    state ^= _expand_key_words(keys[0], W)

    base_sbox = get_base_inversion_sbox()

    for r in range(1, rounds + 1):
        rc = round_constant(s, n_sess, r)
        for i in range(W):
            state[i] = base_sbox[state[i]] ^ rc

        state = gf_matrix_vector_mult(M_CAUCHY_32, state, W).astype(np.uint64)

        state ^= _expand_key_words(keys[r], W)

    return state


def _hash_state(state: np.ndarray) -> bytes:
    z_bytes = b"".join(int(state[i]).to_bytes(2, "big") for i in range(W))
    return sha256(z_bytes).digest()


def diffuse_rsd_s_rounds(
    x: int, y: int, s: bytes, n_sess: int, rounds: int
) -> bytes:
    """Versão experimental parametrizada; a API oficial usa quatro rodadas."""
    return _hash_state(_diffuse_state(x, y, s, n_sess, rounds))


def diffuse_rsd_s_rounds_PRE_SHA(
    x: int, y: int, s: bytes, n_sess: int, rounds: int
) -> np.ndarray:
    """Estado experimental de 512 bits antes do SHA-256 final."""
    return _diffuse_state(x, y, s, n_sess, rounds)


def diffuse_rsd_s_final(x: int, y: int, s: bytes, n_sess: int) -> bytes:
    """API oficial e compatível da RSD-S v4, fixada em quatro rodadas."""
    return diffuse_rsd_s_rounds(x, y, s, n_sess, R)


def diffuse_rsd_s_final_PRE_SHA(x: int, y: int, s: bytes, n_sess: int) -> np.ndarray:
    """Estado oficial de quatro rodadas antes do SHA-256 final."""
    return diffuse_rsd_s_rounds_PRE_SHA(x, y, s, n_sess, R)


if __name__ == "__main__":
    import secrets
    import time

    print("=" * 70)
    print("Teste funcional: RSD-S com AS TRÊS correções aplicadas")
    print("=" * 70)

    print("\nPré-computando S-box de inversão...")
    t0 = time.time()
    get_base_inversion_sbox()
    print(f"Concluído em {time.time()-t0:.1f}s")

    s = secrets.token_bytes(32)
    n_sess = secrets.randbits(63)
    p = 2**255 - 19
    x = secrets.randbits(255) % p
    y = secrets.randbits(255) % p

    z = diffuse_rsd_s_final(x, y, s, n_sess)
    print(f"\nSaída (hex): {z.hex()}")

    z2 = diffuse_rsd_s_final(x, y, s, n_sess)
    print(f"Determinístico: {z == z2}")

    x_high_bit = x ^ (1 << 200)
    z_high = diffuse_rsd_s_final(x_high_bit, y, s, n_sess)
    print(f"\nMudar um bit ALTO de x (posição 200, antes descartado) muda a saída: {z != z_high}")
