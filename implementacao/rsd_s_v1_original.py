import numpy as np
from hashlib import sha256
import hmac
import struct

# Parâmetros
W = 16
B = 16
MASK = (1 << B) - 1
R = 4

def mds_matrix():
    H = np.ones((W, W), dtype=np.uint64)
    for i in range(W):
        for j in range(W):
            H[i, j] = ( (i+1)*(j+1) + (i^j) ) & MASK
    return H

M = mds_matrix()

def rol(x, k):
    return ((x << k) | (x >> (B - k))) & MASK

def chebyshev(k, t_float):
    return np.cos(k * np.arccos(np.clip(t_float, -1, 1)))

def generate_sbox(s, n_sess, r):
    t_hash = hmac.new(s, n_sess.to_bytes(8,'big') + b'RSD-S' + r.to_bytes(1,'big'), sha256).digest()
    t_int = int.from_bytes(t_hash[:2], 'big')
    t = (t_int / 65535.0) * 2 - 1
    sbox = np.zeros(65536, dtype=np.uint64)
    c = int.from_bytes(t_hash[2:4], 'big')
    alpha = (r * 7) % 16
    for w in range(65536):
        k = (w * (r+1) * 2654435761) % 16
        val = chebyshev(k, t - (w/65535.0 * 2 - 1))
        sbox[w] = rol(int(abs(val) * 65535) & MASK, alpha) ^ c
    return sbox

def derive_keys(s, n_sess):
    keys = []
    K0 = hmac.new(s, n_sess.to_bytes(8,'big') + b'\x00', sha256).digest()
    keys.append(K0)
    for r in range(1, R+1):
        K = hmac.new(s, keys[-1] + r.to_bytes(1,'big'), sha256).digest()
        keys.append(K)
    return keys

def diffuse_rsd_s(x, y, s, n_sess):
    state = np.zeros(W, dtype=np.uint64)
    for i in range(8):
        state[i] = (x >> (i*B)) & MASK
        state[8+i] = (y >> (i*B)) & MASK

    keys = derive_keys(s, n_sess)
    K0_words = np.frombuffer(keys[0][:32], dtype='<u2')
    state ^= K0_words.astype(np.uint64)

    for r in range(1, R+1):
        sbox = generate_sbox(s, n_sess, r)
        for i in range(W):
            state[i] = sbox[state[i]]
        state = (M @ state) & MASK
        K_words = np.frombuffer(keys[r][:32], dtype='<u2')
        state ^= K_words.astype(np.uint64)

    z = 0
    for i in range(W):
        z |= int(state[i]) << (i*B)
    return sha256(z.to_bytes(32, 'big')).digest()

if __name__ == "__main__":
    s = b"teste_semente_32_bytes____1234"
    n = 123456789
    x = 1234567890123456789012345678901234567890 % (2**255-19)
    y = 9876543210987654321098765432109876543210 % (2**255-19)

    out = diffuse_rsd_s(x, y, s, n)
    print(out.hex())
