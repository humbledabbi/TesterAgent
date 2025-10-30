from openai import OpenAI
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

if not api_key:
    raise ValueError("API key not found in .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def ask_ai_to_generate_test(url, tag_dict, username, password):
    system_prompt = """
You are a deterministic automation test generator.
You ALWAYS output valid JSON with two keys: "goal" and "code".
Never hallucinate or guess element locators.
Use only IDs or names exactly as given in the provided DOM metadata.
If "-" exists in IDs or names do not change it or simplify it.
Do not assume any other pages beyond what’s shown.
Always use pytest + Selenium + Chrome.
Return minimal, clean, working code.
"""
    user_prompt = f"""
    Generate a Python pytest using Selenium that performs login on {url}.

    Credentials:
      username: {username}
      password: {password}

    Use the following DOM metadata:
    {json.dumps(tag_dict, indent=2)}

    Verification:
    - After clicking the login button, verify that a header or visible element exists
      that confirms successful login (for example, 'Products' in a span or h1 tag if present).
    - If not visible in DOM, skip the assertion rather than guessing.

    Return:
    {{
      "goal": "short one-line description",
      "code": "complete pytest code"
    }}
    """
    response = client.chat.completions.create(
        model="nvidia/nemotron-nano-9b-v2:free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0  # ✅ fully deterministic
    )

    raw_output = response.choices[0].message.content

    try:
        plan = json.loads(raw_output)
    except json.JSONDecodeError:
        print("⚠️ Model returned non-JSON response, fallback to raw text.")
        plan = {"goal": "Failed to parse JSON", "code": raw_output}

    return plan

if __name__ == '__main__':
    print("This module is designed to be imported, not run directly.")
