
import asyncio
import sys
import os
from pathlib import Path

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Mock FastAPI request
class MockRequest:
    def __init__(self):
        self.targetUrl = "http://test.com"
        self.grade = "8"
        self.topic = "Test"
        self.subtopics = "foo,bar"
        self.materialType = "guide"
        self.sourceType = "general"
        self.config = {
            "headless": True,
            "maxTokens": 100,
            "strategy": "fixed",
            "modes": {"D": True},
            "discoveryMethod": "Auto"
        }

async def test_internal_logic():
    print(">>> Testing Bridge Internal Logic")
    try:
        from bridge import execute_pipeline, ExecutionRequest
        
        req = ExecutionRequest(**MockRequest().__dict__)
        
        print("Invoking execute_pipeline()...")
        result = await execute_pipeline(req)
        
        print(f"Result: {result}")
        if result.get("success"):
            print("SUCCESS: Logic executed without error.")
        else:
            print("FAIL: Logic returned failure.")
            
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_internal_logic())
