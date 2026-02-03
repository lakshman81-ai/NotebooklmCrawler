# NotebookLM Crawler - Implementation Plan

**Created**: 2026-02-03
**Priority**: NotebookLM-first approach with URL discovery via Google/DDG
**Target**: Grade 8 educational content pipeline

---

## Current State Assessment

### What's Working
| Component | Status | Location |
|-----------|--------|----------|
| NotebookLM browser automation | ✅ Complete | `ai_pipeline/notebooklm.py` |
| Google URL discovery | ✅ Complete | `discovery/google_scraper.py` |
| DuckDuckGo URL discovery | ✅ Complete | `discovery/ddg_scraper.py` |
| Discovery routing | ✅ Complete | `crawler/discovery_router.py` |
| HTML extraction & cleaning | ✅ Complete | `extractors/`, `postprocess/` |
| Content chunking | ✅ Complete | `postprocess/chunker.py` |
| Prompt engineering (4 modules) | ✅ Complete | `prompt_modules/` |
| Multi-report orchestrator | ✅ Complete | `ai_pipeline/multi_report_orchestrator.py` |
| Discovery cache | ✅ Complete | `outputs/discovery/urls.json` |
| FastAPI server | ✅ Complete | `bridge.py` |
| React frontend | ✅ Complete | `frontend/` |

### Critical Gap
| Component | Status | Impact |
|-----------|--------|--------|
| `outputs/composer.py` | ❌ MISSING | **Pipeline fails at line 37 of run.py** |

### Missing Enhancements (from report)
| Component | ROI | Effort |
|-----------|-----|--------|
| Query templates (curriculum-aware) | 🔥 HIGH | Low |
| Curriculum config | 🔥 HIGH | Low |
| Retry handler | 🔥 HIGH | Low |
| NotebookLM prompts | 🔥 HIGH | Low |
| Robots checker | ⚡ MEDIUM-HIGH | Low |
| Checkpoint system | ⚡ MEDIUM-HIGH | Medium |
| Distractor validator | ⚡ MEDIUM | Medium |

---

## Mini-Phase Implementation Plan

### Phase 0: Critical Blocker Fix
**Goal**: Make pipeline runnable
**ETA**: Immediate

```
outputs/
├── __init__.py
└── composer.py       ← CREATE THIS
```

**`composer.py` Requirements:**
- Takes `ai_result` dict from AI pipeline
- Takes `output_type` (study_material, questionnaire, handout)
- Returns formatted output dict with:
  - `summary` - Main content
  - `metadata` - Source info, timestamps
  - `format` - Output type indicator

**Contract:**
```python
def compose_output(ai_result: dict, output_type: str) -> dict:
    """
    Compose final output from AI result.

    Args:
        ai_result: {"summary": str, "evidence": list, ...}
        output_type: "study_material" | "questionnaire" | "handout"

    Returns:
        {"summary": str, "metadata": dict, "format": str, "content": dict}
    """
```

---

### Phase 1A: NotebookLM Flow Validation
**Goal**: Confirm end-to-end NotebookLM discovery → report flow
**Depends on**: Phase 0

**Tasks:**
1. Test NotebookLM source discovery flow (`discovery_method=notebooklm`)
2. Test NotebookLM report generation with URL sources
3. Validate PDF export functionality
4. Document authentication requirements

**Test Commands:**
```bash
# Set env vars
export DISCOVERY_METHOD=notebooklm
export NOTEBOOKLM_AVAILABLE=true
export CR_TOPIC="Force and Pressure"
export CR_GRADE="Grade 8"

# Run pipeline
python run.py
```

---

### Phase 1B: URL Discovery Enhancement
**Goal**: Improve discovery quality with curriculum awareness
**Depends on**: Phase 0

**Files to Create:**
```
discovery/
├── query_templates.py    ← NEW
config/
├── curriculum.json       ← NEW
├── curriculum_loader.py  ← NEW
```

**`query_templates.py` Specification:**
```python
GRADE_8_SUBJECTS = {
    "math": {
        "topics": ["rational numbers", "linear equations", ...],
        "site_filters": ["khanacademy.org", "ncert.nic.in", "mathsisfun.com"]
    },
    "science": {
        "topics": ["crop production", "microorganisms", "force and pressure", ...],
        "site_filters": ["khanacademy.org", "byjus.com", "ncert.nic.in"]
    }
}

def build_search_query(topic: str, subject: str, grade: int, content_type: str) -> str:
    """Build optimized search query with site filters."""

def expand_topic_queries(topic: str, grade: int = 8) -> list[str]:
    """Generate multiple query variations for better coverage."""
```

**`curriculum.json` Schema:**
```json
{
  "standard": "CBSE",
  "grade": 8,
  "subjects": {
    "mathematics": {
      "chapters": [
        {"id": "math-1", "name": "Rational Numbers", "keywords": ["rational", "number line"]}
      ]
    },
    "science": {
      "chapters": [
        {"id": "sci-9", "name": "Force and Pressure", "keywords": ["force", "pressure", "friction"]}
      ]
    }
  }
}
```

**Integration Point** (`run.py` line 261-276):
```python
# BEFORE (generic query)
query = " ".join(query_parts).strip()

# AFTER (curriculum-aware)
from discovery.query_templates import expand_topic_queries
queries = expand_topic_queries(request.topic, grade=8)
# Run all queries, deduplicate URLs
```

---

### Phase 2A: Reliability - Retry Handler
**Goal**: Prevent pipeline failure on transient network errors
**Depends on**: Phase 0

**File to Create:**
```
reliability/
├── __init__.py
└── retry_handler.py     ← NEW
```

**Specification:**
```python
@retry_async(max_retries=3, exceptions=(aiohttp.ClientError, TimeoutError))
async def fetch_with_retry(url: str) -> str:
    """Fetch URL with exponential backoff (1s → 2s → 4s)."""
```

**Integration Points:**
- `crawler/navigation.py:fetch_page()`
- `discovery/google_scraper.py`
- `discovery/ddg_scraper.py`

---

### Phase 2B: Reliability - Robots Checker
**Goal**: Prevent IP bans from aggressive crawling
**Depends on**: Phase 2A

**File to Create:**
```
discovery/
└── robots_checker.py    ← NEW
```

**Specification:**
```python
def can_fetch(url: str, user_agent: str = "EducationalBot/1.0") -> bool:
    """Check robots.txt before fetching."""

def get_safe_delay(url: str) -> float:
    """Get recommended delay between requests (default 1.0s)."""
```

**Integration Point** (`run.py:collect_chunks_from_url()`):
```python
from discovery.robots_checker import can_fetch, get_safe_delay

if not can_fetch(url):
    logger.warning(f"Blocked by robots.txt: {url}")
    continue

await asyncio.sleep(get_safe_delay(url))
```

---

### Phase 2C: Reliability - Checkpoint System
**Goal**: Resume pipeline after failures without losing work
**Depends on**: Phase 2A

**File to Create:**
```
reliability/
└── checkpoint.py        ← NEW
```

**Specification:**
```python
class PipelineCheckpoint:
    def __init__(self, run_id: str): ...
    def save_stage(self, stage_name: str, data: Any): ...
    def has_stage(self, stage_name: str) -> bool: ...
    def load_stage(self, stage_name: str) -> Any: ...
    def get_resume_point(self) -> str | None: ...
```

**Checkpoint Stages:**
1. `discovery` - URLs found
2. `fetch` - Raw HTML saved
3. `chunk` - Chunks created
4. `ai` - AI results received
5. `compose` - Final output composed

**Integration Point** (`run.py`):
```python
from reliability.checkpoint import PipelineCheckpoint, generate_run_id

run_id = generate_run_id(request.topic)
checkpoint = PipelineCheckpoint(run_id)

# Before discovery
if checkpoint.has_stage("discovery"):
    urls = checkpoint.load_stage("discovery")["urls"]
else:
    urls = await discover_urls(...)
    checkpoint.save_stage("discovery", {"urls": urls})
```

---

### Phase 3A: NotebookLM Prompts Library
**Goal**: Consistent, versioned prompts for NotebookLM interactions
**Depends on**: Phase 1A

**File to Create:**
```
prompts/
└── notebooklm_prompts.py  ← NEW
```

**Prompt Types:**
| Type | Purpose |
|------|---------|
| `discovery` | Find relevant educational sources |
| `evidence_extraction` | Extract key facts from sources |
| `summary_generation` | Create study summary |
| `quiz_material` | Get quiz-ready content |

**Example:**
```python
NOTEBOOKLM_PROMPTS = {
    "discovery": {
        "version": "1.0.0",
        "template": """Find educational resources about "{topic}" suitable for Grade {grade} students.
Requirements:
- Focus on {subject} curriculum content
- Prefer explanations with examples
- Avoid content above Grade {grade_max} reading level"""
    }
}
```

---

### Phase 3B: Output Format Branching
**Goal**: Generate different output types (Quiz, Handout, Flashcards)
**Depends on**: Phase 0

**Enhance `outputs/composer.py`:**
```python
def compose_output(ai_result: dict, output_type: str) -> dict:
    if output_type == "questionnaire":
        return compose_quiz(ai_result)
    elif output_type == "handout":
        return compose_handout(ai_result)
    elif output_type == "study_material":
        return compose_study_guide(ai_result)
    elif output_type == "flashcards":
        return compose_flashcards(ai_result)
```

**Files to Create/Enhance:**
```
outputs/
├── composer.py           ← ENHANCE
├── quiz_composer.py      ← NEW
├── handout_composer.py   ← NEW
└── flashcard_composer.py ← NEW
```

---

### Phase 3C: Distractor Validator
**Goal**: Ensure quiz questions have quality distractors
**Depends on**: Phase 3B

**File to Create:**
```
outputs/
└── distractor_validator.py  ← NEW
```

**Specification:**
```python
def validate_mcq(question: dict) -> dict:
    """
    Returns: {"is_valid": bool, "issues": list, "suggestions": list}

    Checks:
    - Length similarity between correct answer and distractors
    - No "none of the above" lazy distractors
    - No duplicate distractors
    - Grammatical fit with question stem
    """
```

---

## Phase Dependency Graph

```
Phase 0 (composer.py)
    │
    ├──→ Phase 1A (NotebookLM validation)
    │         │
    │         └──→ Phase 3A (NotebookLM prompts)
    │
    ├──→ Phase 1B (Query templates + Curriculum config)
    │
    ├──→ Phase 2A (Retry handler)
    │         │
    │         ├──→ Phase 2B (Robots checker)
    │         │
    │         └──→ Phase 2C (Checkpoint system)
    │
    └──→ Phase 3B (Output format branching)
              │
              └──→ Phase 3C (Distractor validator)
```

---

## Execution Order (Recommended)

| Order | Phase | Description | Effort |
|-------|-------|-------------|--------|
| 1 | **Phase 0** | Create `outputs/composer.py` | 1-2 hours |
| 2 | **Phase 1A** | Validate NotebookLM flow | 2-3 hours |
| 3 | **Phase 2A** | Add retry handler | 1 hour |
| 4 | **Phase 1B** | Query templates + curriculum | 2-3 hours |
| 5 | **Phase 2B** | Robots checker | 1 hour |
| 6 | **Phase 3A** | NotebookLM prompts library | 1-2 hours |
| 7 | **Phase 2C** | Checkpoint system | 2-3 hours |
| 8 | **Phase 3B** | Output format branching | 2-3 hours |
| 9 | **Phase 3C** | Distractor validator | 2 hours |

**Total Estimated Effort**: ~15-20 hours

---

## File Structure After All Phases

```
NotebooklmCrawler/
├── config/
│   ├── curriculum.json           🆕 Phase 1B
│   └── curriculum_loader.py      🆕 Phase 1B
├── discovery/
│   ├── google_scraper.py         ✅ Existing
│   ├── ddg_scraper.py            ✅ Existing
│   ├── discovery_router.py       ✅ Existing
│   ├── query_templates.py        🆕 Phase 1B
│   └── robots_checker.py         🆕 Phase 2B
├── outputs/
│   ├── __init__.py               🆕 Phase 0
│   ├── composer.py               🆕 Phase 0
│   ├── quiz_composer.py          🆕 Phase 3B
│   ├── handout_composer.py       🆕 Phase 3B
│   ├── flashcard_composer.py     🆕 Phase 3B
│   └── distractor_validator.py   🆕 Phase 3C
├── prompts/
│   ├── templates.py              ✅ Existing
│   └── notebooklm_prompts.py     🆕 Phase 3A
├── reliability/
│   ├── __init__.py               🆕 Phase 2A
│   ├── retry_handler.py          🆕 Phase 2A
│   └── checkpoint.py             🆕 Phase 2C
└── ...
```

---

## Environment Variables (New)

```bash
# Educational Config (Phase 1B)
CURRICULUM_STANDARD=CBSE          # CBSE | ICSE | STATE | IB
TARGET_GRADE=8                    # Default grade level

# Quality Control (Phase 2B)
RESPECT_ROBOTS_TXT=true           # Enable robots.txt checking
CRAWL_DELAY_DEFAULT=1.0           # Seconds between requests

# Checkpoint (Phase 2C)
ENABLE_CHECKPOINTS=true           # Enable pipeline checkpointing
CHECKPOINT_DIR=./checkpoints      # Checkpoint storage location
```

---

## Success Criteria

### Phase 0 Complete When:
- [ ] `python run.py` executes without import error
- [ ] Output files created in `outputs/final/`

### Phase 1 Complete When:
- [ ] NotebookLM discovery flow works end-to-end
- [ ] Curriculum-aware queries return higher quality results
- [ ] Educational domain prioritization visible in logs

### Phase 2 Complete When:
- [ ] Network errors retry automatically (visible in logs)
- [ ] Blocked URLs skip gracefully
- [ ] Pipeline resumable after crash

### Phase 3 Complete When:
- [ ] Multiple output formats generated correctly
- [ ] Quiz questions pass validation
- [ ] NotebookLM uses versioned prompts

---

## Quick Start (After Phase 0)

```bash
# 1. Set environment
export DISCOVERY_METHOD=ddg
export NOTEBOOKLM_AVAILABLE=true
export CR_TOPIC="Force and Pressure"
export CR_GRADE="Grade 8"
export CR_OUTPUT_TYPE="study_material"

# 2. Run pipeline
python run.py

# 3. Check outputs
ls outputs/final/
cat outputs/final/result_000.json
```

---

## Reasoning & Code Practices Per Phase

> **Purpose**: This section provides guardrails to prevent AI coding drift. Each phase includes WHY we're doing it, WHAT patterns to follow, and WHAT to avoid.

---

### Phase 0: Composer Module

#### Why This Phase Exists
The pipeline is **completely broken** without `outputs/composer.py`. Line 37 of `run.py` imports it, and line 306 calls `compose_output()`. This is not a nice-to-have—it's a blocker.

#### Design Reasoning
- **Single Responsibility**: Composer ONLY transforms AI output → final output. It does NOT call AI, fetch URLs, or do validation.
- **Loose Coupling**: Composer should work regardless of whether AI result came from NotebookLM or DeepSeek.
- **Forward Compatibility**: Design for multiple output types from day one, even if we only implement one initially.

#### Code Practices

```python
# ✅ DO: Use type hints and validate input
def compose_output(ai_result: dict, output_type: str) -> dict:
    if not isinstance(ai_result, dict):
        raise TypeError(f"Expected dict, got {type(ai_result)}")

    # Validate required keys exist
    if "summary" not in ai_result and "evidence" not in ai_result:
        raise ValueError("ai_result must contain 'summary' or 'evidence'")

# ✅ DO: Return consistent structure regardless of output_type
return {
    "summary": ...,
    "metadata": {"timestamp": ..., "output_type": ...},
    "format": output_type,
    "content": {...}  # Type-specific content
}

# ❌ DON'T: Add AI calls, network requests, or file I/O here
# ❌ DON'T: Import from ai_pipeline, crawler, or discovery modules
# ❌ DON'T: Hard-code HTML templates (use templates/ directory)
```

#### Anti-Patterns to Avoid
| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| Calling AI inside composer | Violates single responsibility | Composer receives finished AI result |
| Catching all exceptions silently | Hides bugs, makes debugging hard | Let exceptions propagate with context |
| Returning different structures per type | Breaks downstream consumers | Always return same top-level keys |

---

### Phase 1A: NotebookLM Flow Validation

#### Why This Phase Exists
NotebookLM browser automation is complex (846 lines in `notebooklm.py`). Before adding features, we must **confirm the existing flow works end-to-end**. This prevents building on a broken foundation.

#### Design Reasoning
- **Test Before Extend**: Don't add prompts library until base flow is verified.
- **Manual Auth is OK**: NotebookLM requires Google login. Don't try to automate OAuth—it's fragile and against ToS.
- **Isolate Failures**: If discovery works but report fails, we need to know which.

#### Code Practices

```python
# ✅ DO: Add explicit stage logging
logger.info("STAGE: NotebookLM source discovery started")
# ... discovery code ...
logger.info("STAGE: NotebookLM source discovery completed with {n} sources")

# ✅ DO: Validate NotebookLM availability before attempting
if not os.getenv("NOTEBOOKLM_AVAILABLE", "").lower() == "true":
    raise RuntimeError("NotebookLM not available. Set NOTEBOOKLM_AVAILABLE=true")

# ✅ DO: Capture screenshots on failure for debugging
try:
    await page.click(selector)
except Exception as e:
    await page.screenshot(path=f"debug/failure_{timestamp}.png")
    raise

# ❌ DON'T: Add new features during validation
# ❌ DON'T: Change existing DOM selectors without testing
# ❌ DON'T: Skip the 5-minute auth wait—users need time to log in
```

#### Validation Checklist
```markdown
- [ ] Browser launches and navigates to NotebookLM
- [ ] Auth wait allows manual Google login
- [ ] New notebook created successfully
- [ ] Source added via "Website URL" option
- [ ] Source added via "Search the web" option
- [ ] Report generation completes (not times out)
- [ ] PDF exports to outputs/ directory
```

---

### Phase 1B: Query Templates & Curriculum Config

#### Why This Phase Exists
Generic searches like "Grade 8 force pressure" return garbage. Educational sites (Khan Academy, NCERT) have specific content structures. **Curriculum-aware queries dramatically improve content relevance.**

#### Design Reasoning
- **Separate Data from Logic**: Put curriculum data in JSON, query building in Python.
- **Extensible by Design**: Adding ICSE or State Board should require only JSON changes.
- **Site Filters as Hints**: Use `site:` operator, but don't fail if no results.

#### Code Practices

```python
# ✅ DO: Keep curriculum data in JSON (not Python dicts)
# config/curriculum.json - editable by non-programmers
{
  "standard": "CBSE",
  "subjects": {...}
}

# ✅ DO: Make topic matching fuzzy (handle variations)
def match_chapter(topic: str, curriculum: dict) -> dict | None:
    topic_words = set(topic.lower().split())
    for chapter in chapters:
        if topic_words & set(chapter["keywords"]):  # Set intersection
            return chapter
    return None  # Don't raise—caller decides fallback

# ✅ DO: Generate multiple query variations
def expand_topic_queries(topic: str) -> list[str]:
    return [
        f"grade 8 {topic} explanation site:khanacademy.org",
        f"NCERT class 8 {topic}",
        f"{topic} simple explanation for students",
    ]
    # Run all, deduplicate URLs by domain+path

# ❌ DON'T: Hard-code subjects in Python—use config file
# ❌ DON'T: Require exact topic match—use fuzzy matching
# ❌ DON'T: Fail if curriculum.json missing—fall back to generic
```

#### File Organization
```
config/
├── curriculum.json       # DATA: chapters, keywords, site filters
└── curriculum_loader.py  # LOGIC: load, match, validate

discovery/
└── query_templates.py    # LOGIC: query building only
```

---

### Phase 2A: Retry Handler

#### Why This Phase Exists
Network calls fail. Servers timeout. Without retry, **one flaky request kills the entire pipeline**. This is table-stakes reliability.

#### Design Reasoning
- **Decorator Pattern**: Wrap existing functions without modifying them.
- **Exponential Backoff**: 1s → 2s → 4s prevents thundering herd.
- **Jitter**: Random delay prevents synchronized retries across parallel requests.

#### Code Practices

```python
# ✅ DO: Use decorator pattern for clean integration
@retry_async(max_retries=3, exceptions=(TimeoutError, ConnectionError))
async def fetch_page(page, url: str) -> str:
    return await page.content()

# ✅ DO: Add jitter to prevent synchronized retries
delay = base_delay * (2 ** attempt)  # Exponential
jitter = delay * 0.5 * random.random()  # 0-50% randomness
await asyncio.sleep(delay + jitter)

# ✅ DO: Log retries with context
logger.warning(f"Retry {attempt}/{max_retries} for {url}: {error}")

# ✅ DO: Re-raise after exhausting retries (don't swallow)
if attempt == max_retries:
    raise last_exception

# ❌ DON'T: Retry indefinitely—cap at 3-5 attempts
# ❌ DON'T: Retry non-transient errors (404, 403)
# ❌ DON'T: Use fixed delays—always use backoff
```

#### What TO Retry vs NOT Retry
| Retry | Don't Retry |
|-------|-------------|
| TimeoutError | 404 Not Found |
| ConnectionError | 403 Forbidden |
| 5xx Server Errors | 400 Bad Request |
| DNS resolution failures | Authentication errors |

---

### Phase 2B: Robots Checker

#### Why This Phase Exists
Aggressive crawling gets IPs banned. Educational sites like NCERT and Khan Academy have rate limits. **Respecting robots.txt is both ethical and practical.**

#### Design Reasoning
- **Cache Per Domain**: Don't re-fetch robots.txt for every URL.
- **Fail Open**: If robots.txt unreachable, assume allowed (but log warning).
- **Conservative Defaults**: 1 second delay minimum, even if robots.txt says 0.

#### Code Practices

```python
# ✅ DO: Cache robots.txt per domain
@lru_cache(maxsize=100)
def get_robot_parser(domain: str) -> RobotFileParser | None:
    ...

# ✅ DO: Fail open with warning
def can_fetch(url: str) -> bool:
    try:
        rp = get_robot_parser(domain)
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        logger.warning(f"Could not check robots.txt for {domain}, assuming allowed")
        return True

# ✅ DO: Enforce minimum delay even for "friendly" sites
MINIMUM_DELAY = 1.0  # Never go below 1 second
def get_safe_delay(url: str) -> float:
    robots_delay = get_crawl_delay(domain)
    return max(MINIMUM_DELAY, robots_delay)

# ❌ DON'T: Ignore robots.txt—it gets you banned
# ❌ DON'T: Cache indefinitely—TTL of 1 hour is reasonable
# ❌ DON'T: Crash if robots.txt is malformed
```

#### Integration Pattern
```python
# In run.py collection loop
for url in urls:
    if not can_fetch(url):
        logger.warning(f"Skipping {url} (blocked by robots.txt)")
        continue

    await asyncio.sleep(get_safe_delay(url))
    chunks = await collect_chunks_from_url(...)
```

---

### Phase 2C: Checkpoint System

#### Why This Phase Exists
Pipeline runs can take 10-20 minutes. If it crashes at minute 18, you lose everything. **Checkpoints enable resume from last successful stage.**

#### Design Reasoning
- **Stage-Based**: Save after each major stage (discovery, fetch, chunk, ai, compose).
- **File-Based**: Simple JSON files. No database needed for this scale.
- **Idempotent Stages**: Re-running a stage with same input produces same output.

#### Code Practices

```python
# ✅ DO: Use unique run IDs for each pipeline execution
def generate_run_id(topic: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    topic_hash = hashlib.md5(topic.encode()).hexdigest()[:6]
    return f"{topic_hash}_{timestamp}"

# ✅ DO: Check for existing checkpoint before each stage
if checkpoint.has_stage("discovery"):
    logger.info("Resuming from discovery checkpoint")
    urls = checkpoint.load_stage("discovery")["urls"]
else:
    urls = await discover_urls(...)
    checkpoint.save_stage("discovery", {"urls": urls})

# ✅ DO: Include metadata in checkpoints for debugging
checkpoint.save_stage("fetch", {
    "urls": urls,
    "fetched_at": datetime.now().isoformat(),
    "success_count": len(successful),
    "failed_urls": failed_urls
})

# ❌ DON'T: Store large binary data in checkpoints (store file paths)
# ❌ DON'T: Rely on checkpoint for critical data (also save to outputs/)
# ❌ DON'T: Keep checkpoints forever—clean up after 7 days
```

#### Stage Ordering Contract
```python
STAGE_ORDER = ["discovery", "fetch", "chunk", "quality", "ai", "compose"]

# Resume always starts from NEXT uncompleted stage
def get_resume_stage(checkpoint) -> str:
    for stage in STAGE_ORDER:
        if not checkpoint.has_stage(stage):
            return stage
    return "complete"
```

---

### Phase 3A: NotebookLM Prompts Library

#### Why This Phase Exists
NotebookLM interactions need consistent, versioned prompts. Ad-hoc prompt strings scattered across code lead to **inconsistent behavior and hard-to-debug issues.**

#### Design Reasoning
- **Version Prompts**: When prompt changes, version increments. Logs show which version was used.
- **Template Variables**: Use `{topic}`, `{grade}` placeholders, not f-strings with code.
- **Separate by Intent**: Discovery prompt ≠ Evidence extraction prompt ≠ Summary prompt.

#### Code Practices

```python
# ✅ DO: Version every prompt
NOTEBOOKLM_PROMPTS = {
    "discovery": {
        "version": "1.0.0",
        "template": "...",
        "required_vars": ["topic", "grade", "subject"]
    }
}

# ✅ DO: Validate required variables before rendering
def get_prompt(prompt_type: str, **kwargs) -> tuple[str, str]:
    prompt_info = NOTEBOOKLM_PROMPTS[prompt_type]

    missing = set(prompt_info["required_vars"]) - set(kwargs.keys())
    if missing:
        raise ValueError(f"Missing required vars: {missing}")

    rendered = prompt_info["template"].format(**kwargs)
    return rendered, prompt_info["version"]

# ✅ DO: Log prompt version with every NotebookLM interaction
prompt, version = get_prompt("discovery", topic="Force", grade=8)
logger.info(f"Using prompt 'discovery' v{version}")

# ❌ DON'T: Hard-code prompts in notebooklm.py
# ❌ DON'T: Use f-strings for prompts (use .format() for explicit vars)
# ❌ DON'T: Change prompt without incrementing version
```

---

### Phase 3B: Output Format Branching

#### Why This Phase Exists
Users need Quiz, Handout, Flashcards—not just study guides. **One AI result should transform into multiple output formats.**

#### Design Reasoning
- **Composer Dispatches, Sub-Composers Transform**: Main composer routes to type-specific composers.
- **Shared Utilities**: All composers use same metadata builder, timestamp formatter, etc.
- **Graceful Degradation**: If specific composer fails, fall back to generic format.

#### Code Practices

```python
# ✅ DO: Use registry pattern for extensibility
COMPOSERS = {
    "questionnaire": compose_quiz,
    "handout": compose_handout,
    "study_material": compose_study_guide,
    "flashcards": compose_flashcards,
}

def compose_output(ai_result: dict, output_type: str) -> dict:
    composer_fn = COMPOSERS.get(output_type)
    if not composer_fn:
        logger.warning(f"Unknown output_type '{output_type}', using generic")
        composer_fn = compose_generic
    return composer_fn(ai_result)

# ✅ DO: Keep sub-composers focused and small
# outputs/quiz_composer.py
def compose_quiz(ai_result: dict) -> dict:
    """Transform AI result into quiz format."""
    # ONLY quiz-specific logic here

# ✅ DO: Share utilities across composers
# outputs/utils.py
def build_metadata(output_type: str) -> dict:
    return {"timestamp": datetime.now().isoformat(), "type": output_type}

# ❌ DON'T: Put all composers in one file (hard to maintain)
# ❌ DON'T: Duplicate metadata/timestamp logic across composers
# ❌ DON'T: Crash on unknown output_type—use fallback
```

---

### Phase 3C: Distractor Validator

#### Why This Phase Exists
Bad MCQ distractors make quizzes useless. "All of the above" is lazy. Similar-length distractors prevent guessing by elimination. **Validation catches quality issues before output.**

#### Design Reasoning
- **Rule-Based First**: Simple rules catch 80% of issues without AI.
- **Suggest, Don't Auto-Fix**: Flag problems for human review or LLM regeneration.
- **Log Everything**: Quality metrics help improve quiz generation prompts.

#### Code Practices

```python
# ✅ DO: Return structured validation result
def validate_mcq(question: dict) -> dict:
    return {
        "is_valid": len(issues) == 0,
        "issues": ["Length mismatch: option A too short", ...],
        "suggestions": ["Consider varying correct answer position"],
        "scores": {"length_balance": 0.8, "no_lazy_options": 1.0}
    }

# ✅ DO: Make rules explicit and testable
VALIDATION_RULES = [
    {
        "id": "length_match",
        "check": lambda q: all(0.5 <= len(d)/len(correct) <= 2.0 for d in distractors),
        "message": "Distractors should be similar length to correct answer"
    },
    ...
]

# ✅ DO: Flag for review, don't silently fix
if not validation["is_valid"]:
    question["_needs_review"] = True
    question["_validation_issues"] = validation["issues"]

# ❌ DON'T: Auto-fix distractors (you might make them worse)
# ❌ DON'T: Block output on validation failure (warn and continue)
# ❌ DON'T: Hard-code lazy patterns—make them configurable
```

#### Validation Flow
```
MCQ Generated → validate_mcq() → is_valid?
                                    ├── Yes → Include in output
                                    └── No → Flag for review + include anyway
```

---

## General Code Practices (All Phases)

### Logging Standards
```python
# ✅ DO: Use structured logging with context
logger.info("Processing URL", extra={"url": url, "index": i, "total": len(urls)})

# ✅ DO: Log stage boundaries clearly
logger.info("=" * 50)
logger.info("STAGE: Discovery Started")
logger.info("=" * 50)

# ❌ DON'T: Log sensitive data (API keys, auth tokens)
# ❌ DON'T: Use print() instead of logger
```

### Error Handling
```python
# ✅ DO: Add context when re-raising
try:
    result = await fetch(url)
except Exception as e:
    raise RuntimeError(f"Failed to fetch {url}") from e

# ✅ DO: Use specific exception types
class DiscoveryError(Exception): pass
class ComposerError(Exception): pass

# ❌ DON'T: Catch Exception silently
# ❌ DON'T: Return None on error (raise or return Result type)
```

### Import Organization
```python
# Standard library
import os
import json
from datetime import datetime

# Third-party
from pydantic import BaseModel

# Local - absolute imports only
from contracts.content_request import ContentRequest
from outputs.composer import compose_output

# ❌ DON'T: Use relative imports (from . import)
# ❌ DON'T: Import from parent directories (from .. import)
```

### Testing Requirements
```python
# Every new module needs:
# 1. Unit tests for pure functions
# 2. Integration test showing it works with real data
# 3. Edge case tests (empty input, None, malformed data)

# tests/test_composer.py
def test_compose_output_study_material():
    ai_result = {"summary": "Test content", "evidence": []}
    result = compose_output(ai_result, "study_material")
    assert "summary" in result
    assert result["format"] == "study_material"

def test_compose_output_unknown_type_uses_fallback():
    result = compose_output({...}, "unknown_type")
    assert result is not None  # Didn't crash
```

---

## Common Drift Patterns to Avoid

| Drift Pattern | Example | Why It's Bad | Correct Approach |
|---------------|---------|--------------|------------------|
| Scope creep | Adding caching while building composer | Delays completion, introduces bugs | Finish phase first, then enhance |
| Premature optimization | Using Redis before file cache is full | Adds complexity without benefit | Start simple, optimize when needed |
| Over-engineering | Abstract base class for one composer | More code to maintain | Just write the function |
| Copy-paste coding | Duplicating retry logic in each file | Hard to fix bugs, inconsistent | Use decorator/utility |
| Silent failures | `except: pass` | Bugs hide, debugging is impossible | Log and re-raise with context |
| Magic strings | `if output_type == "questionaire":` (typo) | Runtime errors, hard to find | Use enums or constants |

---

## Commit Message Format

```
<type>(<phase>): <description>

[optional body]

https://claude.ai/code/session_017s69HwQAKz9eMarHfP5Uyf
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code change that neither fixes nor adds
- `test` - Adding tests
- `docs` - Documentation only

**Examples:**
```
feat(phase-0): Add outputs/composer.py with study_material support

fix(phase-2a): Handle TimeoutError in retry decorator

refactor(phase-1b): Extract query building to separate module
```
