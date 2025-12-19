from openai import AsyncOpenAI

def build_openai(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key)
