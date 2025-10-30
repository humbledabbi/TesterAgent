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
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# --- Constants ---
TEST_FILE_NAME = "test_login_ai.py"


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


def main():
    # 1. SETUP - Check/create the isolated testing environment
    ensure_test_venv_exists(TEST_VENV_PATH)

    # Use a try...finally block to GUARANTEE cleanup happens, even if an error occurs
    try:
        # 2. Prepare Data (URL Fetch)
        url = "https://www.saucedemo.com/"
        print(f"\n🔌 Fetching HTML from {url}...")
        try:
            html = get_rendered_html(url)
            tag_dict = extract_dom_metadata(html)
        except Exception as e:
            print(f"❌ Failed to fetch URL: {e}")
            # Allow finally block to handle cleanup
            return

        # 3. Generate Test Code
        print("🧠 Asking AI to generate test code...")
        plan = ask_ai_to_generate_test(
            url,
            tag_dict,
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