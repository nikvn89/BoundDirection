BoundDirection does not ask whether a number is good enough, and it does not grade anything on a scale. The number is already on the record. It asks which side of that number the author is not allowed to be on, and it turns that answer into the comparison operator every later reading is judged by.

# BoundDirection

`BoundDirection` is a GenLayer Intelligent Contract that determines whether a recorded amount is a floor or a ceiling. The semantic decision is made once when a bound is opened. Every later reading is judged deterministically with the stored operator.

The contract does not hold or transfer funds.

## Core behavior

- `IS_MINIMUM` stores `FLOOR`: a reading below the amount is `BREACH`.
- `IS_MAXIMUM` stores `CEILING`: a reading above the amount is `BREACH`.
- `NOT_SETTLED` or malformed model output reverts and creates no record.
- A reading exactly equal to the amount is `WITHIN` in both directions.
- Only the author records readings and seals a bound.
- The named other wallet may attach one immutable dispute note per reading.
- Sealing blocks new readings but does not block disputes.

The strongest comparison uses the same amount, `250`, and the same later reading, `249`:

- `The agreed figure is the least we will provide.` → `FLOOR` → `BREACH`
- `The agreed figure is the most we will provide.` → `CEILING` → `WITHIN`

After the single model call in `open_bound`, no AI participates in later verdicts.

## Contract methods

Write methods:

- `open_bound(other_wallet, other_label, amount, text)`
- `record_reading(bound_id_hex, value)`
- `dispute_reading(bound_id_hex, index, note)`
- `seal_bound(bound_id_hex)`

Views:

- `get_bound(bound_id_hex)`
- `get_reading(bound_id_hex, index)`
- `get_readings(bound_id_hex, offset, limit)`
- `get_dispute(bound_id_hex, index)`
- `get_rubric()`
- `get_limits()`

## Local verification

```bash
python3 BOUNDDIRECTION_KILLSET_CHECK.py contracts/BoundDirection.py
python3 -m unittest discover -s tests -v
```

The source SHA-256 is recorded in `SOURCE_SHA256.txt`. Completed StudioNet semantic and runtime results are recorded in `TESTING.md`.

## Verified StudioNet deployment

- Contract: `0x221cA363AE07381EC83B53bFc527b4dbf1d7C656`
- Chain ID: `61999`
- Deployment transaction: `0x69466b777ff3873d5a55d25baf49b6b02c8d7a8506f65ce6d2ba07368d491cba`
- Source SHA-256: `9aef694bb65c030ca2981a47110bd0f446db0422f62ad7d2e60e3ffa5e39ed42`
- Deployed source parity: exact after newline normalization
- Runtime: 12/12 finalized transactions matched the expected execution and post-state

The live run proved opposite deterministic behavior around the same amount, fail-closed handling for ambiguous text, permanent sealing, and the ability of the named other wallet to dispute an existing reading after sealing. Full hashes and final state are recorded in `TESTING.md`.
