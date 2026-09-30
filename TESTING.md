# BoundDirection testing

## Automated checks completed

Run on 2026-09-30:

- Kill-set gate: `NO LEAK`.
- Rubric overlap gate: `PASS`.
- GenVM linter: rc 0, two checks passed.
- Deterministic Python suite: 29/29 tests passed.
- Source SHA-256: `9aef694bb65c030ca2981a47110bd0f446db0422f62ad7d2e60e3ffa5e39ed42`.

The automated suite covers validation, permissions, immutable state, amount exclusion from the ID, whitespace normalization, all revert messages, both strict arithmetic boundaries, equality, disputes, sealing, pagination, and the 30-reading limit.

## Required StudioNet verification

Use two wallets, `author` and `other`. Use label `the Client` and amount `250`.

1. Deploy the exact `contracts/BoundDirection.py` source.
2. As `author`, open F4: `The agreed figure is the least we will provide.` Confirm `FLOOR`.
3. On F4, record `250`; confirm `WITHIN`.
4. On F4, record `249`; confirm `BREACH`.
5. As `other`, dispute reading index `2`; confirm the note is stored.
6. As `author`, open C5: `The agreed figure is the most we will provide.` Confirm `CEILING`.
7. On C5, record `249`; confirm `WITHIN`.
8. On C5, record `251`; confirm `BREACH`.
9. Open N1: `The agreed figure applies to this work.` Confirm revert: `The direction of the bound could not be read from the text`, and confirm no record exists.
10. Seal the F4 bound, then try another reading. Confirm `This bound is sealed`.
11. As `other`, dispute reading index `1` after sealing. Confirm disputes remain open.

For each row, record the transaction hash, execution result, and post-state from the relevant view. `FINALIZED` alone is not sufficient evidence of the expected result.

## Evidence boundary

Local tests do not prove model semantics or StudioNet consensus. Until the live steps above are completed, those results remain `NOT RUN` and the final contract address must not be submitted as verified.
