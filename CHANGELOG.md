# Changelog

All notable changes to **BaSingSeCriptografy (`RSD-S — Riemann Spectral Diffusion`)** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.1] - 2026-10-18

### Added
- **Interactive Cryptanalysis Web Laboratory (`docs/index.html`)**: Browser-based interactive workbench for exploring $\mathbb{F}_{2^{16}}$ inversion (`0x1100B`), $32 \times 32$ Cauchy MDS diffusion, `v1` (128-bit truncation bug) vs `v4` (256-bit full $\mathbb{F}_p$ coverage) bit-flip behavior, Known-Answer Test (KAT) vector verification, and Wide-Trail / SAT / SMT bounds.
- **Developer Quickstart CLI (`ferramentas/rsd_cli.py`)**: Zero-friction command-line interface supporting `kat`, `demo`, `bounds`, and `hash` subcommands with machine-readable `--json` output in under 10 seconds.
- **Python Packaging (`pyproject.toml`, `requirements.txt`)**: Standardized package metadata for `basingse-rsd-s`.
- **GitHub Engineering & CI/CD Automation (`.github/`)**: Multi-Python (`3.10–3.12`) and multi-NumPy (`1.26.x`, `2.x`) CI quality gates, tag-triggered release automation, GitHub Pages deployment, structured YAML issue forms (including Cryptanalysis Finding reports), PR template, and Dependabot configuration.
- **OSS Governance & Commercial Strategy**: Added `LICENSE` (MIT), `TRADEMARK_POLICY.md`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `docs/strategy/OSS_COMMERCIAL_STRATEGY.md`, and `docs/growth/GITHUB_LAUNCH_PLAYBOOK.md`.

### Fixed
- **NumPy 1.26 / 2.x Cross-Version Compatibility**: Cast Python scalar `int` operands to `np.uint64` during in-place XOR (`^=`) operations on `dtype=np.uint64` arrays in `implementacao/analise_duas_rodadas.py` and `implementacao/busca_branch_bound.py`, resolving `TypeError` on NumPy 1.26 while preserving bit-identical behavior and KAT outputs on NumPy 2.x.

---

## [0.4.0] - 2026-08-09

### Added
- **RSD-S v4 Official Specification & Implementation (`implementacao/rsd_s_v4_final.py`)**:
  - Full 256-bit input fragmentation (16 slices of 16 bits per scalar $x, y \in \mathbb{F}_p$, $p = 2^{255}-19$) into a 32-word (512-bit) internal state, eliminating the silent 127-bit truncation of `v1–v3`.
  - Expanded $32 \times 32$ Cauchy MDS matrix over $\mathbb{F}_{2^{16}}$ with verified branch number 33 (`implementacao/mds_real.py`).
  - Bijective 16-bit inversion S-box over $\mathbb{F}_{2^{16}} / (x^{16} + x^{12} + x^3 + x + 1)$ (`0x1100B`) with proven differential uniformity 4 ($2^{-14}$ max differential probability) and max Walsh magnitude 512 ($2^{-7}$ max linear correlation).
  - Strict input contract validation (`validate_inputs`) rejecting out-of-range field elements, non-32-byte keys, and invalid session nonces.
- **Formal SAT/SMT & Differential Trail Analysis Suite**:
  - Algebraic and Z3 SMT proof of exact S-box DDT uniformity (`ferramentas/prova_ddt_smt.py`).
  - Boolean MDS bit-matrix verification (`implementacao/mds_bitmatrix.py`) and greedy common-subexpression XOR circuit synthesis reducing 130,848 XOR gates to 45,050 gates (`-65.57%`, `implementacao/mds_xor_synthesis.py`).
  - Exact DIMACS CNF encodings for $\mathbb{F}_{2^{16}}$ inversion (`implementacao/gf16_inverse_cnf.py`), first round (`implementacao/rsd_round_cnf.py`), and compact differential queries (`implementacao/rsd_differential_cnf.py`).
  - Multi-round concrete witness propagation (`implementacao/analise_duas_rodadas.py`), branch-and-bound search (`implementacao/busca_branch_bound.py`, best discovered 4-round characteristic weight $2^{-1439}$), and diversified background search (`implementacao/busca_diversificada.py`).
  - Conservative Wide-Trail dynamic programming bounds (`implementacao/analise_wide_trail.py`) establishing $\ge 66, 99, 132, 165$ active S-boxes for $4, 6, 8, 10$ rounds.
  - Known-Answer Test vectors (`testes/vetores_v4.json`) and 29 deterministic unit tests (`testes/test_rsd_s_v4.py`).
  - Historical implementations (`v1`, `v2`, `v3`) and empirical reports in `RELATORIO_FINAL.md` and `resultados/`.
