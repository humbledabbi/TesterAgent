import sys
import requests
import os
from Login_Framework import ask_ai_to_generate_test
from test_executor import (
    ensure_test_venv_exists,
    run_pytest_test_file,
    cleanup_test_venv,
    TEST_VENV_PATH  # Import the constant for venv path
)

# --- Constants ---
TEST_FILE_NAME = "test_login_ai.py"


def main():
    # 1. SETUP - Check/create the isolated testing environment
    ensure_test_venv_exists(TEST_VENV_PATH)

    # Use a try...finally block to GUARANTEE cleanup happens, even if an error occurs
    try:
        # 2. Prepare Data (URL Fetch)
        url = "https://www.saucedemo.com/"
        print(f"\n🔌 Fetching HTML from {url}...")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html = response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch URL: {e}")
            # Allow finally block to handle cleanup
            return

        # 3. Generate Test Code
        print("🧠 Asking AI to generate test code...")
        plan = ask_ai_to_generate_test(
            url,
            html,
            "standard_user",
            "secret_sauce"
        )

        # 4. Save Test Code
        with open(TEST_FILE_NAME, "w") as f:
            f.write(plan["code"])

        print(f"\nAI Goal: {plan['goal']}")
        print(f"📝 Test code saved to {TEST_FILE_NAME}")

        # 5. Execute Test
        run_pytest_test_file(TEST_FILE_NAME)

    except Exception as e:
        print(f"\n🛑 An unhandled error occurred during the main process: {e}")

    finally:
        # --- 6. CLEANUP (THIS BLOCK IS GUARANTEED TO RUN) ---

        # # Clean up the temporary generated test file
        # if os.path.exists(TEST_FILE_NAME):
        #     os.remove(TEST_FILE_NAME)
        #     print(f"\n🗑️ Cleaned up temporary file: {TEST_FILE_NAME}")

        # Clean up the Venv directory
        cleanup_test_venv(TEST_VENV_PATH)


if __name__ == "__main__":
    main()