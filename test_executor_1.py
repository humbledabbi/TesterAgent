# test_executor_1.py
import textwrap

def run_ai_code_safely(driver, code):
    # ---- Basic safety ----
    forbidden = [
        "webdriver.Chrome",
        "driver.quit",
        "os.",
        "subprocess",
        "open(",
        "socket",
        "shutil",
        "sys.exit",
        "eval(",
        "exec("
    ]
    for bad in forbidden:
        if bad in code:
            print(f"🚫 Unsafe pattern detected: {bad}")
            return False

    # ---- Normalize indentation ----
    code = textwrap.dedent(code).strip()

    # ---- Ensure import By exists (correct logic) ----
    if "from selenium.webdriver.common.by import By" not in code:
        code = (
            "from selenium.webdriver.common.by import By\n" +
            code
        )

    # ---- Execute with restricted globals ----
    try:
        safe_globals = {"driver": driver}
        exec(code, safe_globals)
        return True
    except Exception as e:
        print(f"❌ Execution error: {e}")
        return False
