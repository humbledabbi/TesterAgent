import os
import sys
import subprocess
import shutil

# --- Configuration ---
TEST_VENV_DIR = ".venv-tests"
TEST_VENV_PATH = os.path.join(os.getcwd(), TEST_VENV_DIR)


# --- OS-Agnostic Venv Helpers ---

def get_venv_python_executable(venv_root):
    """
    Returns the absolute path to the Python executable within a virtual environment,
    regardless of the operating system (Windows, Linux, macOS).
    """
    if sys.platform.startswith('win'):
        exec_dir = 'Scripts'
        executable_name = 'python.exe'
    else:
        exec_dir = 'bin'
        executable_name = 'python'

    python_path = os.path.join(venv_root, exec_dir, executable_name)

    # Fallback check for weird path edge cases
    if not os.path.exists(python_path) and sys.platform.startswith('win'):
        python_path = os.path.join(venv_root, 'bin', 'python.exe')

    return python_path


def ensure_test_venv_exists(venv_path=TEST_VENV_PATH):
    """
    Creates the dedicated virtual environment if it doesn't exist and installs
    necessary dependencies (pytest, selenium, webdriver-manager).
    """
    if os.path.isdir(venv_path):
        print(f"\n✅ Dedicated test venv found: {venv_path}")
        return

    print(f"\n⏳ Creating dedicated test venv: {venv_path}")
    try:
        # Create venv
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print("🎉 Virtual environment created successfully.")

        python_executable = get_venv_python_executable(venv_path)

        # Install dependencies
        print("⏳ Installing dependencies: selenium, webdriver-manager, pytest")
        subprocess.run(
            [python_executable, "-m", "pip", "install", "--upgrade", "pip", "selenium", "webdriver-manager", "pytest"],
            check=True
        )
        print("🎉 Dependencies installed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        shutil.rmtree(venv_path, ignore_errors=True)
        sys.exit(1)


def cleanup_test_venv(venv_path=TEST_VENV_PATH):
    """Deletes the dedicated venv safely."""
    if os.path.isdir(venv_path):
        print(f"\n🗑️ Cleaning up dedicated test venv: {venv_path}")
        shutil.rmtree(venv_path, ignore_errors=True)
        print("✅ Cleanup complete.")
    else:
        print("⚠️ No test venv found to clean.")
