"""
Multi-provider LLM factory.
Returns a LangChain-compatible chat model for the given provider.
"""

PROVIDER_MODELS = {
    "openai": [
        {"id": "gpt-4o", "label": "GPT-4o"},
        {"id": "gpt-4o-mini", "label": "GPT-4o Mini (cheaper)"},
    ],
    "anthropic": [
        {"id": "claude-sonnet-4-5-20251001", "label": "Claude Sonnet 4.5"},
        {"id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4.5 (faster)"},
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B (free)"},
        {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant (free, fast)"},
        {"id": "mixtral-8x7b-32768", "label": "Mixtral 8x7B (free)"},
    ],
    "gemini": [
        {"id": "gemini-1.5-flash", "label": "Gemini 1.5 Flash (free tier)"},
        {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
    ],
}


def get_llm(provider: str, api_key: str, model: str):
    """Return a LangChain chat model for the requested provider."""
    provider = provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key, streaming=True)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, streaming=True)

    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key, streaming=True)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, streaming=True)

    else:
        raise ValueError(f"Unknown provider: {provider!r}. Choose from: {list(PROVIDER_MODELS)}")
