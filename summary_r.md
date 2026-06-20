# Raksshana's Work Summary

---

## 2026-06-20 — Agent Module (Initial Build)

### Files Created

**`agent/__init__.py`**
Public re-export of all agent classes: `ScriptAgentWrapper`, `AnthropicClient`, `OpenAIClient`, `FireworksClient`, `Step`, `Trajectory`.

**`agent/trajectory.py`**
- `Step` dataclass: `step_index`, `tool_name`, `tool_args`, `tool_result`, `thought`, `timestamp` (UTC ISO-8601 auto-set). `to_dict()` via `asdict()`.
- `Trajectory` dataclass: `task_id`, `model_id`, `source_schema_id`, `dest_schema_id`, `max_steps`, `steps`, `completed`, `final_score`. `save(path)` / `load(path)` JSON round-trip. `final_score` is `None` until the test file populates it after grading.

**`agent/prompt.py`**
- `build_script_prompt(source_schema, dest_schema, source_data) -> str`
- Embeds all three inputs as labelled JSON code blocks in the system prompt.
- Instructions: top-level executable code only, no function/class definitions, call `write_dest(entity, records)` to emit, standard library imports allowed.
- `source_data` and `write_dest` are pre-injected — model must not redefine them.

**`agent/wrapper.py`**
- `_extract_code(response)` — regex for ` ```python\n...\n``` `, falls back to raw text.
- `_exec_script(code, context)` — `exec()` with `redirect_stdout`/`redirect_stderr`; captures exceptions into result dict as `error=True` instead of raising, so the trajectory always records cleanly.
- `AnthropicClient(model)` — wraps `anthropic.Anthropic()`, calls `messages.create()` with no tools, returns `content[0].text`.
- `_OpenAICompatibleClient` — base for OpenAI-format providers; exponential-backoff retry (up to 8 attempts, `min(2^n × 2, 60)s`) on `RateLimitError`.
- `OpenAIClient(model, api_key)` — reads `OPENAI_API_KEY` from env.
- `FireworksClient(model, api_key)` — reads `FIREWORKS_API_KEY` from env; `base_url = https://api.fireworks.ai/inference/v1`.
- `ScriptAgentWrapper(env, llm_client).run(task_id, model_id) -> Trajectory`
  1. Pull `source_schema`, `dest_schema`, `source_data` from `env`
  2. `build_script_prompt(...)` → system prompt
  3. Single `llm.generate_text()` call
  4. `_extract_code()` → strip fences
  5. `_exec_script()` with injected `source_data`, `write_dest`, `source_schema`, `dest_schema`, `builtins`
  6. Return 1-step `Trajectory`

### Env Interface Expected by Wrapper
```python
env.read_source_schema()          # → dict
env.read_dest_schema()            # → dict  (obfuscated on Tier 3)
env.query_source(entity)          # → list[dict]
env.write_dest(entity, records)   # → {"written": int, "errors": list[str]}
```

---

## 2026-06-20 — Eval Harness (HUD Integration)

HUD replaces the manual eval loop. You define the episode logic inside a `@env.template()` and HUD handles running N episodes in parallel across models, storing trajectories, and returning rewards.

### Files Created

**`harness/env.py`**
- `env = Environment(name="rebar-migration")` — HUD environment handle.
- `@env.template() async def migrate(tier: int = 0)` — the core episode definition:
  1. Generates schemas + source data (via stubs for now)
  2. Builds prompt with `build_script_prompt()`
  3. `yield prompt` → HUD calls the model, sends back the raw response
  4. Extracts code with `_extract_code()`, execs with `_exec_script()`, collects into local `dest_store`
  5. Grades with stub grader, `yield score / 100.0` → reward back to HUD
- Three stubs clearly marked for replacement once real modules exist:
  - `_stub_orchestrate(tier)` → swap for `generator.orchestration.orchestrate(tier)`
  - `_stub_generate_data(schema)` → swap for `generator.data_generation.generate_source_data(schema)`
  - `_stub_grade(source_data, dest_store, transforms)` → swap for `grader.grader.Grader(...).grade(...)`

**`harness/run.py`**
- `evaluate(tiers, n_per_cell, fireworks_api_key) -> dict` — async runner:
  - Claude + Gemini via `create_agent()` through HUD's gateway
  - Llama 70B via `OpenAIChatAgent(OpenAIChatConfig(base_url=fireworks_url))` — OpenAI-compatible
  - Runs `Taskset([migrate(tier=tier) × n_per_cell]).run(agent)` per (model, tier) cell
  - Returns `results[model][tier] = {mean, min, max, n}` — all scores × 100
- `print_report(results)` — model × tier comparison table
- `__main__` entry: `python -m harness.run`

**`harness/__init__.py`**
- Re-exports `env`, `migrate`, `evaluate`, `print_report`

---

## 2026-06-20 — Source Data Generator

**`generator/data_generation.py`**

Hybrid Faker + Gemini data generator. One batched Gemini call per entity (not per field), so API usage stays low.

**Field routing — Faker vs Gemini:**
- Faker: `number`, `bool`, `date`, `enum`, `multi_enum`, `ref`, and `text` fields whose names match a known pattern (email, name, phone, city, street, url, hostname, ip, company, code, slug, version, uuid, token, label, title, etc.)
- Gemini: `richtext` fields always; `text` fields with unrecognized names (e.g. `warehouse`, `scope`, `body`) — Gemini sees the entity name so `Product.name` vs `Category.name` gets different contextually correct values.
- Fallback: if no Gemini model provided, writes `fieldname_id` stubs so pipeline still runs.

**Nested block handling:** `nested` fields generate 1–3 block items per record. Same Faker/Gemini split applies to block fields. Context passed to Gemini is `"EntityName.BlockName"`.

**Topological sort:** entities are generated in dependency order so ref target IDs are always available before entities that reference them.

**Key functions:**
- `generate_source_data(source_schema, n=3, gemini_model=None) -> dict[entity -> list[record]]`
- `make_gemini_model(api_key=None)` — configures `google.generativeai` and returns `gemini-2.0-flash` model; reads `GEMINI_API_KEY` from env if not passed.
- `_topo_sort(entities)` — DFS topological sort on ref deps.
- `_llm_batch(context_label, llm_fields, n, model)` — one Gemini call for all LLM-needed fields across all N records; parses JSON array from response with regex fallback.
- `_generate_block_items(entity, block, block_def, id_pools, model)` — 1–3 nested items per record.

---

## 2026-06-20 — Bug Fixes & Full Pipeline Confirmed Working

### Bugs Fixed

**`Taskset([task])` → 0 runs**
`Taskset.__init__` signature is `(name, tasks, ...)`. Passing `[task]` as the first arg set `name=[task]` and left `tasks=()` empty. Fixed to `Taskset("rebar-name", [task])`. All harness and test calls updated.

**`gemini-1.5-flash` model not found (404)**
`google.generativeai` is deprecated and its v1beta API no longer has `gemini-1.5-flash`. Switched the entire project to `google-genai` (the new SDK). `make_gemini_model()` now returns a `genai.Client(api_key=...)` and `_llm_batch()` calls `client.models.generate_content(model="gemini-2.0-flash", ...)`.

**Gemini API errors crashing episodes**
Wrapped `gemini_model.generate_content()` in a `try/except Exception` that falls back to stub strings, so a Gemini failure degrades gracefully rather than crashing the episode.

### End-to-End Confirmed
Both tests in `tests/test_hud_single.py` pass:
- Minimal task (`2+2?`): `reward=1.0`
- Full `migrate(tier=2)` via LocalRuntime: `reward=1.0`

Real data generation (Faker + Gemini 2.0 Flash) is running inside HUD child process. Model writes records, stub grader checks IDs.

### Next: Build Real Grader
The stub grader only checks if source IDs appear in `dest_store`. Need to build `grader/grader.py` that checks field-level correctness against ground truth transformations.

---

### How HUD fits the pipeline
```
HUD calls model × N episodes
  → your migrate() template generates episode, builds prompt
  → model returns Python script
  → you exec + grade inside the template
  → yield reward → HUD stores trajectory
```
ScriptAgentWrapper is still used for local one-off testing. HUD is the production eval path.