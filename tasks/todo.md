# Task Breakdown & Verification Checklist (`BaSingSeCriptografy`)

## Task 1: Git Initialization & Baseline Import
**Description:** Initialize a valid Git repository on branch `main` (replacing the empty `.git/` directory), configure remote `origin` (`https://github.com/daniloludgero/BaSingSeCriptografy.git`), add `.gitignore` and `.gitattributes`, and commit all original files (`RELATORIO_FINAL.md`, `especificacao/`, `ferramentas/`, `implementacao/`, `resultados/`, `testes/`) untouched as the foundational save point.

**Acceptance criteria:**
- [x] `git status` and `git remote -v` succeed with `origin` set to `https://github.com/daniloludgero/BaSingSeCriptografy.git`
- [x] `.gitignore` excludes `__pycache__/`, `.venv/`, `.env`, build artifacts, and `ferramentas/_vendor/` bytecode while tracking research artifacts
- [x] Initial commit contains the untouched original research package

**Verification:**
- [x] `git log --oneline -n 5` shows the baseline commit
- [x] `git remote -v` shows `https://github.com/daniloludgero/BaSingSeCriptografy.git`

**Dependencies:** None
**Files likely touched:** `.gitignore`, `.gitattributes`
**Estimated scope:** Small (2 files)

---

## Task 2: NumPy 1.x/2.x Compatibility Fix & Full Test Suite Pass
**Description:** Ensure `implementacao/analise_duas_rodadas.py` and `implementacao/busca_branch_bound.py` cast scalar XOR operands to `np.uint64` during in-place `^=` operations on `dtype=np.uint64` arrays so that both NumPy 1.26 (Linux) and NumPy 2.x (Windows) execute identically without `TypeError`.

**Acceptance criteria:**
- [x] `implementacao/analise_duas_rodadas.py` and `implementacao/busca_branch_bound.py` preserve 100% of mathematical behavior and KAT vectors
- [x] `python3 -m unittest discover -s testes -p "test_*.py" -v` passes all 29 tests with 0 errors
- [x] `python3 testes/suite_testes_completa.py` passes all 5 statistical/structural tests

**Verification:**
- [x] Tests pass: `python3 -m unittest discover -s testes -p "test_*.py" -v`
- [x] Statistical suite passes: `python3 testes/suite_testes_completa.py`

**Dependencies:** Task 1
**Files likely touched:** `implementacao/analise_duas_rodadas.py`, `implementacao/busca_branch_bound.py`
**Estimated scope:** Small (2 files, 3 lines)

---

## Task 3: Frictionless Python Packaging & Developer CLI (`< 30s` Quickstart)
**Description:** Create `pyproject.toml`, `requirements.txt`, and `ferramentas/rsd_cli.py` (plus unit tests in `testes/test_cli_and_repo.py`) enabling one-command demos (`demo`, `kat`, `avalanche`, `bounds`, `verify-input`) with JSON/table output for immediate developer evaluation.

**Acceptance criteria:**
- [x] `python3 ferramentas/rsd_cli.py kat` validates all 4 official v4 test vectors in `< 10s`
- [x] `python3 ferramentas/rsd_cli.py demo` demonstrates `v1` high-bit truncation vs `v4` full `F_p` diffusion and Wide-Trail bounds
- [x] CLI handles invalid inputs (`x >= p`, negative `x`, invalid key length, invalid rounds) with clear error exit codes

**Verification:**
- [x] Tests pass: `python3 -m unittest discover -s testes -p "test_*.py" -v`
- [x] Manual check: `python3 ferramentas/rsd_cli.py kat` and `python3 ferramentas/rsd_cli.py demo`

**Dependencies:** Task 2
**Files likely touched:** `pyproject.toml`, `requirements.txt`, `ferramentas/rsd_cli.py`, `testes/test_cli_and_repo.py`
**Estimated scope:** Medium (4 files)

---

## Checkpoint: After Tasks 1-3
- [x] All unit tests pass (`test_rsd_s_v4.py` + `test_cli_and_repo.py`)
- [x] CLI works end-to-end from repository root
- [x] Clean atomic commits recorded

---

## Task 4: OSS Governance, Legal Architecture & Commercial Strategy
**Description:** Establish complete open-source legal, security, governance, and commercial strategy documentation aligned with `/oss-business-strategy` and `/oss-governance-health`.

**Acceptance criteria:**
- [x] `LICENSE` (MIT), `TRADEMARK_POLICY.md`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `GOVERNANCE.md` exist at root
- [x] `docs/strategy/OSS_COMMERCIAL_STRATEGY.md` defines the COSS model (Open Core Cryptanalysis Workbench, SAT/SMT Cloud Verification, R&D Advisory, Public Good Grants) while strictly prohibiting unvetted production encryption claims

**Verification:**
- [x] Automated repository integrity test in `testes/test_cli_and_repo.py` verifies presence and non-empty structure of all governance files

**Dependencies:** Task 1
**Files likely touched:** `LICENSE`, `TRADEMARK_POLICY.md`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `docs/strategy/OSS_COMMERCIAL_STRATEGY.md`
**Estimated scope:** Medium (8 files)

---

## Task 5: GitHub Actions CI/CD, Templates & Repository Metadata
**Description:** Configure `.github/` automation and community templates following `/ci-cd-and-automation` and `/github-repo-growth`.

**Acceptance criteria:**
- [x] `.github/workflows/ci.yml`, `.github/workflows/release.yml`, and `.github/workflows/pages.yml` are valid YAML workflows
- [x] `.github/ISSUE_TEMPLATE/` includes `bug_report.yml`, `cryptanalysis_finding.yml`, `feature_request.yml`, and `config.yml`
- [x] `.github/PULL_REQUEST_TEMPLATE.md`, `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/dependabot.yml`, and `.github/REPO_METADATA.json` are configured

**Verification:**
- [x] Python YAML/JSON structural validation passes in `testes/test_cli_and_repo.py`

**Dependencies:** Task 3, Task 4
**Files likely touched:** `.github/workflows/*.yml`, `.github/ISSUE_TEMPLATE/*.yml`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/CODEOWNERS`, `.github/FUNDING.yml`, `.github/dependabot.yml`, `.github/REPO_METADATA.json`
**Estimated scope:** Medium (12 files)

---

## Task 6: High-Converting `README.md`, Visual SVG Assets, `CHANGELOG.md` & Launch Playbook
**Description:** Create custom vector diagrams (`docs/assets/rsd-s-architecture.svg`, `docs/assets/avalanche-evolution.svg`), a high-converting `README.md`, a human-curated `CHANGELOG.md`, and `docs/growth/GITHUB_LAUNCH_PLAYBOOK.md` (with Show HN, Reddit, and 5 curated `good-first-issue` specs).

**Acceptance criteria:**
- [x] `README.md` features above-the-fold pitch, 5 high-signal badges, SVG visual proof, `<30s` Quickstart, honest security status callout, `v0 -> v4` evolution table, Wide-Trail & SAT/SMT metrics, and architecture overview
- [x] `CHANGELOG.md` documents `v0.1.0` through `v0.4.1` in Keep a Changelog format
- [x] `docs/growth/GITHUB_LAUNCH_PLAYBOOK.md` provides Show HN, Reddit, and 5 `good-first-issue` specifications

**Verification:**
- [x] SVG XML validation and markdown link verification pass in `testes/test_cli_and_repo.py`

**Dependencies:** Task 3, Task 4, Task 5
**Files likely touched:** `README.md`, `CHANGELOG.md`, `docs/assets/rsd-s-architecture.svg`, `docs/assets/avalanche-evolution.svg`, `docs/growth/GITHUB_LAUNCH_PLAYBOOK.md`
**Estimated scope:** Medium (5 files)

---

## Task 7: Interactive Web Cryptanalysis Laboratory (`docs/index.html`) & Browser Verification
**Description:** Build a production-grade, WCAG 2.1 AA accessible Web Cryptanalysis Laboratory (`docs/index.html`, `docs/lab/styles.css`, `docs/lab/app.js`) allowing researchers and visitors to interactively explore GF(2^16) inversion, Cauchy MDS diffusion, the `v1` 128-bit truncation bug vs `v4` 256-bit `F_p` coverage, KAT vector verification, and Wide-Trail/SMT bounds.

**Acceptance criteria:**
- [x] Purpose-built dark engineering aesthetic (no generic purple AI gradients), semantic HTML landmarks, keyboard navigation, ARIA live regions, and responsive layout (`320px`, `768px`, `1024px`, `1440px`)
- [x] Interactive GF(2^16) arithmetic & bit-flip diffusion inspector works deterministically in JavaScript (`docs/lab/app.js`)
- [x] Automated runtime and DOM/JS verification passes with zero errors

**Verification:**
- [x] Node.js / headless runtime test of `docs/lab/app.js` and HTML/ARIA/CSS verification in `testes/test_cli_and_repo.py`

**Dependencies:** Task 6
**Files likely touched:** `docs/index.html`, `docs/lab/styles.css`, `docs/lab/app.js`, `testes/test_cli_and_repo.py`
**Estimated scope:** Medium (4 files)

---

## Checkpoint: Final Release Readiness
- [x] All unit tests, statistical tests, and repo integrity tests pass
- [x] Git history is clean, atomic, and tagged (`v0.4.0`, `v0.4.1`)
- [x] `git status` is clean with zero untracked or uncommitted files
