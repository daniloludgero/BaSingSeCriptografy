"""Composição DIMACS de uma rodada RSD-S sob chave e sessão fixas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gf16_inverse_cnf import build_inverse_cnf
from mds_xor_synthesis import build_mds_xor_circuit
import numpy as np

from mds_real import gf_inv
from rsd_s_v4_final import (
    B, M_CAUCHY_32, W, _expand_key_words, derive_keys, fragment_full,
    gf_matrix_vector_mult, round_constant,
)


@dataclass
class CnfBuilder:
    variable_count: int = 0
    clauses: list[tuple[int, ...]] | None = None

    def __post_init__(self) -> None:
        if self.clauses is None:
            self.clauses = []

    def new_var(self) -> int:
        self.variable_count += 1
        return self.variable_count

    def new_vars(self, count: int) -> list[int]:
        return [self.new_var() for _ in range(count)]

    def equivalence(self, output: int, source: int, inverted: bool = False) -> None:
        assert self.clauses is not None
        if inverted:
            self.clauses.extend(((-output, -source), (output, source)))
        else:
            self.clauses.extend(((-output, source), (output, -source)))

    def xor_gate(self, left: int, right: int, output: int) -> None:
        assert self.clauses is not None
        self.clauses.extend(
            ((-left, -right, -output), (left, right, -output),
             (left, -right, output), (-left, right, output))
        )


@dataclass(frozen=True)
class FixedRoundCnf:
    builder: CnfBuilder
    input_vars: tuple[int, ...]
    output_vars: tuple[int, ...]
    key_hex: str
    session: int


@dataclass(frozen=True)
class RoundTrace:
    after_whitening: tuple[int, ...]
    after_inverse: tuple[int, ...]
    after_constant: tuple[int, ...]
    after_mds: tuple[int, ...]
    outputs: tuple[int, ...]


def _xor_constant(builder: CnfBuilder, inputs: list[int], constant_words) -> list[int]:
    outputs = builder.new_vars(len(inputs))
    for index, (source, output) in enumerate(zip(inputs, outputs)):
        word = index // B
        bit = index % B
        inverted = bool(int(constant_words[word]) & (1 << bit))
        builder.equivalence(output, source, inverted)
    return outputs


def _instantiate_inverse(builder: CnfBuilder, x_vars: list[int]) -> list[int]:
    component = build_inverse_cnf()
    mapping: dict[int, int] = {
        component.x_vars[index]: x_vars[index] for index in range(B)
    }
    y_vars = builder.new_vars(B)
    mapping.update({component.y_vars[index]: y_vars[index] for index in range(B)})
    for variable in range(1, component.variable_count + 1):
        if variable not in mapping:
            mapping[variable] = builder.new_var()
    assert builder.clauses is not None
    for clause in component.clauses:
        builder.clauses.append(
            tuple(mapping[abs(literal)] if literal > 0 else -mapping[abs(literal)]
                  for literal in clause)
        )
    return y_vars


def _instantiate_mds(builder: CnfBuilder, inputs: list[int]) -> list[int]:
    component = build_mds_xor_circuit()
    mapping: dict[int, int] = {
        index: inputs[index] for index in range(component.input_count)
    }
    for left, right, output in component.gates:
        mapped_output = builder.new_var()
        mapping[output] = mapped_output
        builder.xor_gate(mapping[left], mapping[right], mapped_output)
    return [mapping[signal] for signal in component.outputs]


def instantiate_fixed_first_round(
    builder: CnfBuilder,
    raw_inputs: list[int],
    key: bytes = bytes.fromhex("a5" * 32),
    session: int = 7,
) -> RoundTrace:
    if len(raw_inputs) != W * B:
        raise ValueError(f"raw_inputs deve conter {W * B} variáveis")
    keys = derive_keys(key, session, rounds=1)
    key_words = [_expand_key_words(item, W) for item in keys]

    state = _xor_constant(builder, raw_inputs, key_words[0])
    after_inverse: list[int] = []
    for word in range(W):
        after_inverse.extend(_instantiate_inverse(builder, state[word * B:(word + 1) * B]))

    rc_words = [round_constant(key, session, 1)] * W
    after_constant = _xor_constant(builder, after_inverse, rc_words)
    after_mds = _instantiate_mds(builder, after_constant)
    outputs = _xor_constant(builder, after_mds, key_words[1])
    return RoundTrace(
        tuple(state), tuple(after_inverse), tuple(after_constant),
        tuple(after_mds), tuple(outputs)
    )


def build_fixed_first_round_cnf(
    key: bytes = bytes.fromhex("a5" * 32), session: int = 7
) -> FixedRoundCnf:
    builder = CnfBuilder()
    raw_inputs = builder.new_vars(W * B)
    trace = instantiate_fixed_first_round(builder, raw_inputs, key, session)
    return FixedRoundCnf(builder, tuple(raw_inputs), trace.outputs, key.hex(), session)


def export_dimacs(model: FixedRoundCnf, path: Path) -> None:
    clauses = model.builder.clauses or []
    lines = [
        "c RSD-S fixed-key first round (input is raw fragmented state)",
        f"c key_hex {model.key_hex}",
        f"c session {model.session}",
        "c inputs_lsb_word_order " + " ".join(map(str, model.input_vars)),
        "c outputs_lsb_word_order " + " ".join(map(str, model.output_vars)),
        f"p cnf {model.builder.variable_count} {len(clauses)}",
    ]
    lines.extend(" ".join(map(str, clause)) + " 0" for clause in clauses)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def evaluate_fixed_first_round(
    x: int, y: int, key: bytes = bytes.fromhex("a5" * 32), session: int = 7
) -> np.ndarray:
    keys = derive_keys(key, session, rounds=1)
    key_words = [_expand_key_words(item, W) for item in keys]
    state = fragment_full(x, y) ^ key_words[0]
    rc = round_constant(key, session, 1)
    state = np.array([gf_inv(int(word)) ^ rc for word in state], dtype=np.uint32)
    state = gf_matrix_vector_mult(M_CAUCHY_32, state, W).astype(np.uint64)
    return state ^ key_words[1]


def constrain_known_answer(
    model: FixedRoundCnf, input_words: np.ndarray, output_words: np.ndarray
) -> FixedRoundCnf:
    clauses = list(model.builder.clauses or [])
    for variables, words in (
        (model.input_vars, input_words), (model.output_vars, output_words)
    ):
        for index, variable in enumerate(variables):
            bit = (int(words[index // B]) >> (index % B)) & 1
            clauses.append((variable if bit else -variable,))
    builder = CnfBuilder(model.builder.variable_count, clauses)
    return FixedRoundCnf(builder, model.input_vars, model.output_vars, model.key_hex, model.session)


if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "ferramentas" / "rsd_round1_fixed.cnf"
    model = build_fixed_first_round_cnf()
    export_dimacs(model, destination)
    print(f"arquivo: {destination}")
    print(f"variaveis: {model.builder.variable_count}")
    print(f"clausulas: {len(model.builder.clauses or [])}")
