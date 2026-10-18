# Trademark & Brand Usage Policy

While the source code, DIMACS CNF formulas, SMT models, and research documentation in **BaSingSeCriptografy** (`RSD-S — Riemann Spectral Diffusion`) are available under the permissive [MIT License](LICENSE), the open-source license covers copyright only and **does not grant a license to project trademarks, service marks, or logos**.

---

## 1. Protected Marks

The following names and identifiers are protected marks ("the Marks") of the project author (**Danilo Ludgero**):

- **BaSingSeCriptografy** / **BaSingSe Cryptography**
- **RSD-S** / **Riemann Spectral Diffusion** (when referring to the official specification and reference suite)
- Official project logos, badges, and visual identity assets in `docs/assets/`

---

## 2. Permitted Uses (No Prior Written Permission Required)

You may use the Marks without prior written permission solely for:

1. **Truthful Attribution & Academic Citation**: Referring to the original research package, specification, test vectors (`testes/vetores_v4.json`), and empirical reports in academic papers, blog posts, benchmarks, and cryptanalysis papers.
2. **Unmodified Redistribution**: Redistributing exact, unmodified copies of the tagged releases (`v0.4.0+`) while retaining all copyright notices and security disclaimers.
3. **Compatibility & Interoperability Statements**: Stating truthfully that your tool or solver script analyzes or is compatible with `RSD-S v4` (e.g., *"MILP Trail Finder for RSD-S v4"*).

---

## 3. Prohibited Uses

You may **not** use the Marks in any way that implies official endorsement, security certification, or commercial affiliation without explicit written permission:

1. **Commercial Cloud / Managed Service Branding**: Third parties may fork the MIT-licensed code, but may not market a commercial product or hosted service as *"Official BaSingSeCriptografy Cloud"* or *"Certified RSD-S Security Suite"*.
2. **Misleading Security Claims**: You may **never** use the Marks to advertise or sell a product as "Post-Quantum Certified", "Shor-Proof", or "Production-Ready Encryption" in violation of [`especificacao/RESTRICOES_DE_PROJETO.md`](especificacao/RESTRICOES_DE_PROJETO.md) and [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md).
3. **Modified Derivatives Without Rename**: If you modify the round count, S-box polynomial (`0x1100B`), Cauchy MDS matrix, or input domain (`F_p`, `p = 2^255 - 19`) in a breaking manner, you must clearly label the derivative as an unofficial fork or variant so that Known-Answer Test (KAT) vectors are not confused.

---

## 4. Reporting Misuse

Questions regarding trademark usage or commercial licensing inquiries should be directed via GitHub Discussions or repository maintainer channels at [`daniloludgero/BaSingSeCriptografy`](https://github.com/daniloludgero/BaSingSeCriptografy).
