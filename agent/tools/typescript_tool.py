from langchain_core.tools import tool

TYPESCRIPT_PROMPT = """You are a TypeScript/JavaScript expert conducting a focused code review.
Analyze ONLY the TypeScript/JavaScript/TSX/JSX code changes in the diff below.

Focus on:
- TypeScript strictness (`any` usage, type assertions without guards, missing return types)
- React patterns (hooks rules violations, missing dependency arrays, prop drilling, missing keys)
- Async/await correctness (unhandled promise rejections, missing error boundaries, floating promises)
- Type narrowing (missing null checks, improper use of non-null assertion `!`)
- Implicit `undefined` (accessing object properties without optional chaining)
- Bundle size (importing entire libraries instead of tree-shakeable imports)
- Event listener cleanup (missing removeEventListener / subscription cleanup)
- State management issues (direct state mutation, stale closure captures)

Output a concise review with specific line references. If no TS/JS code is present, respond with "No TypeScript/JavaScript code found in diff."

---DIFF---
{diff}
---END DIFF---"""


@tool
def typescript_expert_review(diff: str) -> str:
    """Run a TypeScript/JavaScript expert review on a code diff.

    Checks TypeScript strictness, React hooks rules, async patterns,
    type safety, and common JS/TS anti-patterns.

    Args:
        diff: Unified diff string containing the code changes.

    Returns:
        Detailed TypeScript/JavaScript-specific review feedback.
    """
    return TYPESCRIPT_PROMPT.format(diff=diff)
