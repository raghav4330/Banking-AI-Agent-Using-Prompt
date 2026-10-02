import os
from dotenv import load_dotenv
from google import genai

# Load GEMINI_API_KEY from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Send the prompt and print the response
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain what a banking AI agent is in one sentence.",
)

print(response.text)
