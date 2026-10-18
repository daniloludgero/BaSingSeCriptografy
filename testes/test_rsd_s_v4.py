"""Testes automatizados, determinísticos e portáteis da API RSD-S v4."""

from __future__ import annotations

import json
from pathlib import Path
import statistics
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "implementacao"))

from rsd_s_v4_final import (  # noqa: E402
    KEY_SIZE,
    MAX_SESSION,
    P_CURVE25519,
    M_CAUCHY_32,
    diffuse_rsd_s_final,
    diffuse_rsd_s_rounds,
    diffuse_rsd_s_rounds_PRE_SHA,
    fragment_full,
    gf_matrix_vector_mult,
    get_base_inversion_sbox,
)
from analise_wide_trail import (  # noqa: E402
    bound_for_rounds,
    min_active_sboxes,
    min_active_sboxes_dp,
)
from analise_trilhas_concretas import analyze_single_active  # noqa: E402
from mds_bitmatrix import apply_mds_bitmatrix, mds_bit_rows  # noqa: E402
from mds_xor_synthesis import build_mds_xor_circuit, evaluate_circuit  # noqa: E402
from gf16_inverse_cnf import accepts_pair, build_inverse_cnf  # noqa: E402
from mds_real import gf_inv  # noqa: E402
from rsd_round_cnf import evaluate_fixed_first_round  # noqa: E402
from rsd_differential_cnf import build_compact_max_transition  # noqa: E402
from analise_duas_rodadas import analyze_all_witnesses, analyze_full_witness  # noqa: E402
from busca_branch_bound import (  # noqa: E402
    TwoRoundEvaluator, expand_candidate, maximum_transition_witnesses, search,
)
from busca_diversificada import (  # noqa: E402
    count_two_transition_witnesses,
    deterministic_backgrounds,
    search_diversified,
)


def hamming_distance(a: bytes, b: bytes) -> int:
    return sum((left ^ right).bit_count() for left, right in zip(a, b))


class TestKnownAnswerVectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vector_path = Path(__file__).with_name("vetores_v4.json")
        cls.vectors = json.loads(vector_path.read_text(encoding="utf-8"))
        get_base_inversion_sbox()

    def test_known_answers(self) -> None:
        for vector in self.vectors:
            with self.subTest(vector=vector["name"]):
                output = diffuse_rsd_s_final(
                    int(vector["x"]),
                    int(vector["y"]),
                    bytes.fromhex(vector["s_hex"]),
                    int(vector["n_sess"]),
                )
                self.assertEqual(output.hex(), vector["output_hex"])

    def test_determinism(self) -> None:
        vector = self.vectors[1]
        args = (
            int(vector["x"]),
            int(vector["y"]),
            bytes.fromhex(vector["s_hex"]),
            int(vector["n_sess"]),
        )
        self.assertEqual(diffuse_rsd_s_final(*args), diffuse_rsd_s_final(*args))

    def test_official_api_is_identical_to_four_round_variant(self) -> None:
        vector = self.vectors[2]
        args = (
            int(vector["x"]),
            int(vector["y"]),
            bytes.fromhex(vector["s_hex"]),
            int(vector["n_sess"]),
        )
        self.assertEqual(
            diffuse_rsd_s_final(*args),
            diffuse_rsd_s_rounds(*args, rounds=4),
        )


class TestInputContract(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = (0, 0, bytes(KEY_SIZE), 0)

    def test_rejects_field_values_outside_domain(self) -> None:
        for position, bad_value in ((0, -1), (0, P_CURVE25519), (1, -1), (1, P_CURVE25519)):
            args = list(self.valid)
            args[position] = bad_value
            with self.subTest(position=position, value=bad_value):
                with self.assertRaises(ValueError):
                    diffuse_rsd_s_final(*args)

    def test_rejects_non_integer_field_values(self) -> None:
        for value in (True, 1.5, "1"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    diffuse_rsd_s_final(value, *self.valid[1:])

    def test_requires_32_byte_key(self) -> None:
        for key in (b"", bytes(KEY_SIZE - 1), bytes(KEY_SIZE + 1)):
            with self.subTest(length=len(key)):
                with self.assertRaises(ValueError):
                    diffuse_rsd_s_final(0, 0, key, 0)
        with self.assertRaises(TypeError):
            diffuse_rsd_s_final(0, 0, bytearray(KEY_SIZE), 0)

    def test_rejects_session_outside_uint64(self) -> None:
        for value in (-1, MAX_SESSION + 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    diffuse_rsd_s_final(0, 0, bytes(KEY_SIZE), value)

    def test_rejects_invalid_experimental_round_count(self) -> None:
        for value in (0, 256, -1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    diffuse_rsd_s_rounds(*self.valid, rounds=value)
        for value in (True, 1.5, "4"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    diffuse_rsd_s_rounds(*self.valid, rounds=value)
        for value in (True, 1.5, "1"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    diffuse_rsd_s_final(0, 0, bytes(KEY_SIZE), value)

    def test_fragmentation_round_trip(self) -> None:
        x = P_CURVE25519 - 1
        y = P_CURVE25519 - 2
        words = fragment_full(x, y)
        rebuilt_x = sum(int(words[index]) << (16 * index) for index in range(16))
        rebuilt_y = sum(int(words[index + 16]) << (16 * index) for index in range(16))
        self.assertEqual((rebuilt_x, rebuilt_y), (x, y))


class TestFixedKeyDiffusion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        get_base_inversion_sbox()

    def test_key_and_session_separation(self) -> None:
        x, y = 123456789, 987654321
        base = diffuse_rsd_s_final(x, y, bytes(32), 0)
        changed_key = diffuse_rsd_s_final(x, y, b"\x01" + bytes(31), 0)
        changed_session = diffuse_rsd_s_final(x, y, bytes(32), 1)
        self.assertNotEqual(base, changed_key)
        self.assertNotEqual(base, changed_session)
        self.assertNotEqual(changed_key, changed_session)

    def test_avalanche_with_fixed_key_per_input_region(self) -> None:
        key = bytes.fromhex("5a" * 32)
        session = 0x0123456789ABCDEF
        positions = (0, 63, 127, 128, 191, 254)
        fractions: list[float] = []

        # Entradas determinísticas e abaixo de 2^254 garantem que o flip do
        # bit 254 continue dentro de F_p.
        for trial in range(6):
            x = (trial + 1) * 0x123456789ABCDEF
            y = (trial + 1) * 0xFEDCBA987654321
            base = diffuse_rsd_s_final(x, y, key, session)
            for bit in positions:
                changed = diffuse_rsd_s_final(x ^ (1 << bit), y, key, session)
                distance = hamming_distance(base, changed)
                self.assertGreater(distance, 0, f"bit de entrada {bit} não alterou a saída")
                fractions.append(distance / 256)

        mean = statistics.mean(fractions)
        self.assertGreaterEqual(mean, 0.45)
        self.assertLessEqual(mean, 0.55)

    def test_cached_sbox_is_read_only(self) -> None:
        sbox = get_base_inversion_sbox()
        with self.assertRaises(ValueError):
            sbox[0] = 1


class TestWideTrailBounds(unittest.TestCase):
    def test_minimum_active_sboxes(self) -> None:
        expected = {1: 1, 2: 33, 4: 66, 6: 99, 8: 132, 10: 165}
        for rounds, active in expected.items():
            with self.subTest(rounds=rounds):
                self.assertEqual(min_active_sboxes(rounds), active)
                dp_active, pattern = min_active_sboxes_dp(rounds)
                self.assertEqual(dp_active, active)
                self.assertEqual(len(pattern), rounds)
                self.assertTrue(
                    all(left + right >= 33 for left, right in zip(pattern, pattern[1:]))
                )

    def test_characteristic_bounds(self) -> None:
        four = bound_for_rounds(4)
        self.assertEqual(four.differential_log2_probability_upper, -924)
        self.assertEqual(four.linear_log2_correlation_upper, -462)
        self.assertEqual(four.linear_log2_bias_upper, -463)


class TestConcreteDifferentialTrails(unittest.TestCase):
    def test_single_active_maximum_probability_paths(self) -> None:
        trails = analyze_single_active(4)
        self.assertEqual(len(trails), 32)
        self.assertEqual({trail.active_weights for trail in trails}, {(1, 32, 31, 32)})
        self.assertEqual({trail.active_sboxes for trail in trails}, {96})
        self.assertEqual({trail.differential_log2_probability for trail in trails}, {-1344})


class TestMdsBooleanCircuit(unittest.TestCase):
    def test_all_basis_vectors_match_gf_implementation(self) -> None:
        rows = mds_bit_rows()
        self.assertEqual(len(rows), 512)
        for source in range(512):
            vector = np.zeros(32, dtype=np.uint32)
            vector[source // 16] = 1 << (source % 16)
            self.assertTrue(
                np.array_equal(
                    apply_mds_bitmatrix(vector),
                    gf_matrix_vector_mult(M_CAUCHY_32, vector, 32),
                )
            )

    def test_synthesized_xor_circuit(self) -> None:
        circuit = build_mds_xor_circuit()
        self.assertLess(len(circuit.gates), circuit.direct_gate_count)
        generator = np.random.default_rng(0x44414E494C4F)
        for _ in range(16):
            vector = generator.integers(0, 1 << 16, size=32, dtype=np.uint32)
            expected = gf_matrix_vector_mult(M_CAUCHY_32, vector, 32)
            self.assertTrue(np.array_equal(evaluate_circuit(circuit, vector), expected))


class TestInverseCnf(unittest.TestCase):
    def test_inverse_relation_accepts_correct_pairs(self) -> None:
        for value in (0, 1, 2, 3, 0x015E, 0x1234, 0x8000, 0xFFFF):
            with self.subTest(value=value):
                self.assertTrue(accepts_pair(value, gf_inv(value)))

    def test_inverse_relation_rejects_wrong_pairs(self) -> None:
        for value in (0, 1, 2, 3, 0x015E, 0x1234, 0x8000, 0xFFFF):
            wrong = gf_inv(value) ^ 1
            with self.subTest(value=value):
                self.assertFalse(accepts_pair(value, wrong))

    def test_inverse_cnf_size(self) -> None:
        component = build_inverse_cnf()
        self.assertEqual(component.variable_count, 575)
        self.assertEqual(len(component.clauses), 1962)

    def test_fixed_round_evaluator_matches_official_core(self) -> None:
        key = bytes.fromhex("a5" * 32)
        expected = diffuse_rsd_s_rounds_PRE_SHA(1, 2, key, 7, 1)
        self.assertTrue(np.array_equal(evaluate_fixed_first_round(1, 2, key, 7), expected))


class TestDifferentialCnf(unittest.TestCase):
    def test_compact_query_structure(self) -> None:
        correct = build_compact_max_transition(1)
        wrong = build_compact_max_transition(1, wrong_output_bit=0)
        self.assertEqual(correct.builder.variable_count, 46217)
        self.assertEqual(len(correct.builder.clauses or []), 184749)
        self.assertEqual(correct.builder.variable_count, wrong.builder.variable_count)
        self.assertEqual(len(correct.builder.clauses or []), len(wrong.builder.clauses or []))
        self.assertFalse(correct.intentionally_wrong)
        self.assertTrue(wrong.intentionally_wrong)

    def test_two_round_concrete_witnesses(self) -> None:
        trails = analyze_all_witnesses()
        self.assertEqual([trail.witness for trail in trails], [0, 1, 0x015E, 0x015F])
        self.assertEqual({trail.round_two_input_weight for trail in trails}, {32})
        self.assertEqual({trail.round_two_max_transitions for trail in trails}, {0})
        self.assertEqual({trail.probability_log2 for trail in trails}, {-494})
        self.assertEqual({trail.round_two_output_weight for trail in trails}, {32})
        self.assertEqual(len({trail.second_sbox_difference for trail in trails}), 2)

    def test_four_round_globally_compatible_characteristics(self) -> None:
        trails = [analyze_full_witness(value) for value in (0, 1, 0x015E, 0x015F)]
        expected = ((1, 1, 14), (32, 0, 480), (32, 0, 480), (32, 0, 480))
        self.assertEqual({trail.round_stats for trail in trails}, {expected})
        self.assertEqual({trail.characteristic_log2_weight for trail in trails}, {-1454})
        self.assertEqual({trail.final_active_words for trail in trails}, {32})

    def test_branch_bound_small_deterministic_search(self) -> None:
        self.assertEqual(maximum_transition_witnesses(1), (0, 1, 0x015E, 0x015F))
        results, evaluated = search(deltas=(1, 2), positions=(0, 1), beam_per_position=1)
        self.assertEqual(evaluated, 16)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(len(result.round_stats) == 4 for result in results))
        self.assertTrue(all(result.final_active_words > 0 for result in results))

    def test_best_discovered_candidate_regression(self) -> None:
        evaluator = TwoRoundEvaluator()
        candidate = evaluator.candidate(13, 1, 0x015E)
        self.assertIsNotNone(candidate)
        result = expand_candidate(candidate, evaluator)  # type: ignore[arg-type]
        self.assertEqual(result.total_cost, 1439)
        self.assertEqual(
            result.round_stats,
            ((1, 1, 14), (32, 0, 480), (31, 0, 465), (32, 0, 480)),
        )

    def test_count_two_transition_witnesses_are_exact(self) -> None:
        delta = 1
        sbox = get_base_inversion_sbox()
        domain = np.arange(1 << 16, dtype=np.uint32)
        output_differences = sbox[domain] ^ sbox[domain ^ delta]
        witnesses = count_two_transition_witnesses(delta)
        self.assertEqual(len(witnesses), 4)
        self.assertEqual(len(set(witnesses)), 4)
        for witness in witnesses:
            with self.subTest(witness=witness):
                output_delta = int(sbox[witness]) ^ int(sbox[witness ^ delta])
                self.assertEqual(int(np.count_nonzero(output_differences == output_delta)), 2)
                self.assertNotEqual(output_delta, int(sbox[delta]))
                self.assertLess(witness, witness ^ delta)

    def test_deterministic_backgrounds_belong_to_field(self) -> None:
        backgrounds = deterministic_backgrounds()
        self.assertEqual(len(backgrounds), 4)
        self.assertEqual(backgrounds[0], (0,) * 32)
        for background in backgrounds:
            self.assertEqual(len(background), 32)
            for offset in (0, 16):
                value = sum(
                    background[offset + index] << (16 * index)
                    for index in range(16)
                )
                self.assertLess(value, P_CURVE25519)

    def test_diversified_search_small_deterministic_sample(self) -> None:
        results, evaluated = search_diversified(
            deltas=(1,), positions=(0,),
            backgrounds=deterministic_backgrounds(2),
            beam_per_background_position=1,
        )
        self.assertEqual(evaluated, 16)
        self.assertEqual(len(results), 2)
        self.assertEqual({result.background_id for result in results}, {0, 1})
        self.assertTrue(all(len(result.round_stats) == 4 for result in results))


if __name__ == "__main__":
    unittest.main()
