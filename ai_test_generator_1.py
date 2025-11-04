from openai import OpenAI
import json, os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key= api_key)


def ask_ai_to_generate_test(url, tag_dict, username, password, history=None):
    system_prompt = """
You are a deterministic Selenium test planner.
You generate ONE small executable step for the next page action.
You ALWAYS output JSON with "goal" and "code".
Never hallucinate or rename locators.
Use only provided DOM metadata.
The WebDriver (driver) already exists. Do not quit or reinitialize it.
Use Selenium 4+ syntax (By).
Always include `from selenium.webdriver.common.by import By`.
Always wait for elements using WebDriverWait before interacting.
Example:
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login-button"))).click()
"""
    user_prompt = f"""
Current page URL: {url}

History so far:
{json.dumps(history or [], indent=2)}

DOM Metadata:
{json.dumps(tag_dict, indent=2)}

Credentials:
username = {username}
password = {password}

Goal: Continue the SauceDemo test flow:
1. Login if not yet logged in
2. If logged in, add "Sauce Labs Backpack" (or any bag) to cart
3. Verify cart update

Return:
{{
  "goal": "one-line description",
  "code": "Python code using Selenium that executes this step"
}}
"""

    response = client.chat.completions.create(
        model="nvidia/nemotron-nano-9b-v2:free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"goal": "parse_error", "code": response.choices[0].message.content}
