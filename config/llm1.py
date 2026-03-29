import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL",  "http://localhost:11434")
LARGE_MODEL      = os.getenv("OLLAMA_LARGE_MODEL", "llama3.1:8b")
SMALL_MODEL      = os.getenv("OLLAMA_SMALL_MODEL", "llama3.2")


def get_large_llm(temperature: float = 0.7) -> ChatOllama:
    """llama3.1:8b — drafting, research synthesis, complex reasoning."""
    return ChatOllama(
        model=LARGE_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )


def get_small_llm(temperature: float = 0.1) -> ChatOllama:
    """llama3.2 — classification, rule matching, structured tasks."""
    return ChatOllama(
        model=SMALL_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )


def call_llm_json(llm: ChatOllama, prompt: str) -> str:
    """Call LLM and return raw string content. Caller handles JSON parsing."""
    response = llm.invoke(prompt)
    return response.content
