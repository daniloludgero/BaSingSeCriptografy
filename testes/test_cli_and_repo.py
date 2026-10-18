"""Testes automatizados para a CLI (`rsd_cli.py`), governança OSS e Laboratório Web (`docs/`)."""

from __future__ import annotations

from html.parser import HTMLParser
import io
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr, redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "implementacao"))
sys.path.insert(0, str(ROOT / "ferramentas"))

import rsd_cli  # noqa: E402
from rsd_s_v4_final import P_CURVE25519  # noqa: E402


class _A11yHtmlInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.landmarks: set[str] = set()
        self.headings: list[str] = []
        self.labels_for: set[str] = set()
        self.input_ids: set[str] = set()
        self.has_live_region = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag in ("header", "main", "nav", "section", "footer"):
            self.landmarks.add(tag)
        if tag in ("h1", "h2", "h3"):
            self.headings.append(tag)
        if tag == "label" and attr_map.get("for"):
            self.labels_for.add(str(attr_map["for"]))
        if tag in ("input", "select") and attr_map.get("id"):
            self.input_ids.add(str(attr_map["id"]))
        if attr_map.get("aria-live") == "polite":
            self.has_live_region = True


class TestCliCommands(unittest.TestCase):
    def _run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = rsd_cli.main(argv)
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 2
        return code, out.getvalue(), err.getvalue()

    def test_cli_kat_json_passes_all_vectors(self) -> None:
        code, stdout, stderr = self._run_cli(["--json", "kat"])
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["vectors_checked"], 4)
        self.assertTrue(all(item["matched"] for item in payload["results"]))

    def test_cli_demo_json_exposes_v1_truncation_vs_v4_coverage(self) -> None:
        code, stdout, stderr = self._run_cli(["--json", "demo"])
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        comp = payload["high_bit_truncation_comparison"]
        self.assertEqual(comp["flipped_bit"], 200)
        self.assertEqual(comp["v1_changed_bits_out_of_256"], 0)
        self.assertGreater(comp["v4_changed_bits_out_of_256"], 100)
        self.assertEqual(payload["four_round_wide_trail_min_active_sboxes"], 66)

    def test_cli_bounds_json_and_invalid_round_edge_cases(self) -> None:
        code, stdout, _ = self._run_cli(["--json", "bounds", "--rounds", "4", "6"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(
            [item["min_active_sboxes"] for item in payload["wide_trail_bounds"]],
            [66, 99],
        )

        for bad_round in ("0", "256", "-3"):
            with self.subTest(bad_round=bad_round):
                bad_code, _, bad_err = self._run_cli(["bounds", "--rounds", bad_round])
                self.assertEqual(bad_code, 2)
                self.assertIn("error", bad_err.lower())

    def test_cli_hash_matches_kat_and_rejects_invalid_inputs(self) -> None:
        code, stdout, stderr = self._run_cli(
            [
                "--json",
                "hash",
                "--x",
                "1",
                "--y",
                "2",
                "--key-hex",
                "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
                "--session",
                "1",
            ]
        )
        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(
            payload["digest_hex"],
            "38659dbb20ab18e575e635a708bdd67131ab6afefc79b253c246ced16e8a41ac",
        )
        self.assertEqual(len(payload["pre_sha_words_hex"]), 32)

        # Edge cases: x = P_CURVE25519 (out of domain), negative x, bad key length, bad session
        invalid_cases = [
            ["hash", "--x", str(P_CURVE25519), "--y", "0"],
            ["hash", "--x", "-1", "--y", "0"],
            ["hash", "--x", "0", "--y", "0", "--key-hex", "0011"],
            ["hash", "--x", "0", "--y", "0", "--session", "-1"],
            ["hash", "--x", "0", "--y", "0", "--rounds", "0"],
        ]
        for case in invalid_cases:
            with self.subTest(case=case):
                err_code, _, err_out = self._run_cli(case)
                self.assertEqual(err_code, 2)
                self.assertIn("Input validation error", err_out)


class TestRepositoryGovernanceAndWebLab(unittest.TestCase):
    def test_required_oss_and_github_files_exist(self) -> None:
        required_files = [
            "README.md",
            "RELATORIO_FINAL.md",
            "CHANGELOG.md",
            "LICENSE",
            "TRADEMARK_POLICY.md",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "GOVERNANCE.md",
            "CITATION.cff",
            "pyproject.toml",
            "requirements.txt",
            ".gitignore",
            ".gitattributes",
            ".github/REPO_METADATA.json",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/CODEOWNERS",
            ".github/FUNDING.yml",
            ".github/dependabot.yml",
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
            ".github/workflows/pages.yml",
            "docs/index.html",
            "docs/lab/styles.css",
            "docs/lab/app.js",
            "docs/assets/rsd-s-architecture.svg",
            "docs/assets/avalanche-evolution.svg",
            "docs/strategy/OSS_COMMERCIAL_STRATEGY.md",
            "docs/growth/GITHUB_LAUNCH_PLAYBOOK.md",
        ]
        for rel_path in required_files:
            with self.subTest(path=rel_path):
                path = ROOT / rel_path
                self.assertTrue(path.is_file(), f"Missing required file: {rel_path}")
                self.assertGreater(path.stat().st_size, 20, f"Empty file: {rel_path}")

    def test_repo_metadata_adheres_to_github_seo_constraints(self) -> None:
        meta = json.loads((ROOT / ".github" / "REPO_METADATA.json").read_text(encoding="utf-8"))
        self.assertLessEqual(len(meta["description"]), 120)
        self.assertGreaterEqual(len(meta["topics"]), 5)
        self.assertLessEqual(len(meta["topics"]), 8)

    def test_svg_visual_assets_are_valid_xml(self) -> None:
        for svg_name in ("rsd-s-architecture.svg", "avalanche-evolution.svg"):
            with self.subTest(svg=svg_name):
                svg_path = ROOT / "docs" / "assets" / svg_name
                root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
                self.assertTrue(root.tag.endswith("svg"))

    def test_web_lab_html_accessibility_and_kat_parity(self) -> None:
        html_text = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        inspector = _A11yHtmlInspector()
        inspector.feed(html_text)

        self.assertEqual(
            inspector.landmarks,
            {"header", "main", "nav", "section", "footer"},
        )
        self.assertEqual(inspector.headings[0], "h1")
        self.assertEqual(inspector.headings.count("h1"), 1)
        self.assertTrue(inspector.has_live_region)
        self.assertTrue(inspector.input_ids.issubset(inspector.labels_for))

        # Ensure all 4 official KAT digests appear in docs/lab/app.js
        js_text = (ROOT / "docs" / "lab" / "app.js").read_text(encoding="utf-8")
        vectors = json.loads((ROOT / "testes" / "vetores_v4.json").read_text(encoding="utf-8"))
        for vec in vectors:
            self.assertIn(vec["output_hex"], js_text)


if __name__ == "__main__":
    unittest.main()
