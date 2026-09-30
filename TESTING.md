# BoundDirection testing

## Automated checks completed

Run on 2026-09-30:

- Kill-set gate: `NO LEAK`.
- Rubric overlap gate: `PASS`.
- GenVM linter: rc 0, two checks passed.
- Deterministic Python suite: 29/29 tests passed.
- Source SHA-256: `9aef694bb65c030ca2981a47110bd0f446db0422f62ad7d2e60e3ffa5e39ed42`.

The automated suite covers validation, permissions, immutable state, amount exclusion from the ID, whitespace normalization, all revert messages, both strict arithmetic boundaries, equality, disputes, sealing, pagination, and the 30-reading limit.

## StudioNet verification completed

Run completed on 2026-09-30 using the exact source hash listed above.

- Contract: `0x221cA363AE07381EC83B53bFc527b4dbf1d7C656`
- Author: `0x6276095FAEA15108740445ff277fdA8c304657F4`
- Other wallet: `0xAD05365aFe0C2450d4FFBcdbE555b6E5fB7Dfa35`
- Label: `the Client`
- Amount: `250`
- Bound A (`FLOOR`): `44b5b66e2cf0052efaa829d2c68a840095064f8c72f5208d4d4ea8ee399309dc`
- Bound B (`CEILING`): `7be57770e84bbfe679d743114bebca32d218e048e00925e4d0907d26beaefe70`
- Ambiguous derived ID: `e53942de25f467846b077db1cdd43e081ce39db044f2d23d28762bcc8247cbab`

| # | Operation | Verified result | Transaction |
|---:|---|---|---|
| 1 | Deploy | `FINALIZED / SUCCESS` | `0x69466b777ff3873d5a55d25baf49b6b02c8d7a8506f65ce6d2ba07368d491cba` |
| 2 | Open Bound A with `least` text | `IS_MINIMUM`, `FLOOR`, `OPEN` | `0xc3cbf0ed591674fffa676a9862149e6ac8c3d94e8084f3306fe8023bc5b648d8` |
| 3 | Bound A reading `250` | `WITHIN` | `0x918b73f355c2ab80917e8d7d86b88b511ab292ecdffd14ac31519c7b007e5673` |
| 4 | Bound A reading `249` | `BREACH` | `0x784b34032cbe8b88c2c1a4d97d48b1450b2616d11d55f2ece40f8c373042dba3` |
| 5 | Other wallet disputes A reading 2 | Note stored | `0x46c4ec121ff38efdba0e99ae02b798b2bb3140f74017d895c4a74cc665358524` |
| 6 | Open Bound B with `most` text | `IS_MAXIMUM`, `CEILING`, `OPEN` | `0x825ea31f038ba2027cb43fcb192e65515fbf182649b1b0a38ad83b73206d6055` |
| 7 | Bound B reading `249` | `WITHIN` | `0xcbf3cb4d70f5df24a898b0e8ed827ac8a9dffa50f675a95f4c465d9cfd1f1258` |
| 8 | Bound B reading `251` | `BREACH` | `0x37ecca076648c20eb06a255902f5afbe2fec4bb5852428e592b2c8768765b7d7` |
| 9 | Open ambiguous N1 text | `ERROR / Rollback`: direction could not be read | `0x8079366b99e35aa5d9a22a4e99c77df50921593237615e478e3e023945ff81d9` |
| 10 | Seal Bound A | `SUCCESS`, state `SEALED` | `0xd9f2dda76b27521b46ead54adb84e73918a279c4b8e2ff38b1e274328f36c76b` |
| 11 | Bound A reading `240` after seal | `ERROR / Rollback`: `This bound is sealed` | `0xfa2221314f9f23724d62e5eed50f9ea047664e07c92baa9261cdf1c00950dad6` |
| 12 | Other wallet disputes A reading 1 after seal | `FINALIZED / SUCCESS`, note stored | `0x6b53b389c6aabfe5c2666d41cd9194b6ec7e1c0bc6ec4d1cb2d90200d364d930` |

## Final accepted state

Bound A is `SEALED`, with two readings and one breach:

- Reading 1: `250`, `WITHIN`, disputed with `The equality reading is contested`.
- Reading 2: `249`, `BREACH`, disputed with `The source data is contested`.

Bound B remains `OPEN`, with two readings and one breach:

- Reading 1: `249`, `WITHIN`.
- Reading 2: `251`, `BREACH`.

The ambiguous derived ID returns `{}`, proving the reverted N1 call created no record. The deployed source SHA-256 equals the local source SHA-256: `9aef694bb65c030ca2981a47110bd0f446db0422f62ad7d2e60e3ffa5e39ed42`.

## Evidence boundary

Local tests alone do not prove model semantics or StudioNet consensus. The live results above are separately supported by finalized Explorer transactions and accepted-state RPC reads from this exact deployment.
