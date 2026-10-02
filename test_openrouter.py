import os
import httpx
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")

if not api_key or api_key == "your_openrouter_api_key_here":
    raise ValueError(
        "OPENROUTER_API_KEY is not set or still has the placeholder value in .env."
    )

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://localhost",
    "X-Title": "Banking AI Agent",
}

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "Explain what a banking AI agent is in one sentence."}
    ],
}

response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
response.raise_for_status()

data = response.json()
reply = data["choices"][0]["message"]["content"]

print(reply)
