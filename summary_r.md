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