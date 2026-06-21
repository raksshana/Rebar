from __future__ import annotations
import builtins
import contextlib
import io
import re
import time


def _make_restricted_builtins():
    """Builtins available to model-generated migration scripts.

    Removes file I/O and code-execution functions that a model could use to
    read grader source files, inspect the answer key, or execute arbitrary
    code — all of which are RFT reward-hacking vectors.
    """
    safe = vars(builtins).copy()
    for name in (
        "open", "eval", "exec", "compile", "breakpoint",
        "__loader__", "__spec__", "__build_class__",
    ):
        safe.pop(name, None)
    return safe


_RESTRICTED_BUILTINS = _make_restricted_builtins()

from agent.trajectory import Step, Trajectory
from agent.prompt import build_script_prompt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_code(response: str) -> str:
    """Pull the last fenced code block out of the model response.

    Uses the LAST match so that chain-of-thought models whose reasoning
    references snippets early still return the final, complete script.
    Tries ```python, ```py, and plain ``` in that order.  If no fence is
    found, falls back to the text starting at the first unambiguous Python
    statement (import/from only — not # which appears in prose).
    """
    for pattern in (
        r"```python\n(.*?)```",
        r"```py\n(.*?)```",
        r"```\n(.*?)```",
    ):
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[-1].strip()

    # No fence — skip prose and start at the first import/from statement.
    lines = response.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(("import ", "from ")):
            return "\n".join(lines[i:]).strip()

    return response.strip()


def _exec_script(code: str, context: dict) -> dict:
    """exec() the migration script and capture stdout/stderr."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    error = False
    try:
        with (
            contextlib.redirect_stdout(stdout_buf),
            contextlib.redirect_stderr(stderr_buf),
        ):
            exec(code, context)  # noqa: S102
    except Exception as e:
        stderr_buf.write(f"{type(e).__name__}: {e}\n")
        error = True
    return {
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "error": error,
    }


# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

class AnthropicClient:
    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic
        self.model = model
        self._client = anthropic.Anthropic()

    def generate_text(self, messages: list[dict], system_prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=8096,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text


class _OpenAICompatibleClient:
    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        import openai
        self.model = model
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self._openai = openai

    def generate_text(self, messages: list[dict], system_prompt: str) -> str:
        all_messages = [{"role": "system", "content": system_prompt}, *messages]
        for attempt in range(8):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=all_messages,
                )
                return response.choices[0].message.content
            except self._openai.RateLimitError:
                if attempt < 7:
                    time.sleep(min(2 ** attempt * 2, 60))
                else:
                    raise


class OpenAIClient(_OpenAICompatibleClient):
    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        import os
        super().__init__(
            model=model,
            api_key=api_key or os.environ["OPENAI_API_KEY"],
        )


class FireworksClient(_OpenAICompatibleClient):
    def __init__(
        self,
        model: str = "accounts/fireworks/models/llama-v3p1-70b-instruct",
        api_key: str | None = None,
    ):
        import os
        super().__init__(
            model=model,
            api_key=api_key or os.environ["FIREWORKS_API_KEY"],
            base_url="https://api.fireworks.ai/inference/v1",
        )


# ---------------------------------------------------------------------------
# Script agent wrapper
# ---------------------------------------------------------------------------

class ScriptAgentWrapper:
    """One LLM call → one Python script → exec → trajectory."""

    def __init__(self, env, llm_client):
        self.env = env
        self.llm = llm_client

    def run(self, task_id: str, model_id: str) -> Trajectory:
        env = self.env

        source_schema = env.read_source_schema()
        dest_schema = env.read_dest_schema()
        source_data = {
            entity: env.query_source(entity)
            for entity in source_schema["entities"]
        }

        system_prompt = build_script_prompt(source_schema, dest_schema, source_data)
        messages = [{"role": "user", "content": "Write the migration script."}]
        raw = self.llm.generate_text(messages, system_prompt)

        code = _extract_code(raw)
        result = _exec_script(code, {
            "source_data": source_data,
            "write_dest": env.write_dest,
            "source_schema": source_schema,
            "dest_schema": dest_schema,
            "__builtins__": _RESTRICTED_BUILTINS,
        })

        step = Step(
            step_index=0,
            tool_name="run_script",
            tool_args={"code": code},
            tool_result=result,
            thought=raw,
        )

        return Trajectory(
            task_id=task_id,
            model_id=model_id,
            source_schema_id=task_id,
            dest_schema_id=task_id,
            max_steps=1,
            steps=[step],
            completed=not result["error"],
        )
