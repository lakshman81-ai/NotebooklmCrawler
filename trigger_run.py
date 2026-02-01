import requests
import json

url = "http://localhost:8000/api/auto/execute"
payload = {
  "targetUrl": "https://byjus.com/jee/gravitation/",
  "grade": "General",
  "topic": "Analysis",
  "subtopics": "",
  "materialType": "study_material",
  "sourceType": "trusted",
  "config": {
    "headless": True,
    "maxTokens": 2000,
    "strategy": "section_aware",
    "modes": {"D": True},
    "discoveryMethod": "notebooklm",
    "difficulty": "Medium",
    "outputs": {"studyGuide": True, "quiz": True}
  }
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
