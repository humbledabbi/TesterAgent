# test_executor_1.py
import textwrap

def run_ai_code_safely(driver, code):
    if "webdriver.Chrome" in code or "driver.quit" in code:
        print("🚫 Unsafe code detected — skipping.")
        return False

    try:
        code = textwrap.dedent(code).strip()
        exec(code, {"driver": driver})
        return True
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return False
