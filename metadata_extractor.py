import openai
import os
import json
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_metadata(text, classification):
    if classification != "Contract":
        return {}

    prompt = f"""
Extract key metadata from this service contract. Return in JSON format:

Fields to extract:
- Client
- Provider
- Start Date
- End Date (if specified)
- Monthly Payment
- Termination Terms (if available)
- Agreement Title

Document:
\"\"\"
{text}
\"\"\"
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response['choices'][0]['message']['content']
        return json.loads(content)
    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        return {}
