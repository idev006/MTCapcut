# OpenRouter token economy and three-minute cut

Status: engineering checkpoint, 2026-11-04. V22 later produced a three-minute CapCut draft and local export; see [retest](./36-three-minute-autonomous-retest.md) and [pipeline diagnosis](./37-v22-diagnosis-design-and-delivery-plan.md). The measured baseline below describes the earlier V9–V15 runs.

## Measured baseline

- Latest studio snapshot: 61 assets, 190 observations, 137,204 UTF-8 bytes as compact JSON serialization. This is not a measured token count.
- The snapshot currently appears in six specialist calls, the director call, the initial lead editor call, and some repairs. The repeated context and long-form repair responses are the primary current cost drivers.
- OpenRouter Vision analyzed all 57 registered event photos once and stored findings in the SQLite understanding map. Repeated picture analysis uses the current-version cache.
- Runs V9–V15 failed validation or contract checks. V15 still produced only 72 seconds and omitted required messages. No draft was created from those runs.

## Format decision

TOON is a candidate wire format for repetitive, uniform asset and observation rows. Keep SQLite/JSON as the canonical SSOT and strict JSON Schema for model output. Introduce TOON only after an A/B replay on the same fixed snapshot and model shows lower actual prompt tokens and no worse evidence citation, brief compliance or timeline validity. The official Python implementation is `toon-format`, but it is not a project dependency yet.

## Cost reduction order

1. Project only the relevant evidence into each role's prompt. Brief interpreter gets authority text only; photo curator gets a concise, scored picture catalog; long-form editor works scene by scene with stable IDs and source ranges. Never send 190 detailed observations to every role.
2. Use OpenRouter's returned `usage.prompt_tokens`, `usage.completion_tokens`, cache details and generation cost to log cost per stage and per successful candidate. Current provider parses token totals but does not persist a stage ledger.
3. Keep stable prefixes and check `cached_tokens` before enabling provider-specific caching. An identical-request response cache may help retries but requires explicit opt-in and an invalidation key tied to asset/brief/model/prompt versions.
4. Compare compact JSON and TOON on the real snapshot, including Thai text, UUIDs and nested observations. Bytes or character counts alone are insufficient to claim token savings.
5. Split the 170–190 second cut into story sequences, then validated short timeline chunks. Assemble them mechanically with an exact duration and music contract. This limits output truncation and repair cost while OpenRouter remains responsible for every creative decision.

## References

- TOON official specification: https://github.com/toon-format/spec
- TOON Python implementation: https://github.com/toon-format/toon-python
- OpenRouter prompt caching: https://openrouter.ai/docs/guides/best-practices/prompt-caching
- OpenRouter response caching: https://openrouter.ai/docs/guides/features/response-caching
