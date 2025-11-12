from openai import OpenAI
import json, os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key= api_key)


def ask_ai_to_generate_test(url, tag_dict, username, password, history=None, user_prompt=None):
    system_prompt = """
    You are a deterministic Selenium test planner.
    Your task is to generate ONE small, executable Python step for the next web page action.

    RULES:
    1. You MUST output ONLY a valid JSON object.
    2. Do NOT include markdown formatting (no ```json or ``` anywhere).
    3. The JSON MUST contain exactly two keys: "goal" and "code".
    4. The "goal" is a short natural language description of the step.
    5. The "code" is valid Python Selenium 4+ code using the existing `driver` object.
    6. Never create, reinitialize, or quit the WebDriver.
    7. Never invent or rename locators — only use provided DOM metadata.
    8. Always use `from selenium.webdriver.common.by import By`.
    9. Always use WebDriverWait for clickable or visible elements.
    10. No explanations or text outside the JSON object.

    Example of valid output:
    {
      "goal": "Click the login button",
      "code": "from selenium.webdriver.common.by import By\\nfrom selenium.webdriver.support.ui import WebDriverWait\\nfrom selenium.webdriver.support import expected_conditions as EC\\nWebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'login-button'))).click()"
    }
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

Goal: {user_prompt or "Continue the SauceDemo test flow"}

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
