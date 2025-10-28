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

def ask_ai_to_generate_test(url, html, username, password):
    prompt = f"""
You are an automation testing expert.
You will generate Python pytest + Selenium code that tests login on {url}.

Use the given HTML DOM to infer the login form fields.

Credentials:
  username: {username}
  password: {password}

Return only JSON with two keys:
- goal: a short sentence describing what the test verifies
- code: a complete pytest test using Selenium

DOM snippet:
```html
{html[:6000]}
"""

    response = client.chat.completions.create(
        model="nvidia/nemotron-nano-9b-v2:free",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content
    print("raw output observed", raw_output)
    return json.loads(raw_output)


## ⚙️ Step 4 — Example Use


url = "https://www.saucedemo.com/"
response = requests.get(url)
html = response.text
plan = ask_ai_to_generate_test(
    "https://www.saucedemo.com/",
    html,
    "standard_user",
    "secret_sauce"
)

print("AI Goal:", plan["goal"])

with open("test_login_ai.py", "w") as f:
    f.write(plan["code"])