def validate_schema(schema):
    """Returns list of problem strings. Empty list = valid schema."""
    problems = []
    entities = schema.get("entities", {})
    nested_blocks = schema.get("nested_blocks", {})

    collisions = set(entities.keys()) & set(nested_blocks.keys())
    for name in collisions:
        problems.append(f"Name '{name}' exists in both entities and nested_blocks")

    for ename, entity in entities.items():
        fields = entity.get("fields", {})
        id_fields = [f for f, d in fields.items() if d.get("kind") == "id"]
        if len(id_fields) == 0:
            problems.append(f"Entity '{ename}': no 'id' field")
        elif len(id_fields) > 1:
            problems.append(f"Entity '{ename}': multiple 'id' fields: {id_fields}")

        for fname, fdef in fields.items():
            kind = fdef.get("kind")
            if kind == "ref":
                target = fdef.get("target")
                if target not in entities:
                    problems.append(
                        f"Entity '{ename}', field '{fname}': ref.target '{target}' not in entities"
                    )
            elif kind == "nested":
                of = fdef.get("of")
                if of not in nested_blocks:
                    problems.append(
                        f"Entity '{ename}', field '{fname}': nested.of '{of}' not in nested_blocks"
                    )

    return problems
