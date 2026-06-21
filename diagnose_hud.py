"""
Direct diagnostic: 3 tier-3 episodes against HUD gateway model.
No HUD runtime involved — raw exec results and grades printed for each run.
"""
import asyncio, os, textwrap
from openai import AsyncOpenAI
from hud.settings import settings
from migration_episode import build_episode
from agent.wrapper import _extract_code, _exec_script, _RESTRICTED_BUILTINS
from generator.difficulty_dial import translate_dest_data

MODEL      = "kimi-k-2p5-baseline"
MAX_TOKENS = 10000
TIER       = 3
N_RECORDS  = 3
SEEDS      = [42000, 42001, 42002]

client = AsyncOpenAI(
    api_key=settings.api_key,
    base_url=settings.hud_gateway_url,
)


async def run_episode(seed: int) -> float:
    print(f"\n{'='*60}")
    print(f"Episode  seed={seed}  tier={TIER}")
    print('='*60)

    episode = build_episode(seed=seed, tier=TIER, n_records=N_RECORDS)
    print(f"Source entities : {list(episode.source_data.keys())}")

    resp = await client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        messages=[{"role": "user", "content": episode.prompt}],
    )

    raw = resp.choices[0].message.content or ""
    finish = resp.choices[0].finish_reason
    tokens_used = resp.usage.completion_tokens if resp.usage else "?"

    print(f"Completion tokens: {tokens_used}  finish_reason: {finish}")
    if finish == "length":
        print("*** WARNING: response hit token limit — script likely truncated ***")

    code = _extract_code(raw)
    print(f"Extracted code   : {len(code)} chars")

    dest_store: dict = {}
    def write_dest(entity, records):
        dest_store.setdefault(entity, []).extend(records)
        return {"written": len(records), "errors": []}

    exec_result = _exec_script(code, {
        "source_data":   episode.source_data,
        "write_dest":    write_dest,
        "source_schema": episode.task.source_schema,
        "dest_schema":   episode.shown_dest_schema,
        "__builtins__":  _RESTRICTED_BUILTINS,
    })

    print(f"exec_error       : {exec_result['error']}")
    if exec_result["error"]:
        print("STDERR:")
        print(textwrap.indent(exec_result["stderr"].strip(), "  "))

    print(f"dest_store       : ", end="")
    if dest_store:
        for ent, rows in dest_store.items():
            print(f"{ent}({len(rows)})", end="  ")
        print()
    else:
        print("EMPTY")

    real_dest = translate_dest_data(dest_store, episode.entity_map, episode.field_maps)
    grade = episode.task.grader.grade(episode.source_data, real_dest)

    print(f"Grade breakdown  :")
    for k, v in grade.items():
        print(f"  {k}: {v}")

    return grade["total"]


async def main():
    scores = []
    for seed in SEEDS:
        score = await run_episode(seed)
        scores.append(score)

    print(f"\n{'='*60}")
    print(f"Results across {len(SEEDS)} runs  (model={MODEL}):")
    for seed, score in zip(SEEDS, scores):
        print(f"  seed={seed}  total={score:.1f}")
    print(f"  mean = {sum(scores)/len(scores):.1f}")
    print('='*60)

asyncio.run(main())
