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
        # Windows: executables are in 'Scripts' for venv
        exec_dir = 'Scripts'
        executable_name = 'python.exe'
    else:
        # POSIX (Linux, macOS): executables are in 'bin'
        exec_dir = 'bin'
        executable_name = 'python'

    python_path = os.path.join(venv_root, exec_dir, executable_name)

    # Fallback check for Windows systems
    if not os.path.exists(python_path) and sys.platform.startswith('win'):
        python_path = os.path.join(venv_root, 'bin', 'python.exe')

    return python_path


def ensure_test_venv_exists(venv_path):
    """
    Creates the dedicated virtual environment if it doesn't exist and installs
    necessary dependencies (pytest, selenium, webdriver-manager).
    """
    if os.path.isdir(venv_path):
        print(f"\n✅ Dedicated Venv Found: {venv_path}")
        return

    print(f"\n⏳ Creating dedicated Venv: {venv_path}")

    try:
        # Create the venv using the system's current Python interpreter
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        print("🎉 Venv created successfully.")

        # Use the Venv's Python interpreter path for installation
        python_executable = get_venv_python_executable(venv_path)

        # Install necessary testing dependencies
        print("⏳ Installing core test dependencies: pytest, selenium, webdriver-manager...")
        subprocess.run(
            [python_executable, "-m", "pip", "install", "pytest", "selenium", "webdriver-manager"],
            check=True,
            capture_output=True,
            text=True
        )
        print("🎉 Dependencies installed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Venv creation/setup. Deleting partial Venv.")
        print(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        shutil.rmtree(venv_path, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)


def run_pytest_test_file(file_path):
    """
    Executes a specific pytest file using the dedicated Venv's Python interpreter.
    """
    python_executable = get_venv_python_executable(TEST_VENV_PATH)
    print(f"\n🚀 Running generated test using Venv Python: {python_executable}")

    # Command: Execute the "pytest" module using the VENV's Python
    command = [python_executable, "-m", "pytest", file_path]

    try:
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        # Print the output
        print("\n--- Pytest Test Output ---")
        print(result.stdout)
        print("--- Pytest Standard Error (if any) ---")
        print(result.stderr)
        print("--------------------------")

        if result.returncode == 0:
            print("🎉 Result: ALL tests PASSED.")
        elif result.returncode == 1:
            print("❌ Result: Some tests FAILED.")
        else:
            print(
                f"⚠️ Result: Pytest finished with status code {result.returncode} (Internal Error or No tests found).")

    except FileNotFoundError:
        print("❌ Error: Venv Python executable not found. Did the Venv setup fail?")
    except Exception as e:
        print(f"❌ An unexpected error occurred during subprocess execution: {e}")


def cleanup_test_venv(venv_path):
    """
    Safely removes the dedicated virtual environment directory.
    """
    if os.path.isdir(venv_path):
        print(f"\n🗑️ Cleaning up dedicated Venv: {venv_path}...")
        try:
            # shutil.rmtree recursively deletes the directory and its contents
            shutil.rmtree(venv_path)
            print("🎉 Venv deleted successfully.")
        except OSError as e:
            # Handle permissions or other OS-level errors
            print(f"❌ Error deleting Venv directory {venv_path}: {e}")
    else:
        print(f"\n⚠️ Venv directory not found at {venv_path}. Nothing to clean up.")


if __name__ == '__main__':
    print("This module provides utilities and should be imported by the workflow.")