from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    diff: str
    pr_title: str
    pr_description: str
    messages: Annotated[list[BaseMessage], operator.add]
    review_sections: dict
    final_review: str
