import os
import time
import subprocess
import requests
import sys

def run_cmd(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result

def wait_for_backend(url, timeout=60):
    print(f"Waiting for backend to be ready at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(2)
    print("Backend failed to become ready in time.")
    return False

def main():
    print("=== Starting Production E2E Test ===")
    
    # 1. Stand up the Docker Compose stack
    run_cmd("docker compose down -v") # Clean state
    run_cmd("docker compose up -d --build")
    
    # 2. Wait for Backend
    is_ready = wait_for_backend("http://localhost:8000/")
    
    if not is_ready:
        print("Fetching backend logs for debugging:")
        run_cmd("docker compose logs backend", check=False)
        run_cmd("docker compose down -v")
        sys.exit(1)
        
    print("\n=== Running E2E Script ===")
    # 3. Run the E2E script
    # Injecting environment variables for the E2E script to point to the local stack
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    if "GEMINI_API_KEY" not in env:
        env["GEMINI_API_KEY"] = "dummy_key"
        
    result = subprocess.run("python test_e2e.py", shell=True, env=env)
    
    if result.returncode == 0:
        print("\n=== E2E Test Passed Successfully! ===")
    else:
        print(f"\n=== E2E Test Failed (Exit Code: {result.returncode}) ===")
        print("Fetching backend logs for debugging:")
        run_cmd("docker compose logs backend", check=False)
        
    # 4. Tear down
    print("\n=== Tearing Down Stack ===")
    run_cmd("docker compose down -v")
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
