
import os
import json
import sys
from contracts.content_request import ContentRequest
from postprocess.context_builder import build_context

# Mock Environment Variables (Simulating UI Launch)
os.environ["CR_GRADE"] = "Grade 8"
os.environ["CR_TOPIC"] = "Physics Verification"
os.environ["CR_SUBTOPICS"] = "kinematics, dynamics"
os.environ["CR_OUTPUT_TYPE"] = "mixed_outputs"
os.environ["CR_SOURCE_TYPE"] = "notebooklm"
os.environ["CR_DIFFICULTY"] = "Extend"
os.environ["CR_KEYWORDS_REPORT"] = "Gap Analysis"
os.environ["CR_OUTPUT_CONFIG"] = json.dumps({"quiz": True, "studyGuide": True, "handout": False})
os.environ["CR_QUIZ_CONFIG"] = json.dumps({"mcq": 15, "ar": 5})

print(">>> SIMULATION: Starting Logic Verification...")

try:
    # 1. Test run.py request parsing (Importing function dynamically to avoid running main)
    # We'll just manually test the logic that is in run.py's get_content_request
    # Copying logic for isolation or importing run if safe? 
    # run.py imports crawler etc, might be heavy. Let's just test the model directly or minimal import.
    from run import get_content_request
    
    print(">>> STEP 1: Calling get_content_request()...")
    req = get_content_request()
    
    print(f"    [PASS] Grade: {req.grade}")
    print(f"    [PASS] Difficulty: {req.difficulty}")
    print(f"    [PASS] Output Config: {req.output_config}")
    
    assert req.difficulty == "Extend", "Difficulty mismatch"
    assert req.output_config.get("quiz") is True, "Quiz config mismatch"
    
    # 2. Test Context Builder
    print(">>> STEP 2: Calling build_context()...")
    ctx = build_context(req)
    
    print(f"    [PASS] Context Difficulty: {ctx.get('difficulty')}")
    assert ctx.get('difficulty') == "Extend", "Context Difficulty mismatch"
    assert ctx.get('output_config', {}).get('studyGuide') is True, "Context StudyGuide mismatch"

    print("\n>>> VERIFICATION SUCCESS: Data flow from ENV -> Request -> Context is correct.")

except Exception as e:
    print(f"\n>>> VERIFICATION FAILED: {str(e)}")
    sys.exit(1)
