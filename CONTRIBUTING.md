# Contributing to BaSingSeCriptografy (RSD-S)

Thank you for contributing to **BaSingSeCriptografy**! Whether you are submitting a new SAT/SMT cryptanalysis encoding, optimizing boolean circuits, improving the Interactive Web Laboratory, or refining documentation, this guide ensures your contribution lands smoothly.

---

## 1. Golden Rules of Scientific & Engineering Integrity

Before opening an issue or Pull Request, please review our two non-negotiable invariants:

1. **Preserve the Official `v4` Contract & Historical Artifacts**:
   - The historical implementations (`rsd_s_v1_original.py`, `rsd_s_v2_matriz_corrigida.py`, `rsd_s_v3_sbox_corrigida.py`) exist intentionally to reproduce the `v0 -> v4` diagnostic journey documented in [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md). Do not "fix" `v1–v3`.
   - `diffuse_rsd_s_final(x, y, s, n_sess)` in [`implementacao/rsd_s_v4_final.py`](implementacao/rsd_s_v4_final.py) must remain bit-for-bit compatible with all Known-Answer Test (KAT) vectors in [`testes/vetores_v4.json`](testes/vetores_v4.json).
2. **Strict Intellectual Honesty ([`especificacao/RESTRICOES_DE_PROJETO.md`](especificacao/RESTRICOES_DE_PROJETO.md))**:
   - Never claim that a statistical test, avalanche score, or single-characteristic Wide-Trail bound constitutes a "proof of security".
   - Always report timeouts (`unknown` in Z3/SAT) honestly as **inconclusive**, never as evidence of security.
   - Respect the quantum threat model rules in [`especificacao/RESTRICOES_DE_PROJETO.md`](especificacao/RESTRICOES_DE_PROJETO.md): you may state that RSD-S is not based on factoring or discrete logarithms, but you must **never** claim it "beats Shor" or is "post-quantum secure" without formal oracle reductions and peer review.

---

## 2. Local Development Setup (Under 30 Seconds)

```bash
# 1. Clone the repository
git clone https://github.com/daniloludgero/BaSingSeCriptografy.git
cd BaSingSeCriptografy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the fast deterministic test suite
python3 -m unittest discover -s testes -p "test_*.py" -v

# 4. Run the CLI quick verification
python3 ferramentas/rsd_cli.py kat
```

---

## 3. Git Workflow & Commit Discipline

We follow **Trunk-Based Development** with short-lived branches and **Atomic Conventional Commits**:

### Branch Naming
- `feat/<short-slug>` — New analysis tool, solver model, or UI capability
- `fix/<short-slug>` — Bug fix in tooling, tests, or compatibility
- `docs/<short-slug>` — Reports, mathematical documentation, or ADRs
- `test/<short-slug>` — New KAT vectors, property tests, or regression checks
- `chore/<short-slug>` — CI/CD, dependencies, or repository configuration

### Conventional Commit Format & DCO Sign-Off
We use the lightweight **Developer Certificate of Origin (DCO)** (`git commit -s`) rather than a heavy copyright-assignment CLA:

```text
<type>(<scope>): <concise summary in imperative mood>

<body explaining the WHY and mathematical/engineering rationale>

Signed-off-by: Your Name <your.email@example.com>
```

---

## 4. Pre-Submit Quality Checklist

Before opening a Pull Request, ensure all checks pass locally:

- [ ] `python3 -m unittest discover -s testes -p "test_*.py" -v` passes 100%
- [ ] `python3 testes/suite_testes_completa.py` passes all 5 statistical checks
- [ ] `python3 ferramentas/rsd_cli.py kat` confirms all 4 KAT vectors match
- [ ] No secrets, `.env` files, or `__pycache__` artifacts are staged (`git diff --staged`)
- [ ] New empirical results include exact environment metadata (Python version, NumPy version, solver version, seed, and reproduction command) in `resultados/`
