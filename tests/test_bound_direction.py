"""Deterministic tests for the exact BoundDirection contract source.

The local SDK stand-in exercises validation order, state transitions, prompt
boundaries, arithmetic verdicts, and immutable records. It does not simulate
StudioNet consensus or prove the model's semantic classifications.
"""

from pathlib import Path
import copy
import hashlib
import os
import re
import sys
import types
import unittest


SOURCE = Path(
    os.environ.get(
        "BOUND_DIRECTION_SOURCE",
        Path(__file__).parents[1] / "contracts" / "BoundDirection.py",
    )
)

AUTHOR = "0x3065E31B1D993d7C0D59E6786844cBa56780B2d3"
OTHER = "0x5a52d040581A76e2C032542855D31480f2ea7097"
OUTSIDER = "0x1111111111111111111111111111111111111111"
ZERO = "0x" + ("0" * 40)

LABEL = "the Client"
FLOOR_TEXT = "The agreed figure is the least we will provide."
CEILING_TEXT = "The agreed figure is the most we will provide."
UNSETTLED_TEXT = "The agreed figure applies to this work."


class UserError(Exception):
    pass


class Return:
    def __init__(self, calldata):
        self.calldata = calldata


class U256(int):
    def __new__(cls, value):
        value = int(value)
        if not 0 <= value < 2**256:
            raise ValueError("test u256 bounds")
        return super().__new__(cls, value)


class TreeMap(dict):
    def __getitem__(self, key):
        return copy.deepcopy(super().__getitem__(key))

    def get(self, key, default=None):
        return copy.deepcopy(super().get(key, default))


class Hash:
    def __init__(self, data):
        # Isolation stand-in only. StudioNet uses the SDK Keccak256 class.
        self._hash = hashlib.sha256(data)

    def hexdigest(self):
        return self._hash.hexdigest()


class Runtime:
    def __init__(self):
        self.default = {"outcome": "IS_MINIMUM"}
        self.outputs = []
        self.prompts = []
        self.consensus_calls = 0
        self.validator_results = []

    def exec_prompt(self, prompt, response_format):
        if response_format != "json":
            raise AssertionError("unexpected response format")
        self.prompts.append(prompt)
        value = self.outputs.pop(0) if self.outputs else self.default
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)

    def run(self, leader, validator):
        self.consensus_calls += 1
        leader_result = Return(leader())
        agreed = validator(leader_result)
        self.validator_results.append(agreed)
        if not agreed:
            raise UserError("Fake consensus did not converge")
        return leader_result


def load_contract():
    runtime = Runtime()
    gl = types.SimpleNamespace(
        Contract=object,
        public=types.SimpleNamespace(
            write=lambda fn: fn,
            view=lambda fn: fn,
        ),
        message=types.SimpleNamespace(sender_address=AUTHOR),
        vm=types.SimpleNamespace(
            UserError=UserError,
            Return=Return,
            run_nondet_unsafe=runtime.run,
        ),
        nondet=types.SimpleNamespace(exec_prompt=runtime.exec_prompt),
    )

    sdk = types.ModuleType("genlayer")
    exports = {
        "gl": gl,
        "u256": U256,
        "TreeMap": TreeMap,
        "Address": str,
        "allow_storage": lambda cls: cls,
        "Keccak256": Hash,
    }
    for name, value in exports.items():
        setattr(sdk, name, value)
    sys.modules["genlayer"] = sdk

    module = types.ModuleType("bound_direction_under_test")
    sys.modules[module.__name__] = module
    source = SOURCE.read_text(encoding="utf-8")
    exec(compile(source, str(SOURCE), "exec"), module.__dict__)

    contract = module.BoundDirection()
    for name in (
        "bounds",
        "reading_value",
        "reading_verdict",
        "dispute_note",
    ):
        setattr(contract, name, TreeMap())
    return module, contract, gl, runtime


class BoundDirectionTests(unittest.TestCase):
    def setUp(self):
        self.module, self.contract, self.gl, self.runtime = load_contract()

    def sender(self, address):
        self.gl.message.sender_address = address

    def bound_id(self, text=FLOOR_TEXT, author=AUTHOR):
        return self.contract._bound_id_for(
            author,
            self.contract._normalize_text(text.strip()),
        )

    def open_floor(self, amount=250, text=FLOOR_TEXT):
        self.runtime.default = {"outcome": "IS_MINIMUM"}
        self.contract.open_bound(OTHER, LABEL, amount, text)
        return self.bound_id(text)

    def open_ceiling(self, amount=250, text=CEILING_TEXT):
        self.runtime.default = {"outcome": "IS_MAXIMUM"}
        self.contract.open_bound(OTHER, LABEL, amount, text)
        return self.bound_id(text)

    def snapshot(self):
        return copy.deepcopy(vars(self.contract))

    def refuse(self, call, message, model_delta=0):
        before = self.snapshot()
        calls = self.runtime.consensus_calls
        with self.assertRaisesRegex(Exception, re.escape(message)):
            call()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(calls + model_delta, self.runtime.consensus_calls)

    def test_open_floor_stores_normalized_wallet_and_immutable_initial_state(self):
        self.runtime.default = {"outcome": "IS_MINIMUM"}
        self.contract.open_bound("  " + OTHER.upper() + "  ", "  " + LABEL + "  ", 250, "  " + FLOOR_TEXT + "  ")
        record = self.contract.get_bound(self.bound_id())
        self.assertEqual(record["author"], AUTHOR)
        self.assertEqual(record["other_wallet"], OTHER.lower())
        self.assertEqual(record["other_label"], LABEL)
        self.assertEqual(record["text"], FLOOR_TEXT)
        self.assertEqual(record["amount"], 250)
        self.assertEqual(record["direction"], "FLOOR")
        self.assertEqual(record["state"], "OPEN")
        self.assertEqual(record["reading_count"], 0)
        self.assertEqual(record["breach_count"], 0)

    def test_open_ceiling_sets_ceiling_and_full_operator_text(self):
        pid = self.open_ceiling()
        record = self.contract.get_bound(pid)
        self.assertEqual(record["direction"], "CEILING")
        self.assertEqual(record["operator"], "a reading over 250 is the breach")

    def test_floor_operator_text_is_human_readable(self):
        pid = self.open_floor(37)
        self.assertEqual(
            self.contract.get_bound(pid)["operator"],
            "a reading under 37 is the breach",
        )

    def test_invalid_wallet_variants_are_refused(self):
        for wallet in ("", "0x123", ZERO, "0x" + ("g" * 40)):
            with self.subTest(wallet=wallet):
                self.refuse(
                    lambda wallet=wallet: self.contract.open_bound(wallet, LABEL, 250, FLOOR_TEXT),
                    "Invalid wallet address",
                )

    def test_empty_and_oversized_text_are_refused(self):
        self.refuse(lambda: self.contract.open_bound(OTHER, LABEL, 250, "  "), "Text is empty")
        self.refuse(lambda: self.contract.open_bound(OTHER, LABEL, 250, "x" * 601), "Text is too long")

    def test_empty_and_oversized_label_are_refused(self):
        self.refuse(lambda: self.contract.open_bound(OTHER, " ", 250, FLOOR_TEXT), "Label is empty")
        self.refuse(lambda: self.contract.open_bound(OTHER, "x" * 81, 250, FLOOR_TEXT), "Label is too long")

    def test_reserved_tokens_are_rejected_in_text_and_label_case_insensitively(self):
        for label, text in (
            (LABEL, "prefix " + self.module.NOT_SETTLED.lower()),
            (self.module.TEXT_OPEN.lower(), FLOOR_TEXT),
        ):
            with self.subTest(label=label, text=text):
                self.refuse(
                    lambda label=label, text=text: self.contract.open_bound(OTHER, label, 250, text),
                    "Text or label contains a reserved token",
                )

    def test_fixed_point_prompt_filter_removes_nested_marker(self):
        nested = "<<UNTRUSTED_BOUND_TEXT>UNTRUSTED_BOUND_TEXT>"
        cleaned = self.contract._safe_prompt_text(nested)
        self.assertNotIn(self.module.TEXT_OPEN, cleaned.upper())

    def test_amount_range_and_same_wallet_are_refused_before_model(self):
        for amount in (0, self.module.BoundDirection.MAX_AMOUNT + 1):
            self.refuse(
                lambda amount=amount: self.contract.open_bound(OTHER, LABEL, amount, FLOOR_TEXT),
                "The amount is out of range",
            )
        self.refuse(
            lambda: self.contract.open_bound(AUTHOR.lower(), LABEL, 250, FLOOR_TEXT),
            "The other side cannot be the author",
        )

    def test_internal_whitespace_normalizes_to_same_id(self):
        first = "The agreed figure is the least we will provide."
        second = "The\tagreed\nfigure is  the least we will provide."
        self.assertEqual(
            self.bound_id(first),
            self.bound_id(second),
        )

    def test_amount_is_excluded_from_id_and_blocks_reroll(self):
        self.open_floor(250)
        self.refuse(
            lambda: self.contract.open_bound(OTHER, LABEL, 251, FLOOR_TEXT),
            "This bound already exists",
        )

    def test_prompt_exposes_only_label_text_and_one_deterministic_amount(self):
        self.open_floor()
        prompt = self.runtime.prompts[0]
        self.assertIn(LABEL, prompt)
        self.assertIn(FLOOR_TEXT, prompt)
        self.assertIn("250", prompt)
        self.assertNotIn(AUTHOR.lower(), prompt.lower())
        self.assertNotIn(OTHER.lower(), prompt.lower())

    def test_not_settled_reverts_and_creates_no_record(self):
        self.runtime.default = {"outcome": "NOT_SETTLED"}
        self.refuse(
            lambda: self.contract.open_bound(OTHER, LABEL, 250, UNSETTLED_TEXT),
            "The direction of the bound could not be read from the text",
            model_delta=1,
        )
        self.assertEqual(self.contract.get_bound(self.bound_id(UNSETTLED_TEXT)), {})

    def test_malformed_model_output_fails_closed_without_storage(self):
        self.runtime.default = {"unexpected": "value"}
        self.refuse(
            lambda: self.contract.open_bound(OTHER, LABEL, 250, UNSETTLED_TEXT),
            "The direction of the bound could not be read from the text",
            model_delta=1,
        )

    def test_floor_boundaries_are_breach_within_within(self):
        pid = self.open_floor()
        for value in (249, 250, 251):
            self.contract.record_reading(pid, value)
        rows = self.contract.get_readings(pid, 0, 10)
        self.assertEqual([r["verdict"] for r in rows], ["BREACH", "WITHIN", "WITHIN"])
        self.assertEqual(self.contract.get_bound(pid)["breach_count"], 1)

    def test_ceiling_boundaries_are_within_within_breach(self):
        pid = self.open_ceiling()
        for value in (249, 250, 251):
            self.contract.record_reading(pid, value)
        rows = self.contract.get_readings(pid, 0, 10)
        self.assertEqual([r["verdict"] for r in rows], ["WITHIN", "WITHIN", "BREACH"])
        self.assertEqual(self.contract.get_bound(pid)["breach_count"], 1)

    def test_same_reading_has_opposite_verdict_under_frozen_operators(self):
        floor_id = self.open_floor()
        ceiling_id = self.open_ceiling()
        self.contract.record_reading(floor_id, 249)
        self.contract.record_reading(ceiling_id, 249)
        self.assertEqual(self.contract.get_reading(floor_id, 1)["verdict"], "BREACH")
        self.assertEqual(self.contract.get_reading(ceiling_id, 1)["verdict"], "WITHIN")

    def test_only_author_records_and_reading_range_is_bounded(self):
        pid = self.open_floor()
        self.sender(OUTSIDER)
        self.refuse(
            lambda: self.contract.record_reading(pid, 250),
            "Only the author may record a reading",
        )
        self.sender(AUTHOR)
        self.refuse(
            lambda: self.contract.record_reading(pid, self.module.BoundDirection.MAX_AMOUNT + 1),
            "The reading is out of range",
        )

    def test_reading_cap_is_bound_scoped(self):
        pid = self.open_floor()
        record = self.contract.bounds[pid]
        record.reading_count = self.module.u256(30)
        self.contract.bounds[pid] = record
        self.refuse(
            lambda: self.contract.record_reading(pid, 250),
            "No room for further readings",
        )

    def test_unknown_id_errors_for_every_write_method(self):
        unknown = "f" * 64
        for call in (
            lambda: self.contract.record_reading(unknown, 1),
            lambda: self.contract.dispute_reading(unknown, 1, "note"),
            lambda: self.contract.seal_bound(unknown),
        ):
            with self.subTest(call=call):
                self.refuse(call, "Unknown bound id")

    def test_only_named_other_side_may_dispute(self):
        pid = self.open_floor()
        self.contract.record_reading(pid, 249)
        self.sender(OUTSIDER)
        self.refuse(
            lambda: self.contract.dispute_reading(pid, 1, "The reading is contested"),
            "Only the named other side may dispute a reading",
        )

    def test_dispute_index_duplicate_and_note_limit_guards(self):
        pid = self.open_floor()
        self.contract.record_reading(pid, 249)
        self.sender(OTHER)
        for index in (0, 2):
            self.refuse(
                lambda index=index: self.contract.dispute_reading(pid, index, "note"),
                "No such reading",
            )
        self.refuse(
            lambda: self.contract.dispute_reading(pid, 1, "x" * 61),
            "Note is too long",
        )
        self.contract.dispute_reading(pid, 1, "The source data is contested")
        self.refuse(
            lambda: self.contract.dispute_reading(pid, 1, "Second note"),
            "This reading has already been disputed",
        )

    def test_empty_dispute_is_still_a_one_time_immutable_entry(self):
        pid = self.open_floor()
        self.contract.record_reading(pid, 249)
        self.sender(OTHER)
        self.contract.dispute_reading(pid, 1, "")
        self.assertEqual(self.contract.get_dispute(pid, 1)["note"], "")
        self.refuse(
            lambda: self.contract.dispute_reading(pid, 1, "later"),
            "This reading has already been disputed",
        )

    def test_seal_requires_author_and_at_least_one_reading(self):
        pid = self.open_floor()
        self.refuse(lambda: self.contract.seal_bound(pid), "Nothing has been recorded yet")
        self.contract.record_reading(pid, 250)
        self.sender(OUTSIDER)
        self.refuse(lambda: self.contract.seal_bound(pid), "Only the author may seal this bound")

    def test_seal_is_permanent_and_blocks_new_readings(self):
        pid = self.open_floor()
        self.contract.record_reading(pid, 250)
        self.contract.seal_bound(pid)
        self.refuse(lambda: self.contract.record_reading(pid, 249), "This bound is sealed")
        self.refuse(lambda: self.contract.seal_bound(pid), "This bound is already sealed")
        self.assertEqual(self.contract.get_bound(pid)["state"], "SEALED")

    def test_dispute_remains_open_after_seal(self):
        pid = self.open_floor()
        self.contract.record_reading(pid, 249)
        self.contract.seal_bound(pid)
        self.sender(OTHER)
        self.contract.dispute_reading(pid, 1, "The source data is contested")
        self.assertEqual(
            self.contract.get_dispute(pid, 1)["note"],
            "The source data is contested",
        )

    def test_unknown_views_are_non_throwing_and_empty(self):
        unknown = "0" * 64
        self.assertEqual(self.contract.get_bound(unknown), {})
        self.assertEqual(self.contract.get_reading(unknown, 1), {})
        self.assertEqual(self.contract.get_readings(unknown, 0, 10), [])
        self.assertEqual(self.contract.get_dispute(unknown, 1), {})

    def test_pagination_and_view_validation(self):
        pid = self.open_floor()
        for value in (248, 249, 250):
            self.contract.record_reading(pid, value)
        self.assertEqual(
            [r["value"] for r in self.contract.get_readings(pid, 1, 2)],
            [249, 250],
        )
        self.refuse(lambda: self.contract.get_readings(pid, -1, 1), "Invalid offset")
        self.refuse(lambda: self.contract.get_readings(pid, 0, 0), "Invalid page size")
        self.refuse(lambda: self.contract.get_readings(pid, 0, 51), "Invalid page size")

    def test_exact_revert_catalog_is_covered_by_named_tests(self):
        source = SOURCE.read_text(encoding="utf-8")
        actual = set(re.findall(r'raise gl\.vm\.UserError\(\s*"([^"]+)"', source))
        expected = {
            "Invalid wallet address",
            "Text is empty",
            "Text is too long",
            "Label is empty",
            "Label is too long",
            "Note is too long",
            "Text or label contains a reserved token",
            "Unknown bound id",
            "The amount is out of range",
            "The other side cannot be the author",
            "This bound already exists",
            "The direction of the bound could not be read from the text",
            "Only the author may record a reading",
            "This bound is sealed",
            "No room for further readings",
            "The reading is out of range",
            "Only the named other side may dispute a reading",
            "No such reading",
            "This reading has already been disputed",
            "Only the author may seal this bound",
            "This bound is already sealed",
            "Nothing has been recorded yet",
            "Invalid offset",
            "Invalid page size",
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
