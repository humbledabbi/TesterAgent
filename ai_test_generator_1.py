from openai import OpenAI
import json, os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def ask_ai_to_generate_test(
    url,
    tag_dict,
    username,
    password,
    history=None,
    ui_user_prompt=None,
    global_steps=None,          # 🔥 NEW
    next_required_step=None     # 🔥 NEW
):
    """
    Deterministic Selenium step generator.
    Produces EXACTLY one next step based on UI-provided global steps.
    """

    if not global_steps:
        raise ValueError("global_steps is required but missing.")

    if not next_required_step:
        raise ValueError("next_required_step is required but missing.")


    # --------------------------
    # 🧩 Build final prompt sent to LLM
    # --------------------------
    step_index = len(history or [])

    final_prompt = f"""
Current URL: {url}

Completed History:
{json.dumps(history or [], indent=2)}

Next Required Step (from UI):
"{next_required_step}"

All Global Steps:
{json.dumps(global_steps, indent=2)}

DOM Metadata:
{json.dumps(tag_dict, indent=2)}

Credentials:
username = {username}
password = {password}

User Freeform Prompt (optional):
"{ui_user_prompt or ''}"

IMPORTANT EXECUTION RULES:
- You MUST execute EXACTLY this required step: "{next_required_step}"
- NEVER skip or reorder steps.
- NEVER perform any step not listed in global_steps.
- NEVER redo login after success.
- ONLY use elements present in DOM metadata.
- NEVER invent XPaths, IDs, names, or CSS selectors.
- If this step cannot be performed with current DOM:
  Return exactly: {{"goal": "no_action", "code": ""}}

Return ONLY valid JSON:
{{
  "goal": "{next_required_step}",
  "code": "Python Selenium code for ONLY this step"
}}
"""

    # --------------------------
    # 🧠 System prompt
    # --------------------------
    system_prompt = """
You are a STRICT deterministic Selenium automation agent.
You must generate exactly ONE next test step based on an externally provided sequence.

RULES:
1. You MUST follow the next_required_step exactly.
2. You MUST NOT generate any other step.
3. You MUST NOT invent DOM locators.
4. You MUST return ONLY valid JSON with "goal" and "code".
5. If step cannot be performed: return {"goal": "no_action", "code": ""}.


Always include this import at the top of the code:

from selenium.webdriver.common.by import By


"""

    # --------------------------
    # 🧠 Debug logging
    # --------------------------

    print("🧠 ===== PROMPT SENT TO MODEL (first 1500 chars) =====")
    print(final_prompt[:1500])
    print("======================================================\n")

    # --------------------------
    # 📤 Send prompt to OpenRouter
    # --------------------------
    response = client.chat.completions.create(
        model="nvidia/nemotron-nano-9b-v2:free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    # --------------------------
    # 🧾 Safe JSON extraction
    # --------------------------
    try:
        json_str = raw[raw.index("{"): raw.rindex("}") + 1]
        parsed = json.loads(json_str)
        print(f"✅ Model returned goal: {parsed.get('goal')}")
        return parsed

    except Exception:
        print("⚠️ JSON parsing failed. Raw output:\n", raw)
        return {"goal": "parse_error", "code": raw}
