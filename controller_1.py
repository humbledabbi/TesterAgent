from locator_extractor_1 import extract_locators_for_url, extract_dom_metadata
from ai_test_generator_1 import ask_ai_to_generate_test
from test_executor_1 import run_ai_code_safely
from selenium import webdriver
import time

def run_agentic_test(start_url, username, password, user_prompt=None, max_steps=3):
    print("🧭 Extracting initial DOM metadata...")
    tag_dict = extract_locators_for_url(start_url)

    driver = webdriver.Chrome()
    driver.get(start_url)

    history = []
    log_text = "🧭 Extracting initial DOM metadata...\n"
    for step in range(max_steps):
        log_text += f"\n===== Step {step + 1} =====\n"
        print(f"\n===== Step {step + 1} =====")

        ai_plan = ask_ai_to_generate_test(
            url=driver.current_url,
            tag_dict=tag_dict,
            username=username,
            password=password,
            history=history,
            user_prompt=user_prompt
        )

        print(f"🤖 AI decided: {ai_plan['goal']}")

        success = run_ai_code_safely(driver, ai_plan["code"])
        driver.save_screenshot(f"step_{step + 1}.png")

        history.append({
            "step": step + 1,
            "goal": ai_plan["goal"],
            "url": driver.current_url,
            "success": success
        })

        time.sleep(3)
        tag_dict = extract_dom_metadata(driver.page_source)

        if "cart" in driver.current_url or step == max_steps - 1:
            print("🛑 Ending test sequence.")
            break

    driver.quit()

    print("\nFinal history:")
    for h in history:
        print(f"- {h['goal']} (success={h['success']})")

    # 🔹 Clean final report
    log_text += "\n📊 Final Test Summary:\n"
    for h in history:
        emoji = "✅" if h["success"] else "❌"
        log_text += f"{emoji} Step {h['step']}: {h['goal']}\n"

    return log_text



if __name__ == "__main__":
    run_agentic_test(
        start_url="https://www.saucedemo.com/",
        username="standard_user",
        password="secret_sauce",
        user_prompt = None,
        max_steps=6
    )
