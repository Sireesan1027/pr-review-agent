from langchain_core.tools import tool

JAVA_PROMPT = """You are a Java expert conducting a focused code review.
Analyze ONLY the Java/Kotlin code changes in the diff below.

Focus on:
- Spring Boot / Spring MVC patterns (missing @Transactional, wrong bean scope, etc.)
- Null safety (NPE risks, missing Optional usage, unchecked casts)
- Exception handling (swallowed exceptions, catching Exception/Throwable, checked vs unchecked)
- OOP principles (SRP violations, improper inheritance, missing interfaces)
- JPA/Hibernate pitfalls (N+1 queries, missing lazy/eager annotations, cartesian products)
- Lombok misuse (@Data on entities, missing @EqualsAndHashCode(callSuper))
- Thread safety (shared mutable state, missing synchronization)
- Resource leaks (unclosed streams, connections)

Output a concise review with specific line references. If no Java/Kotlin code is present, respond with "No Java/Kotlin code found in diff."

---DIFF---
{diff}
---END DIFF---"""


@tool
def java_expert_review(diff: str) -> str:
    """Run a Java/Kotlin expert review on a code diff.

    Checks Spring Boot patterns, null safety, JPA pitfalls, exception handling,
    Lombok misuse, and thread safety issues.

    Args:
        diff: Unified diff string containing the code changes.

    Returns:
        Detailed Java-specific review feedback.
    """
    # This tool is called by the LangGraph agent which passes it to the LLM.
    # The agent fills the prompt and returns the LLM response.
    return JAVA_PROMPT.format(diff=diff)
