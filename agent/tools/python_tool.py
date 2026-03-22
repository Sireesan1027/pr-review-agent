from langchain_core.tools import tool

PYTHON_PROMPT = """You are a Python expert conducting a focused code review.
Analyze ONLY the Python code changes in the diff below.

Focus on:
- PEP 8 violations (naming, line length, imports order)
- Type hints (missing annotations, incorrect types, use of Any)
- Mutable default arguments (def f(x=[]) anti-pattern)
- Context managers (missing `with` for file/db/network resources)
- Django/FastAPI patterns (N+1 queries, missing select_related/prefetch_related, Pydantic misuse)
- Exception handling (bare `except:`, swallowing exceptions, overly broad catches)
- Generator vs list (unnecessary list comprehensions that should be generators)
- Async correctness (blocking calls inside async functions, missing await)
- Security (eval/exec usage, shell injection via subprocess, hardcoded credentials)

Output a concise review with specific line references. If no Python code is present, respond with "No Python code found in diff."

---DIFF---
{diff}
---END DIFF---"""


@tool
def python_expert_review(diff: str) -> str:
    """Run a Python expert review on a code diff.

    Checks PEP8, type hints, async correctness, Django/FastAPI patterns,
    mutable defaults, and common Python anti-patterns.

    Args:
        diff: Unified diff string containing the code changes.

    Returns:
        Detailed Python-specific review feedback.
    """
    return PYTHON_PROMPT.format(diff=diff)
