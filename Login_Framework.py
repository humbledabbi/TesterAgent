from openai import OpenAI
import json
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

if not api_key:
    raise ValueError("API key not found in .env file")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def get_rendered_html(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)  # allow JS to render
    html = driver.page_source
    driver.quit()
    return html

def extract_dom_metadata(html):
    """Extracts relevant login field info from DOM for AI context."""
    soup = BeautifulSoup(html, "html.parser")
    inputs = []
    for tag in soup.find_all("input"):
        inputs.append({
            "id": tag.get("id"),
            "name": tag.get("name"),
            "placeholder": tag.get("placeholder"),
            "type": tag.get("type")
        })
    buttons = []
    for tag in soup.find_all("button"):
        buttons.append({
            "id": tag.get("id"),
            "text": tag.text.strip(),
            "type": tag.get("type")
        })
    return {"inputs": inputs, "buttons": buttons}


def ask_ai_to_generate_test(url, html, username, password):
    """Generate consistent pytest + Selenium test code based on DOM."""

    dom_summary = extract_dom_metadata(html)

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
{json.dumps(dom_summary, indent=2)}

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

## ⚙️ Step 4 — Example Use


url = "https://www.saucedemo.com/"
html = get_rendered_html(url)
summary = extract_dom_metadata(html)
print(json.dumps(summary, indent=2))

plan = ask_ai_to_generate_test(
    "https://www.saucedemo.com/",
    html,
    "standard_user",
    "secret_sauce"
)

print("AI Goal:", plan["goal"])

with open("test_login_ai.py", "w", encoding="utf-8") as f:
    f.write(plan["code"])

