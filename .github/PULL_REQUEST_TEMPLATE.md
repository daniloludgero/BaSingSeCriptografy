## Summary of Changes

<!-- Explain the WHY behind this change, not just the what. -->

## Related Issue / Cryptanalysis Report

- Closes #

## Scope Discipline (`THINGS I DIDN'T TOUCH`)

- [ ] `implementacao/rsd_s_v4_final.py` public contract and `testes/vetores_v4.json` KAT outputs remain 100% unchanged.
- [ ] Historical implementations (`v1`, `v2`, `v3`) remain preserved for pedagogical reproducibility.

## Verification Checklist

- [ ] `python3 -m unittest discover -s testes -p "test_*.py" -v` passes 100%
- [ ] `python3 ferramentas/rsd_cli.py kat` passes all 4 Known-Answer Test vectors
- [ ] `python3 testes/suite_testes_completa.py` passes all 5 statistical checks
- [ ] Commit messages follow Conventional Commits (`feat`, `fix`, `docs`, `test`, `chore`) with DCO sign-off (`Signed-off-by:`)
- [ ] Documentation respects [`especificacao/RESTRICOES_DE_PROJETO.md`](especificacao/RESTRICOES_DE_PROJETO.md) (no unverified post-quantum or production security claims)
