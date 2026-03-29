import os
import time
from dotenv import load_dotenv
load_dotenv()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
if LLM_PROVIDER == "ollama":
    from langchain_ollama import ChatOllama
    def get_large_llm(temperature=0.7):
        return ChatOllama(model=os.getenv("OLLAMA_LARGE_MODEL", "llama3.1:8b"), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), temperature=temperature)
    def get_small_llm(temperature=0.1):
        return ChatOllama(model=os.getenv("OLLAMA_SMALL_MODEL", "llama3.2"), base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), temperature=temperature)
elif LLM_PROVIDER == "anthropic":
    from langchain_anthropic import ChatAnthropic
    def get_large_llm(temperature=0.7):
        return ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=os.getenv("ANTHROPIC_API_KEY"), temperature=temperature, max_tokens=2048)
    def get_small_llm(temperature=0.1):
        return ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=os.getenv("ANTHROPIC_API_KEY"), temperature=temperature, max_tokens=1024)
elif LLM_PROVIDER == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI
    def get_large_llm(temperature=0.7):
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"), temperature=temperature, max_output_tokens=2048)
    def get_small_llm(temperature=0.1):
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"), temperature=temperature, max_output_tokens=1024)
else:
    from langchain_groq import ChatGroq
    def get_large_llm(temperature=0.7):
        return ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"), temperature=temperature, max_tokens=2048)
    def get_small_llm(temperature=0.1):
        return ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"), temperature=temperature, max_tokens=1024)
def call_llm_json(llm, prompt: str, label: str = "") -> str:
    t0 = time.perf_counter()
    response = llm.invoke(prompt)
    elapsed = time.perf_counter() - t0
    tag = f"[{label}] " if label else ""
    print(f"  LLM call took {elapsed:.1f}s")
    return response.content
