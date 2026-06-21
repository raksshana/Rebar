from harness.env import env

tasks = [
    env.task("migrate", slug=f"rebar-t3-{i:02d}", tier=3)
    for i in range(1, 21)
]
