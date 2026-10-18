# Implementation Plan: BaSingSeCriptografy (RSD-S v4) — Competitive Open-Source & Research Laboratory Repository

## Overview
Transform the local `rsd_final_package` directory into a competitive, publication-grade GitHub repository for `https://github.com/daniloludgero/BaSingSeCriptografy.git` ("BaSingSeCriptografy — RSD-S: Riemann Spectral Diffusion"). The repository must strictly respect and preserve the original cryptographic research source code (`especificacao/`, `ferramentas/`, `implementacao/`, `resultados/`, `testes/`, `RELATORIO_FINAL.md`) and its scientific honesty constraints (`especificacao/RESTRICOES_DE_PROJETO.md`), while layering world-class Git workflows, GitHub community/CI governance, OSS commercial strategy, high-converting visual documentation, and an accessible interactive Web Cryptanalysis Laboratory (`docs/index.html`).

## Assumptions Surface (`/using-agent-skills`)
1. **Source Code Preservation**: All original files in `especificacao/`, `ferramentas/`, `implementacao/`, `resultados/`, `testes/`, and `RELATORIO_FINAL.md` are preserved intact and committed first as the baseline foundation. A surgical 3-line `np.uint64(...)` scalar cast in `implementacao/analise_duas_rodadas.py` and `implementacao/busca_branch_bound.py` is applied in a dedicated atomic commit (`fix(compat)`) so that all 29 tests in `testes/test_rsd_s_v4.py` pass across both NumPy 1.26 (Linux CI) and NumPy 2.x (Windows).
2. **Scientific Integrity**: Every README section, commercial strategy document, launch playbook, and interactive UI element explicitly enforces the constraints in `RELATORIO_FINAL.md` and `especificacao/RESTRICOES_DE_PROJETO.md` (RSD-S is an experimental symmetric diffusion/hash research prototype; NOT audited, NOT for production use, and does NOT claim to break or supersede Shor/post-quantum standards without formal proof).
3. **Git & Remote Setup**: Because `.git/` was an empty directory and WSL has no active GitHub OAuth token stored, we initialize a full Git repository on branch `main`, configure `origin` to `https://github.com/daniloludgero/BaSingSeCriptografy.git`, build a clean atomic Conventional Commits history with semantic tags (`v0.4.0`, `v0.4.1`), and provide a one-command push verification script.

## Architecture Decisions
- **Git Workflow (`/git-workflow-and-versioning`)**: Trunk-based structure on `main` with atomic Conventional Commits (`feat`, `fix`, `docs`, `ci`, `chore`, `test`), `.gitignore`, `.gitattributes`, `CHANGELOG.md` (Keep a Changelog format), and annotated release tags (`v0.4.0`, `v0.4.1`).
- **GitHub Repo Growth (`/github-repo-growth`)**: Above-the-fold `README.md` with custom SVG architectural & avalanche telemetry diagrams (`docs/assets/rsd-s-architecture.svg`, `docs/assets/avalanche-evolution.svg`), <30-second Quickstart via `pyproject.toml` and `ferramentas/rsd_cli.py`, `CITATION.cff`, `.github/REPO_METADATA.json`, and a multi-channel launch & contributor acquisition playbook (`docs/growth/GITHUB_LAUNCH_PLAYBOOK.md`).
- **OSS Business & Governance Strategy (`/oss-business-strategy` & `/oss-governance-health`)**: Permissive `LICENSE` (MIT) paired with `TRADEMARK_POLICY.md`, `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `docs/strategy/OSS_COMMERCIAL_STRATEGY.md` detailing ethical COSS monetization (Open Core Cryptanalysis Workbench, Formal SAT/SMT Verification Cloud, R&D Advisory, and Public Good Grants).
- **Interactive Cryptographic Web Lab (`/frontend-ui-engineering` & `/browser-testing-with-devtools`)**: Zero-dependency, WCAG 2.1 AA compliant interactive laboratory (`docs/index.html`, `docs/lab/styles.css`, `docs/lab/app.js`) featuring live GF(2^16) polynomial arithmetic (`0x1100B`), interactive `v1` (128-bit truncation bug) vs `v4` (256-bit full `F_p` coverage) bit-flip simulator, 32-word state diffusion inspector, Known-Answer Vector (KAT) verifier, and Wide-Trail / SMT / SAT cryptanalysis explorer.

## Dependency Graph
```
Task 1: Git Initialization & Baseline Import (Original Code)
  └── Task 2: NumPy 1.x/2.x Compatibility Fix & Full Test Verification
        ├── Task 3: Packaging (`pyproject.toml`) & Fast CLI (`ferramentas/rsd_cli.py`)
        ├── Task 4: OSS Legal, Governance & Commercial Strategy Docs
        ├── Task 5: GitHub Actions CI/CD, Issue/PR Templates & Metadata
        ├── Task 6: Custom SVG Visual Diagrams & High-Converting `README.md` + `CHANGELOG.md`
        └── Task 7: Interactive Web Cryptanalysis Lab (`docs/index.html`) + Automated Verification
```

## Task List

### Phase 1: Foundation & Core Verification
- [x] Task 1: Initialize Git repository, `.gitignore`, `.gitattributes`, remote `origin`, and commit untouched original package
- [x] Task 2: Fix NumPy 1.26 `uint64` in-place XOR scalar casting in analysis modules and verify all 29 unit tests pass
- [x] Task 3: Add `pyproject.toml` and `ferramentas/rsd_cli.py` for <30s developer onboarding + CLI unit tests

### Checkpoint: Foundation
- [x] Original files preserved; `python3 -m unittest discover -s testes -p "test_*.py" -v` passes 100%

### Phase 2: OSS Strategy, Governance & GitHub Platform Engineering
- [x] Task 4: Create `LICENSE`, `TRADEMARK_POLICY.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `CITATION.cff`, and `docs/strategy/OSS_COMMERCIAL_STRATEGY.md`
- [x] Task 5: Create `.github/` workflows (`ci.yml`, `release.yml`, `pages.yml`), issue/PR templates, `dependabot.yml`, `FUNDING.yml`, and `REPO_METADATA.json`

### Checkpoint: Core Features
- [x] All governance, legal, CI/CD, and commercial strategy artifacts validated

### Phase 3: Growth Engineering, Visual Assets & Interactive Web Laboratory
- [x] Task 6: Create SVG visual proof assets (`docs/assets/`), `README.md`, `CHANGELOG.md`, and `docs/growth/GITHUB_LAUNCH_PLAYBOOK.md`
- [x] Task 7: Build Interactive Web Cryptanalysis Lab (`docs/index.html`, `docs/lab/styles.css`, `docs/lab/app.js`) and verify DOM/accessibility/console/runtime

### Checkpoint: Complete
- [x] All acceptance criteria met
- [x] Annotated git tags minted and repository ready for `git push -u origin main --tags`

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| NumPy 1.26 vs 2.x scalar casting difference in `uint64 ^= int` | High (causes 5 errors in `test_rsd_s_v4.py` on Linux NumPy 1.26) | Commit original files first, then apply explicit `np.uint64(...)` cast in a dedicated `fix(compat)` commit and verify all 29 tests pass. |
| Overstating cryptographic security in marketing/README materials | High (violates `RELATORIO_FINAL.md` and `RESTRICOES_DE_PROJETO.md`) | Embed prominent non-production warnings and exact mathematical scope boundaries in `README.md`, `SECURITY.md`, launch playbooks, and the Web Lab UI. |
| Pushing to remote without credentials in non-interactive shell | Low | Configure remote `origin` (`https://github.com/daniloludgero/BaSingSeCriptografy.git`), branches, and tags locally so user can push with one command. |

## Open Questions
- None; all requirements and constraints are specified in `<original_task>`, `RELATORIO_FINAL.md`, and `especificacao/RESTRICOES_DE_PROJETO.md`.
