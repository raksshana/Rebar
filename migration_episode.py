"""
Deterministic episode factory for GRPO rollouts.

build_episode(seed, tier, n_records) seeds the global random module and Faker,
then runs the standard orchestrate → generate_source_data pipeline. Given the
same (seed, tier, n_records), every call returns byte-identical output.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from faker import Faker

from generator.orchestration import orchestrate, GeneratedTask
from generator.data_generation import generate_source_data
from generator.difficulty_dial import obfuscate_dest_schema
from agent.prompt import build_script_prompt


@dataclass
class MigrationEpisode:
    task: GeneratedTask
    source_data: dict
    shown_dest_schema: dict
    entity_map: dict | None
    field_maps: dict | None
    prompt: str


def build_episode(seed: int, tier: int, n_records: int) -> MigrationEpisode:
    """
    Build a deterministic migration episode.

    Seeds global random and Faker with `seed`, then runs the full pipeline:
    orchestrate → generate_source_data → (Tier 3: obfuscate) → build prompt.

    Identical (seed, tier, n_records) always produces identical output.
    """
    random.seed(seed)
    Faker.seed(seed)

    task = orchestrate(tier)
    source_data = generate_source_data(task.source_schema, n=n_records, gemini_model=None)

    if tier == 3:
        shown_dest_schema, entity_map, field_maps = obfuscate_dest_schema(task.dest_schema)
    else:
        shown_dest_schema = task.dest_schema
        entity_map = None
        field_maps = None

    prompt = build_script_prompt(task.source_schema, shown_dest_schema, source_data)

    return MigrationEpisode(
        task=task,
        source_data=source_data,
        shown_dest_schema=shown_dest_schema,
        entity_map=entity_map,
        field_maps=field_maps,
        prompt=prompt,
    )
