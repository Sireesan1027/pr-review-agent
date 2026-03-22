"""
LangGraph ReAct agent for PR code review.

Flow:
  START → agent node (ReAct loop) → tool calls → synthesize → END

The agent:
  1. Receives the diff + PR metadata
  2. Detects which languages are present
  3. Calls the appropriate language expert tools + security_scanner
  4. Synthesizes a final structured review
"""

import asyncio
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from agent.llm_factory import get_llm
from agent.tools.java_tool import java_expert_review
from agent.tools.python_tool import python_expert_review
from agent.tools.typescript_tool import typescript_expert_review
from agent.tools.security_tool import security_scanner

SYSTEM_PROMPT = """You are a senior software engineer and security expert conducting a thorough PR code review.

You have access to the following specialist tools:
- java_expert_review: Use when the diff contains Java or Kotlin code
- python_expert_review: Use when the diff contains Python code
- typescript_expert_review: Use when the diff contains TypeScript, JavaScript, TSX, or JSX code
- security_scanner: ALWAYS call this regardless of language

Your process:
1. Examine the diff to detect which programming languages are present
2. Call the relevant language expert tool(s) for each detected language
3. Always call security_scanner
4. After collecting all tool results, synthesize a final structured review

Final review format:
## PR Review: {title}

### 1. Summary
(What does this PR do? 2-3 sentences)

### 2. Language-Specific Findings
(Results from language expert tools)

### 3. Security
(Results from security_scanner)

### 4. Code Quality
(Readability, naming, duplication, overall structure)

### 5. Test Coverage
(Are changes tested? What's missing?)

### 6. Suggestions
(Specific improvements with examples)

### 7. Overall Verdict
**APPROVE** / **REQUEST CHANGES** / **NEEDS DISCUSSION** — one-line reason

Be direct, reference file names and line numbers. If a section has no issues, write "No issues found."
"""

REVIEW_TOOLS = [
    java_expert_review,
    python_expert_review,
    typescript_expert_review,
    security_scanner,
]


def build_agent(provider: str, api_key: str, model: str):
    """Build a LangGraph ReAct agent with the given LLM."""
    llm = get_llm(provider, api_key, model)
    agent = create_react_agent(
        model=llm,
        tools=REVIEW_TOOLS,
        prompt=SYSTEM_PROMPT,
    )
    return agent


async def stream_review(
    provider: str,
    api_key: str,
    model: str,
    diff: str,
    pr_title: str,
    pr_description: str,
) -> AsyncIterator[str]:
    """
    Run the LangGraph agent and stream text chunks.
    Yields string chunks as they arrive from the LLM.
    """
    agent = build_agent(provider, api_key, model)

    user_message = f"""Please review the following pull request.

PR Title: {pr_title or "(no title)"}
PR Description: {pr_description or "(no description)"}

---DIFF START---
{diff}
---DIFF END---

Follow your instructions: detect languages, call the appropriate expert tools and security_scanner, then write the final structured review."""

    inputs = {"messages": [HumanMessage(content=user_message)]}

    async for event in agent.astream_events(inputs, version="v2"):
        kind = event.get("event")

        # Stream LLM text tokens
        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content

        # Notify when a tool is being called
        elif kind == "on_tool_start":
            tool_name = event.get("name", "")
            yield f"\n\n> Running **{tool_name}**...\n\n"

        # Notify when a tool finishes
        elif kind == "on_tool_end":
            tool_name = event.get("name", "")
            yield f"> `{tool_name}` complete.\n\n"
