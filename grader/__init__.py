"""MigrateGym grader package.

Public entry point:

    from grader import Grader
    result = Grader(source_schema, transformations).grade(source_data, dest_data)
"""

try:
    from .grader import Grader
except ImportError:  # allow flat-script usage
    from grader import Grader

__all__ = ["Grader"]
