
import requests
import time
import subprocess
import sys
import os
import signal

def test_bridge_api():
    print(">>> Testing Bridge API Integration")
    
    # 1. Start Bridge (if not running, but we assume we might need to start it for test)
    # Actually, let's try to connect to localhost:3000 first.
    base_url = "http://localhost:3000"
    
    bridge_process = None
    try:
        try:
            requests.get(f"{base_url}/docs", timeout=2)
            print("Bridge already running.")
        except:
            print("Bridge not running. Starting it...")
            bridge_process = subprocess.Popen([sys.executable, "bridge.py"], cwd=os.getcwd())
            time.sleep(5) # Wait for startup
    
        # 2. Send Execute Request
        payload = {
            "targetUrl": "https://example.com",
            "grade": "Test Grade",
            "topic": "Test Topic",
            "subtopics": "test",
            "materialType": "study_material",
            "sourceType": "general",
            "config": {
                "headless": True, # Test headless
                "modes": {
                    "D": True # Enable NotebookLM
                }
            }
        }
        
        print("Sending /api/auto/execute request...")
        resp = requests.post(f"{base_url}/api/auto/execute", json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print("SUCCESS: API returned success.")
                print(f"Response: {data}")
            else:
                 print(f"FAIL: API returned success=False. {data}")
        else:
            print(f"FAIL: Status code {resp.status_code}")
            print(f"Body: {resp.text}")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if bridge_process:
            print("Killing bridge process...")
            bridge_process.terminate()

if __name__ == "__main__":
    test_bridge_api()
