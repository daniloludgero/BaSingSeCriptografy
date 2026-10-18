#!/usr/bin/env python3
"""CLI de inspeção rápida, verificação KAT e demonstração pedagógica do RSD-S v4.

Permite avaliar a primitiva de pesquisa RSD-S em menos de 30 segundos sem alterar
os módulos originais em `implementacao/`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "implementacao"))

from analise_wide_trail import bound_for_rounds, min_active_sboxes_dp  # noqa: E402
from rsd_s_v1_original import diffuse_rsd_s as diffuse_v1_original  # noqa: E402
from rsd_s_v4_final import (  # noqa: E402
    P_CURVE25519,
    diffuse_rsd_s_final,
    diffuse_rsd_s_rounds,
    diffuse_rsd_s_rounds_PRE_SHA,
    get_base_inversion_sbox,
)


def _hamming_bits(left: bytes, right: bytes) -> int:
    return sum((a ^ b).bit_count() for a, b in zip(left, right))


def cmd_kat(as_json: bool = False) -> int:
    vector_path = ROOT / "testes" / "vetores_v4.json"
    vectors = json.loads(vector_path.read_text(encoding="utf-8"))
    t0 = time.perf_counter()
    get_base_inversion_sbox()
    results: list[dict[str, Any]] = []
    all_ok = True

    for vec in vectors:
        actual = diffuse_rsd_s_final(
            int(vec["x"]),
            int(vec["y"]),
            bytes.fromhex(vec["s_hex"]),
            int(vec["n_sess"]),
        ).hex()
        matched = actual == vec["output_hex"]
        all_ok = all_ok and matched
        results.append(
            {
                "name": vec["name"],
                "matched": matched,
                "expected": vec["output_hex"],
                "actual": actual,
            }
        )

    elapsed = time.perf_counter() - t0
    if as_json:
        print(
            json.dumps(
                {
                    "status": "PASS" if all_ok else "FAIL",
                    "vectors_checked": len(results),
                    "elapsed_seconds": round(elapsed, 3),
                    "results": results,
                },
                indent=2,
            )
        )
    else:
        print("=" * 72)
        print("RSD-S v4 — Known-Answer Test (KAT) Verification")
        print("=" * 72)
        for item in results:
            badge = "PASS" if item["matched"] else "FAIL"
            print(f"  [{badge}] {item['name']:<18} -> {item['actual'][:32]}...")
        print("-" * 72)
        print(
            f"Summary: {sum(r['matched'] for r in results)}/{len(results)} vectors matched "
            f"in {elapsed:.2f}s"
        )
    return 0 if all_ok else 1


def cmd_bounds(rounds_list: list[int], as_json: bool = False) -> int:
    rows: list[dict[str, Any]] = []
    for r in rounds_list:
        if r < 1 or r > 255:
            print(f"Error: rounds must be in 1..255 (got {r})", file=sys.stderr)
            return 2
        b = bound_for_rounds(r)
        _, pattern = min_active_sboxes_dp(r)
        rows.append(
            {
                "rounds": b.rounds,
                "min_active_sboxes": b.min_active_sboxes,
                "activity_pattern": list(pattern),
                "diff_log2_prob_upper": b.differential_log2_probability_upper,
                "linear_log2_corr_upper": b.linear_log2_correlation_upper,
                "linear_log2_bias_upper": b.linear_log2_bias_upper,
            }
        )

    if as_json:
        print(json.dumps({"wide_trail_bounds": rows}, indent=2))
    else:
        print("=" * 72)
        print("RSD-S v4 — Conservative Wide-Trail Single-Characteristic Bounds")
        print("(Cauchy MDS 32x32 Branch Number = 33 | GF(2^16) Inv Max DDT = 2^-14)")
        print("=" * 72)
        print(f"{'Rounds':>6} | {'Active S-Boxes':>14} | {'Diff Bound':>12} | {'Lin Corr Bound':>14}")
        print("-" * 72)
        for row in rows:
            print(
                f"{row['rounds']:>6} | {row['min_active_sboxes']:>14} | "
                f"2^{row['diff_log2_prob_upper']:<10} | 2^{row['linear_log2_corr_upper']:<12}"
            )
        print("-" * 72)
        print("Note: Bounds apply to individual characteristics, not full differential hulls.")
    return 0


def cmd_demo(as_json: bool = False) -> int:
    get_base_inversion_sbox()
    key = bytes.fromhex("a5" * 32)
    session = 7
    x = 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF % P_CURVE25519
    y = 0xFEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA987654321 % P_CURVE25519
    high_bit = 200
    x_flipped = x ^ (1 << high_bit)

    v1_base = diffuse_v1_original(x, y, key, session)
    v1_flip = diffuse_v1_original(x_flipped, y, key, session)
    v1_diff_bits = _hamming_bits(v1_base, v1_flip)

    v4_base = diffuse_rsd_s_final(x, y, key, session)
    v4_flip = diffuse_rsd_s_final(x_flipped, y, key, session)
    v4_diff_bits = _hamming_bits(v4_base, v4_flip)

    bound4 = bound_for_rounds(4)
    payload = {
        "prototype_warning": (
            "Research prototype ONLY. NOT audited, NOT constant-time, "
            "NOT recommended for production use."
        ),
        "high_bit_truncation_comparison": {
            "flipped_bit": high_bit,
            "v1_changed_bits_out_of_256": v1_diff_bits,
            "v1_avalanche_percent": round(v1_diff_bits / 256 * 100, 2),
            "v4_changed_bits_out_of_256": v4_diff_bits,
            "v4_avalanche_percent": round(v4_diff_bits / 256 * 100, 2),
        },
        "v4_digest_hex": v4_base.hex(),
        "four_round_wide_trail_min_active_sboxes": bound4.min_active_sboxes,
        "four_round_wide_trail_diff_bound_log2": bound4.differential_log2_probability_upper,
    }

    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("=" * 72)
        print("BaSingSeCriptografy — RSD-S v1 vs v4 Diagnostic Demonstration")
        print("WARNING: Experimental research prototype. Do NOT use in production.")
        print("=" * 72)
        print(f"Input x (mod 2^255-19) bit #{high_bit} flipped:")
        print(
            f"  [v1 Original] Changed bits: {v1_diff_bits:3d}/256 "
            f"({v1_diff_bits / 256 * 100:5.2f}%) -> COLLISION BUG (bits 128..254 silently dropped)"
        )
        print(
            f"  [v4 Final   ] Changed bits: {v4_diff_bits:3d}/256 "
            f"({v4_diff_bits / 256 * 100:5.2f}%) -> FULL F_p COVERAGE & AVALANCHE"
        )
        print("-" * 72)
        print(f"v4 Digest (base):    {v4_base.hex()}")
        print(f"v4 Digest (flipped): {v4_flip.hex()}")
        print(
            f"4-Round Wide-Trail:  >= {bound4.min_active_sboxes} active S-boxes "
            f"(single-characteristic bound <= 2^{bound4.differential_log2_probability_upper})"
        )
    return 0


def cmd_hash(
    x_str: str,
    y_str: str,
    key_hex: str,
    session: int,
    rounds: int,
    as_json: bool = False,
) -> int:
    try:
        x = int(x_str, 0)
        y = int(y_str, 0)
        key = bytes.fromhex(key_hex)
        digest = (
            diffuse_rsd_s_final(x, y, key, session)
            if rounds == 4
            else diffuse_rsd_s_rounds(x, y, key, session, rounds)
        )
        pre_sha = diffuse_rsd_s_rounds_PRE_SHA(x, y, key, session, rounds)
    except (TypeError, ValueError) as exc:
        print(f"Input validation error: {exc}", file=sys.stderr)
        return 2

    state_hex = [f"0x{int(w):04x}" for w in pre_sha]
    if as_json:
        print(
            json.dumps(
                {
                    "x": str(x),
                    "y": str(y),
                    "session": session,
                    "rounds": rounds,
                    "digest_hex": digest.hex(),
                    "pre_sha_words_hex": state_hex,
                },
                indent=2,
            )
        )
    else:
        print(f"Digest ({rounds} rounds): {digest.hex()}")
        print(f"Pre-SHA 512-bit state (first 8 words): {' '.join(state_hex[:8])} ...")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rsd_cli",
        description="RSD-S v4 Cryptographic Research & Verification CLI",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("kat", help="Verify all Known-Answer Test (KAT) vectors from vetores_v4.json")
    sub.add_parser("demo", help="Run interactive v1 vs v4 high-bit truncation & avalanche demo")

    bounds_p = sub.add_parser("bounds", help="Compute conservative Wide-Trail bounds")
    bounds_p.add_argument(
        "--rounds",
        type=int,
        nargs="+",
        default=[4, 6, 8, 10],
        help="Round counts to evaluate (default: 4 6 8 10)",
    )

    hash_p = sub.add_parser("hash", help="Evaluate RSD-S v4 on explicit inputs")
    hash_p.add_argument("--x", required=True, help="Field element x in 0 <= x < 2^255 - 19")
    hash_p.add_argument("--y", required=True, help="Field element y in 0 <= y < 2^255 - 19")
    hash_p.add_argument(
        "--key-hex",
        default="00" * 32,
        help="32-byte key encoded as 64 hex characters",
    )
    hash_p.add_argument("--session", type=int, default=0, help="64-bit unsigned session nonce")
    hash_p.add_argument("--rounds", type=int, default=4, help="Round count (1..255, official=4)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "kat":
        return cmd_kat(as_json=args.json)
    if args.command == "demo":
        return cmd_demo(as_json=args.json)
    if args.command == "bounds":
        return cmd_bounds(args.rounds, as_json=args.json)
    if args.command == "hash":
        return cmd_hash(
            args.x,
            args.y,
            args.key_hex,
            args.session,
            args.rounds,
            as_json=args.json,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
