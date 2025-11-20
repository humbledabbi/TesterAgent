from locator_extractor_1 import extract_locators_for_url, extract_dom_metadata
from ai_test_generator_1 import ask_ai_to_generate_test
from test_executor_1 import run_ai_code_safely
from selenium import webdriver
from urllib.parse import urlparse
from memory_db_1 import init_db, save_step_memory, get_cached_success
import time

def run_agentic_test(start_url, username, password, user_prompt=None,
                     global_steps=None, max_steps=5):

    # Initialize DB
    init_db()

    if not global_steps or len(global_steps) == 0:
        raise ValueError("global_steps cannot be empty. Steps must come from UI input.")

    print("📋 Global steps received:", global_steps)

    print("🧭 Extracting initial DOM metadata...")
    tag_dict = extract_locators_for_url(start_url)

    driver = webdriver.Chrome()
    driver.get(start_url)

    history = []
    log_text = "🧭 Extracting initial DOM metadata...\n"

    base_url = urlparse(start_url).netloc

    current_step_index = 0       # <-- controls which UI step we're on
    agent_steps_taken = 0        # <-- total attempts (not steps)

    while agent_steps_taken < max_steps:

        log_text += f"\n===== Agent Attempt {agent_steps_taken + 1} =====\n"
        print(f"\n===== Agent Attempt {agent_steps_taken + 1} =====")

        # Stop if all UI steps done
        if current_step_index >= len(global_steps):
            print("🎉 All global steps completed.")
            break

        next_required_step = global_steps[current_step_index]
        print(f"➡ Required step: {next_required_step}")

        cached = get_cached_success(base_url, driver.current_url, next_required_step)

        if cached:
            print("⚡ Using cached successful code (skipping LLM)")
            code = cached["code"]

            success = run_ai_code_safely(driver, code)
            driver.save_screenshot(f"cached_{agent_steps_taken + 1}.png")

            if success:
                print("🎯 Cached code succeeded → advancing")
                history.append({
                    "step": current_step_index + 1,
                    "goal": next_required_step,
                    "url": driver.current_url,
                    "success": True
                })
                current_step_index += 1
                agent_steps_taken += 1
                time.sleep(2)
                tag_dict = extract_dom_metadata(driver.page_source)
                continue  # ⬅ SKIP LLM
            else:
                print("❌ Cached code failed → falling back to LLM")
                # (optional later: delete failed memory)

        # Call AI
        ai_plan = ask_ai_to_generate_test(
            url=driver.current_url,
            tag_dict=tag_dict,
            username=username,
            password=password,
            history=history,
            ui_user_prompt=user_prompt,
            global_steps=global_steps,
            next_required_step=next_required_step
        )

        goal = ai_plan.get("goal", "parse_error")
        code = ai_plan.get("code", "")

        print(f"🤖 AI decided: {goal}")

        # Execute code safely
        success = False
        if goal == "no_action" or goal == "parse_error":
            print("⚠️ Ignoring invalid agent action, marking as failure")
        else:
            success = run_ai_code_safely(driver, code)
        driver.save_screenshot(f"step_{agent_steps_taken + 1}.png")

        # Save history
        history.append({
            "step": current_step_index + 1,
            "goal": goal,
            "url": driver.current_url,
            "success": success
        })

        # Save to DB
        try:
            tag_ids = [t.get("id") for t in tag_dict.get("inputs", []) if t.get("id")]
            if goal in ["no_action", "parse_error"]:
                print("🚫 NOT saving invalid step to DB")
            else:
                save_step_memory(
                    base_url=base_url,
                    page_url=driver.current_url,
                    goal=goal,
                    code=code,
                    summary=goal[:120] + "..." if len(goal) > 120 else goal,
                    tags=tag_ids,
                    success=success
                )
                print(f"💾 Step recording saved ({'✅' if success else '❌'})")
        except Exception as db_err:
            print(f"⚠️ DB save error: {db_err}")

        # === STEP CONTROL LOGIC ===
        if success:
            print("🎯 Success → advancing to next UI step")
            current_step_index += 1
        else:
            print("🔁 Failure → staying on same required step")

        agent_steps_taken += 1
        time.sleep(3)
        tag_dict = extract_dom_metadata(driver.page_source)

    driver.quit()

    print("\n📊 Final history:")
    for h in history:
        print(f"- {h['goal']} (success={h['success']})")

    # Build final report
    log_text += "\n📊 Final Test Summary:\n"
    for h in history:
        emoji = "✅" if h["success"] else "❌"
        log_text += f"{emoji} Step {h['step']}: {h['goal']}\n"

    if agent_steps_taken >= max_steps:
        log_text += "\n🛑 Stopped due to max step budget.\n"

    return log_text





if __name__ == "__main__":
    run_agentic_test(
        start_url="https://www.saucedemo.com/",
        username="standard_user",
        password="secret_sauce",
        user_prompt = None,
        max_steps=6
    )
