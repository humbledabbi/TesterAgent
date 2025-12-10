from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from controller_1 import run_agentic_test
from openai import OpenAI
import os, re, json
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

class ChatRequest(BaseModel):
    user_prompt: str

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_KEY")
)

def extract_test_parameters(user_text: str):
    """
    Extracts URL, username, password, and goal either via regex or fallback LLM parsing.
    """
    url_match = re.search(r"https?://[^\s]+", user_text)
    username_match = re.search(r"username\s*[:=]\s*(\S+)", user_text)
    password_match = re.search(r"password\s*[:=]\s*(\S+)", user_text)

    url = url_match.group(0) if url_match else None
    username = username_match.group(1) if username_match else None
    password = password_match.group(1) if password_match else None
    goal = None

    if not all([url, username, password]):
        print("⚠️ Missing info → falling back to LLM extraction")

        response = client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2:free",
            messages=[
                {"role": "system", "content": "Extract website URL, username, password, and testing goal from text. Output valid JSON only."},
                {"role": "user", "content": user_text},
            ],
        )

        try:
            content = response.choices[0].message.content
            print("🧠 LLM Extraction:", content)
            parsed = json.loads(content)

            url = url or parsed.get("url")
            username = username or parsed.get("username")
            password = password or parsed.get("password")
            goal = parsed.get("goal")

        except Exception as e:
            print("❌ LLM parse error, failing over:", e)
            goal = user_text
    else:
        goal = user_text

    return url, username, password, goal


def parse_steps_from_ui_prompt(ui_text: str):
    """
    Extract ordered steps from user UI input.
    Supports formats:
    1. Step
    2) Step
    3 - Step
    - bullet step
    * bullet step
    """
    steps = []
    import re

    numbered = re.compile(r"^\s*(\d+)[\.\-\)]\s+(.*)$")
    bullet   = re.compile(r"^\s*[\*\-\+]\s+(.*)$")

    for line in ui_text.splitlines():
        line = line.strip()

        m = numbered.match(line)
        if m:
            steps.append(m.group(2).strip())
            continue

        b = bullet.match(line)
        if b:
            steps.append(b.group(1).strip())
            continue

    return steps


@router.post("/", response_class=PlainTextResponse)
def chat_with_ai(request: ChatRequest):
    user_text = request.user_prompt
    print(f"🧠 User said: {user_text}")

    url, username, password, goal = extract_test_parameters(user_text)
    print(f"🌐 URL: {url}, 👤 Username: {username}, 🔑 Password: {password}, 🎯 Goal: {goal}")

    if not url:
        return "❌ Couldn't detect a valid URL in your message."

    # 1️⃣ Try extracting steps from user input
    global_steps = parse_steps_from_ui_prompt(user_text)

    # 2️⃣ Try extracting steps from LLM-extracted goal
    if not global_steps and goal:
        global_steps = parse_steps_from_ui_prompt(goal)

    # 3️⃣ Bail if we have no steps
    if not global_steps:
        return (
            "❌ I couldn't detect any ordered steps.\n"
            "Please provide them like:\n"
            "1. Login\n2. Add item\n3. Verify cart"
        )

    print(f"📋 Parsed Steps: {global_steps}")

    try:
        result_text = run_agentic_test(
            start_url=url,
            username=username or "",
            password=password or "",
            user_prompt=goal,
            global_steps=global_steps,
            max_steps=8  # You control the limit
        )
        return result_text

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"❌ Error: {e}"
