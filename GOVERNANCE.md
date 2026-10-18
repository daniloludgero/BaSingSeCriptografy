# Project Governance & Maintainer Succession (`GOVERNANCE.md`)

This document defines the governance structure, decision-making protocols, contributor advancement ladder, and operational security rules for **BaSingSeCriptografy (`RSD-S`)**.

---

## 1. Governance Model: BDFL with RFC Consensus Path

`BaSingSeCriptografy` currently operates under a **Benevolent Dictator For Life (BDFL)** model led by the original author (**Danilo Ludgero**), designed to transition smoothly to a **Technical Steering Committee (TSC)** as the contributor base scales beyond 3 active core maintainers.

```
┌─────────────────────────────────────────────────────────────┐
│                 GOVERNANCE MATURITY ROADMAP                 │
│                                                             │
│  [Phase 1: BDFL] ──────▶ [Phase 2: Core Team / TSC]         │
│  Danilo Ludgero          ≥ 3 Active Maintainers             │
│  Architectural Integrity Apache-Style Voting + RFCs         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Contributor Advancement Ladder

We maintain a transparent 5-tier contributor ladder so every community researcher and engineer has a clear pathway to leadership:

| Tier | Role | Qualification Criteria | Authority & Privileges |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **User / Researcher** | Runs the suite, verifies KAT vectors, or participates in Discussions. | Open issues, submit cryptanalysis reports, propose ideas. |
| **Tier 2** | **Contributor** | ≥ 2 non-trivial merged PRs (cryptanalysis scripts, CNF/SMT models, documentation, or UI improvements) with DCO sign-off. | Listed in release notes and contributor acknowledgments. |
| **Tier 3** | **Member / Triager** | Sustained contribution over ≥ 60 days; demonstrated understanding of `RESTRICOES_DE_PROJETO.md`. | Triage privileges: label issues, reproduce cryptanalysis reports, manage milestones. |
| **Tier 4** | **Reviewer / Approver** | Deep expertise in finite-field arithmetic, SAT/SMT solvers, or frontend laboratory architecture. | Approve and merge PRs in designated subsystems (`implementacao/`, `ferramentas/`, `docs/`). |
| **Tier 5** | **Core Maintainer / TSC** | Nominated by existing maintainers after ≥ 6 months of high-impact technical stewardship. | Repository administration, release tagging, security advisory publication, RFC voting. |

---

## 3. Formal Decision-Making & RFC Workflow

### A. Routine Changes (Lazy Consensus)
Non-breaking improvements (new analysis scripts, documentation clarifications, performance optimizations, Web Lab enhancements) follow **Lazy Consensus**:
- A PR is opened and passes all CI quality gates.
- If no reviewer raises a reasoned technical objection within **72 hours**, the change may be merged.

### B. Breaking Specification Changes (`RSD-S v5+` RFC Process)
Any change that alters the `v4` state width, S-box polynomial (`0x1100B`), Cauchy MDS matrix, key schedule, or round count (`R = 4`) **must** go through a formal Request for Comments (RFC):
1. **Draft Proposal**: Submit an RFC document in `especificacao/` detailing the mathematical motivation, empirical benchmarks, and Wide-Trail / SMT impact.
2. **Public Cryptanalysis Period**: Minimum **14 days** open for community counterexamples.
3. **Voting Protocol**:
   - `+1`: Endorse with verification evidence.
   - ` 0`: Neutral / Abstain.
   - `-1`: Technical Veto (must be accompanied by a reproducible counterexample, regression proof, or concrete alternative).

---

## 4. Community Health SLAs (CHAOSS Standards)

We track and hold ourselves accountable to the following responsiveness targets:

| Metric | Target SLA | Alert Threshold |
| :--- | :--- | :--- |
| **Time to First Human Response (Issues/PRs)** | `< 24 Hours` | `> 72 Hours` |
| **PR Review & Merge/Close Cycle** | `< 14 Days` | `> 45 Days` |
| **Target Bus Factor** | `≥ 3 Maintainers` | `= 1 Maintainer` (Active mentoring priority) |

---

## 5. Operational Security & Maintainer Emeritus Protocol

1. **Hardware/2FA Custody**: All maintainers with write or release permissions must enforce strong two-factor authentication (2FA) on GitHub.
2. **Signed Releases & Tags**: Official version releases (`v0.4.0`, `v0.4.1`, etc.) are minted via annotated Git tags verified by GitHub Actions CI.
3. **Maintainer Emeritus Transition**: Maintainers inactive for `> 6 months` are honored as *Maintainer Emeritus* in this document, and write tokens are rotated to minimize supply-chain exposure.
