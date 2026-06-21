import hashlib
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migration_episode import build_episode


def _fingerprint(ep) -> str:
    payload = json.dumps({
        "prompt": ep.prompt,
        "source_data": ep.source_data,
        "shown_dest_schema": ep.shown_dest_schema,
        "entity_map": ep.entity_map,
        "field_maps": ep.field_maps,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def test_build_episode_deterministic():
    a = _fingerprint(build_episode(seed=1007, tier=3, n_records=3))
    b = _fingerprint(build_episode(seed=1007, tier=3, n_records=3))
    assert a == b, f"fingerprints differ:\n  call 1: {a}\n  call 2: {b}"
