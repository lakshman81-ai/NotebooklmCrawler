
import requests
import time
import subprocess
import os

def trigger_mission():
    url = "http://localhost:3000/api/auto/execute"
    payload = {
        "targetUrl": "https://www.khanacademy.org/science/physics/forces-newtons-laws",
        "grade": "Grade 8",
        "topic": "Force and Pressure",
        "subtopics": "pressure in fluids, Newton's laws",
        "materialType": "Summary",
        "sourceType": "general",
        "config": {
            "headless": False,
            "maxTokens": 1200,
            "strategy": "section_aware",
            "modes": {"D": True}
        }
    }
    print(f">>> Triggering mission via {url}")
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Response: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Failed to trigger: {e}")

def monitor_logs():
    log_file = os.path.join("logs", "app.log")
    print(f">>> Monitoring {log_file} for 'Auto-approved' messages...")
    
    # Read last 10 lines, then follow
    try:
        with open(log_file, "r") as f:
            # Go to end
            f.seek(0, os.SEEK_END)
            start_time = time.time()
            while time.time() - start_time < 120: # Monitor for 2 mins
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                if "Auto-approved" in line or "Login detected" in line or "Google Login Required" in line:
                    print(f"LOG: {line.strip()}")
                elif "ERROR" in line or "CRITICAL" in line:
                    print(f"ERROR LOG: {line.strip()}")
                elif "Starting NotebookLM" in line:
                     print(f"LOG: {line.strip()}")
    except FileNotFoundError:
        print("Log file not found yet.")

if __name__ == "__main__":
    trigger_mission()
    monitor_logs()
