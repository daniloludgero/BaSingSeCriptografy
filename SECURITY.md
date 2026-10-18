# Security Policy & Cryptanalysis Disclosure Protocol

> [!CAUTION]
> **CRITICAL RESEARCH DISCLAIMER**:
> **RSD-S (Riemann Spectral Diffusion)** is an **experimental cryptographic research prototype**.
> It is **NOT audited**, **NOT peer-reviewed**, **NOT constant-time**, and **MUST NOT be used in production** or to protect real sensitive data.

---

## 1. Scope of Security & Cryptanalysis Reports

We actively distinguish between two categories of reports:

### Category A: Public Cryptanalysis Findings (Encouraged Publicly!)
Because the primary mission of `BaSingSeCriptografy` is transparent cryptographic research and peer review, **mathematical and structural cryptanalysis findings are welcome as public GitHub Issues** using the **Cryptanalysis Finding** template:
- Differential trails with higher probability than the currently documented four-round concrete weight (`2^-1439`)
- Linear approximations with correlation exceeding the Wide-Trail bound (`2^-462`)
- Algebraic attacks over $\mathbb{F}_{2^{16}}$ exploiting the interaction between inversion (`0x1100B`) and the $32 \times 32$ Cauchy MDS matrix
- Related-key distinguishers against the hierarchical HMAC-SHA256 round key schedule
- Faster SAT/SMT/MILP encodings that resolve the 2-round and 4-round global compatibility queries

### Category B: Repository / Tooling / Supply-Chain Vulnerabilities (Private Disclosure)
If you discover a vulnerability in the **repository infrastructure, CI/CD workflows, Web Laboratory (`docs/`), or Python CLI tooling** (such as arbitrary code execution, XSS in the web laboratory, or dependency vulnerabilities), please report it privately via **GitHub Private Vulnerability Reporting** (`Security` tab -> `Report a vulnerability`).

---

## 2. Supported Versions

| Version | Variant | Status | Purpose |
| :--- | :--- | :--- | :--- |
| **`v0.4.x` (`rsd_s_v4_final.py`)** | 32-word state, GF($2^{16}$) Inversion S-Box, $32 \times 32$ Cauchy MDS | **Active Research Baseline** | Target for formal cryptanalysis & KAT verification |
| **`v3` (`rsd_s_v3_sbox_corrigida.py`)** | 16-word state (128-bit truncation flaw) | Historical Artifact | Pedagogical demonstration of input truncation failure (23.79% avalanche) |
| **`v2` (`rsd_s_v2_matriz_corrigida.py`)** | Cauchy MDS + Chebyshev S-Box | Historical Artifact | Pedagogical demonstration of non-bijective S-box failure (19.90% avalanche) |
| **`v1` (`rsd_s_v1_original.py`)** | Rank-5 Matrix + Chebyshev S-Box | Historical Artifact | Pedagogical baseline exposing rank-deficient diffusion (18.65% avalanche) |

---

## 3. Known Architectural Limitations (By Design in Prototype Stage)

Do **not** report the following known prototype characteristics as software vulnerabilities—they are already explicitly documented in [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md) and [`resultados/validacao_2026-07-28.md`](resultados/validacao_2026-07-28.md):

1. **Non-Constant-Time Table Lookups**: `rsd_s_v4_final.py` indexes `_INVERSION_SBOX_CACHE` in Python using secret-dependent state words, which is vulnerable to cache-timing side channels.
2. **Unbounded Trail Clustering**: The documented weights (`2^-924` Wide-Trail bound, `2^-1439` concrete 4-round characteristic) bound single characteristics, not the full differential hull (sum of all trails sharing an input/output difference).
3. **Quantum Threat Model**: As documented in [`especificacao/RESTRICOES_DE_PROJETO.md`](especificacao/RESTRICOES_DE_PROJETO.md), RSD-S is a symmetric keyed primitive; Grover's algorithm is the generic quantum reference, and no formal post-quantum security claim is made.

---

## 4. Response SLA

| Report Type | Acknowledgment SLA | Triage & Verification SLA |
| :--- | :--- | :--- |
| **Supply-Chain / Tooling Vulnerability** | `< 24 hours` | `< 7 days` |
| **Reproducible Cryptanalysis Script / CNF Witness** | `< 48 hours` | `< 14 days` (documented in `resultados/` with full credit) |
