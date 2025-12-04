# services/openai_client.py
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def call_llm(messages, model: str = "gpt-5-nano") -> str:
    """
    封裝對 OpenAI Chat Completions API 的呼叫。
    messages: list[{"role": "...", "content": "..."}]
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content.strip()
