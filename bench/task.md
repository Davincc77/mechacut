# A/B benchmark — what a weak agent gains from mechacut

**Fixed task** (same prompt bytes in both arms, temperature 0, seed 42):
clean a dirty CSV → repair broken JSON → deduplicate URLs → emit one final
YAML document. Data and steps in `bench/task_data.py`.

- **Arm A (without mechacut)**: the model does everything in its own
  context and answers directly. One generation.
- **Arm B (with mechacut)**: the model gets `GET /agent/manifest` in its
  system prompt and five function tools (clean-table recipe, json/repair,
  list/dedupe, format/convert, validate). Loop capped at 12 steps.

**Success** = parsed final YAML, canonical-JSON sha256 equals the pinned
gold answer:

```
313389d967fb8d98fd78408da7139db9e1668fb39e55f0bfa79f96203736e7de
```

Re-pin after any pipeline change: `python bench/expected.py write`
(check with `python bench/expected.py check`).

**Run**: `python bench/run.py [0.5b|1.5b|7b] [A|B]` — appends one row per
cell to `bench/results.jsonl` (tokens in/out, tool calls, success, seconds).

**Agents** (local, Ollama, base hardware = Mac mini M4 Pro 24 Go — the
customer profile: no cloud, tight budget):
- `qwen2.5:0.5b-instruct` — the weakest honest agent
- `qwen2.5:1.5b-instruct`
- `qwen2.5:7b-instruct-q4_K_M` — the exact profile the operator runs daily

## Results

| agent | arm | tokens in | tokens out | calls | success | seconds |
|---|---|---|---|---|---|---|
| _(measured runs land in results.jsonl; fill from there)_ | | | | | | |
