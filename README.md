WhichWay does not ask whether a number is good enough, and it does not grade anything on a scale. The number is already on the record. It asks which side of that number the author is not allowed to be on, and it turns that answer into the comparison operator every later reading is judged by.

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

The source SHA-256 is recorded in `SOURCE_SHA256.txt`. StudioNet semantic and runtime results must be added only after real transactions have completed successfully.
