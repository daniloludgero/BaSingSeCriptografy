# GitHub Repository Growth, SEO & Multi-Channel Launch Playbook

> **Target Repository**: `https://github.com/daniloludgero/BaSingSeCriptografy.git`
> **Interactive Demo URL**: `https://daniloludgero.github.io/BaSingSeCriptografy/`

---

## 1. Repository Header & GitHub SEO Configuration

Configure these exact settings in the GitHub repository **About** gear menu (also machine-readable in [`.github/REPO_METADATA.json`](../../.github/REPO_METADATA.json)):

- **Description (118 chars)**:
  `Keyed 512-bit SPN cryptographic diffusion lab (GF(2^16) inversion S-box + 32x32 Cauchy MDS) with Z3 SMT & SAT/CNF proofs.`
- **Website**:
  `https://daniloludgero.github.io/BaSingSeCriptografy/`
- **Topics (8 Focused Tags)**:
  `cryptography`, `cryptanalysis`, `finite-fields`, `mds-matrix`, `s-box`, `sat-solver`, `z3`, `python`
- **Checkboxes to Enable**:
  - [x] Releases
  - [x] Discussions (for cryptanalysis threads & RFCs)
  - [x] Preserve this repository (GitHub Archive Program / Arctic Code Vault)

---

## 2. Hacker News ("Show HN") Launch Protocol

### Optimal Timing
- **Day**: Tuesday or Wednesday
- **Time**: 07:30 – 08:45 EST (11:30 – 12:45 UTC)

### Title Syntax
```text
Show HN: BaSingSeCriptografy – Debugging a custom 512-bit SPN primitive with Z3 SMT, SAT/CNF, and Wide-Trail bounds
```

### 60-Second First Comment Protocol (Post Immediately After Submitting)
```markdown
Hi HN, author here.

BaSingSeCriptografy (RSD-S — Riemann Spectral Diffusion) is an open-source cryptographic research laboratory documenting the complete, unvarnished engineering journey of designing, breaking, and fixing an experimental 512-bit Substitution-Permutation Network (SPN) operating on pairs of scalars in F_p (p = 2^255 - 19).

### 1. Why I built and published the failures alongside the fix
Most experimental cryptography posts claim "unbreakable security" without testing basic algebraic invariants. We took the opposite approach—every structural mistake from v0 to v4 is preserved in `implementacao/` with reproducible failure tests:
- **v0 (9.34% avalanche)**: Purely linear (Chebyshev modulation + QR rotation). Completely broken by elementary linear algebra in 8 observations.
- **v1 (18.65% avalanche)**: Added dynamic Chebyshev S-boxes and an alleged "Reed-Solomon MDS" matrix `H[i,j] = (i+1)(j+1) + (i^j)`. Empirical rank testing over GF(2^16) exposed that the matrix had rank 5 of 16 (not invertible, let alone MDS), and `arccos` domain saturation left the S-box with only 23,393 / 65,536 unique values.
- **v2 (19.90% avalanche)**: Replaced the matrix with a true Cauchy MDS matrix over GF(2^16) (`M[i,j] = 1/(x_i XOR y_j)`). Marginal gain proved the S-box was still bottlenecking diffusion.
- **v3 (23.79% avalanche)**: Replaced the Chebyshev S-box with multiplicative inversion in GF(2^16) (`0x1100B`). Why was avalanche still ~24% when both the S-box and MDS matrix were mathematically sound?
- **v4 (50.31% pre-SHA / 49.53% post-SHA avalanche)**: Found the root cause—slicing 255-bit F_p inputs into eight 16-bit words (128 bits) silently discarded 127 bits (49.8%) of every input! Expanding to 16 slices per input (32 words = 512-bit internal state) with a 32x32 Cauchy MDS matrix (branch number 33) immediately achieved full 50.31% avalanche.

### 2. Formal Verification & SAT/SMT Tooling in the Repo
Beyond statistical tests, we built:
- **Z3 SMT DDT Uniformity Proof (`ferramentas/prova_ddt_smt.py`)**: Proves the 16-bit inversion S-box has differential uniformity 4 (max probability 2^-14) with 4 concrete Z3 witnesses `(0, 1, 0x015E, 0x015F)`.
- **Boolean XOR Synthesis (`implementacao/mds_xor_synthesis.py`)**: Synthesizes the 512x512 boolean Cauchy MDS transformation from 130,848 naive XOR gates down to 45,050 XOR gates (-65.57%) and exports DIMACS CNF (`ferramentas/mds_512.cnf`).
- **Wide-Trail & Branch-and-Bound Trail Search**: DP proof of >= 66 active S-boxes over 4 rounds (single-characteristic bound <= 2^-924), plus concrete 4-round trail search finding a globally compatible characteristic of weight 2^-1439 (`profile: 1, 32, 31, 32`).

### 3. What this is NOT suitable for
This is an **experimental research prototype and educational cryptanalysis testbed**. It is NOT audited, NOT constant-time (Python table lookups leak timing), and MUST NOT be used in production. We also explicitly document in `especificacao/RESTRICOES_DE_PROJETO.md` why avoiding factoring/DLP does not automatically grant post-quantum security claims.

- Interactive Web Lab (no install): https://daniloludgero.github.io/BaSingSeCriptografy/
- GitHub Repo: https://github.com/daniloludgero/BaSingSeCriptografy

I'd love feedback from cryptanalysts and SAT/SMT solver folks—especially on tighter CNF encodings for the 2-round and 4-round global differential queries!
```

---

## 3. Reddit Communities Playbook (`r/crypto`, `r/programming`, `r/Python`)

- **Format**: Self-post (technical write-up), never a bare link post.
- **Structure**:
  1. Lead with the counter-intuitive engineering lesson: *"Why fixing both the S-box (GF(2^16) inversion) and the diffusion matrix (Cauchy MDS) still left our cipher at 23.79% avalanche—until we found a 127-bit input truncation bug."*
  2. Include the `v0 -> v4` table and the 65.57% XOR gate reduction numbers.
  3. Ask specific technical questions about Boyar-Peralta / Paar heuristics vs greedy CSE for 512×512 MDS boolean matrices.
  4. Place the GitHub repository and Interactive Web Lab links at the end.

---

## 4. Curated `good-first-issue` Backlog (Contributor Conversion Loop)

Maintain these 5 concrete, well-scoped issues open with the `good-first-issue` and `help-wanted` labels to convert visitors into active contributors:

### Issue #1: Vectorize `gf_matrix_vector_mult` in `implementacao/mds_bitmatrix.py` using NumPy bitwise operations
- **Target File & Function**: [`implementacao/mds_bitmatrix.py`](../../implementacao/mds_bitmatrix.py) -> `apply_mds_bitmatrix(vector)`
- **Expected Behavior**: Pack the 512-bit state into an array of 8 `uint64` integers and compute parity via bitwise AND + `.bit_count() & 1` instead of nested Python loops, achieving a `>10x` speedup while returning identical `np.uint32` output.
- **Verification Command**: `python3 -m unittest testes/test_rsd_s_v4.py -k TestMdsBooleanCircuit -v`

### Issue #2: Add Paar / Boyar-Peralta two-step lookahead option to `implementacao/mds_xor_synthesis.py`
- **Target File & Function**: [`implementacao/mds_xor_synthesis.py`](../../implementacao/mds_xor_synthesis.py) -> `build_mds_xor_circuit()`
- **Expected Behavior**: Benchmark whether tie-breaking candidate XOR pairs by maximum downstream fan-out reduces the total gate count below `45,050` gates while passing all basis and random vector equivalence checks.
- **Verification Command**: `python3 -m unittest testes/test_rsd_s_v4.py -k test_synthesized_xor_circuit -v`

### Issue #3: Add external DIMACS SAT solver runner (`cadical` / `kissat` / `z3 -dimacs`) to `ferramentas/rsd_cli.py`
- **Target File & Function**: [`ferramentas/rsd_cli.py`](../../ferramentas/rsd_cli.py) -> `build_parser()`
- **Expected Behavior**: Add a `solve-cnf` subcommand that runs an installed SAT solver binary against `ferramentas/rsd_diff_round1_compact_sat.cnf` and `ferramentas/rsd_diff_round1_compact_unsat.cnf` and reports wall-clock time and SAT/UNSAT verification.
- **Verification Command**: `python3 -m unittest discover -s testes -p "test_*.py" -v`

### Issue #4: Export 4-round concrete trail differential differences to JSON for the Web Lab
- **Target File & Function**: [`implementacao/analise_duas_rodadas.py`](../../implementacao/analise_duas_rodadas.py) -> `analyze_full_witness()`
- **Expected Behavior**: Add a `--json` flag when running `python3 implementacao/analise_duas_rodadas.py` so researchers can pipe concrete 4-round witness traces directly into visualization tools.
- **Verification Command**: `python3 -m unittest testes/test_rsd_s_v4.py -k test_four_round_globally_compatible_characteristics -v`

### Issue #5: Add constant-time bitsliced / algebraic circuit reference prototype for GF(2^16) inversion
- **Target File & Function**: [`implementacao/gf16_inverse_cnf.py`](../../implementacao/gf16_inverse_cnf.py)
- **Expected Behavior**: Provide a pure boolean-gate evaluator for $x^{65534}$ in $\mathbb{F}_{2^{16}}$ without secret-dependent table indexing, documenting the gate count vs lookup table trade-off.
- **Verification Command**: `python3 -m unittest testes/test_rsd_s_v4.py -k TestInverseCnf -v`
