# UI Fixes Needed - Based on User Screenshot

## Priority Issues to Fix

### 1. ✅ URL Input Field - Convert to Textarea
**Location:** Dashboard (INPUT mode https://example.com/a_hi... field)
**Current:** Single-line input that truncates long URLs
**Fix:** Convert to textarea or multi-line input with word wrap
**File:** Dashboard/AutoMode.jsx or InputMode component

### 2. ✅ Intelligence Source - Fix Overlapping Text
**Location:** Intelligence Source section
**Current:** Shows "AUTOGOOGLEDUCKDUCKGONOTEBOOKLM" as one string
**Fix:**  Proper spacing between toggle buttons - should show as separate options:
- AUTO
- GOOGLE
- DUCKDUCKGO  
- NOTEBOOKLM

### 3. ✅ Disable Topic Source Conditional
**Requirement:** Disable "Topic Source" dropdown when "Web Search" toggle is OFF
**Logic:** topicSource.disabled = !webSearchEnabled

### 4. ✅ Font & Style Improvements
**Requirements:**
- More elegant, professional typography
- Cleaner spacing and alignment
- Modern, readable fonts (consider Inter, Roboto, or system fonts)
- Consistent sizing and weights

### 5. ⚠️ White Screen on Logs/Config Tabs
**Status:** Need to verify - imports look correct
**Action:** Test after deploying UI fixes

---

## Implementation Order

1. Fix Intelligence Source button layout (highest visual priority)
2. Convert URL input to textarea
3. Add Topic Source conditional disable
4. Improve typography and spacing
5. Test Logs/Config tabs for white screen issue
