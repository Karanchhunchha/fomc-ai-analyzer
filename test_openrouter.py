import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

try:
    print("Testing OpenRouter streaming with model: moonshotai/kimi-k2.6:free")
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2.6:free",
        messages=[{"role": "user", "content": "Explain monetary policy in a long paragraph."}],
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
    print("\nStream successful.")
except Exception as e:
    print("\nError:", e)
