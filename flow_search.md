# Intelligence Source: GOOGLE / DUCKDUCKGO Execution Path

*Functionally similar to AUTO, but explicitly selects the search strategy.*

## Logic Flow

1.  **Trigger**: User explicitly selects "GOOGLE" or "DUCKDUCKGO" in the UI.
2.  **Strategy Selection**: The backend receives the specific source type (e.g., "trusted" vs "general").
3.  **Discovery (Current Constraints)**:
    *   Like the AUTO path, `run.py` currently relies on **Cached URLs** or **Manual Override**.
    *   It does **not** actively trigger a scraper in this version.
    *   If no cache exists, it fails.
4.  **Processing**:
    *   Valid URLs are passed to the standard Fetch -> Chunk -> AI Router pipeline.

## Mermaid Diagram

```mermaid
graph TD
    Start([User Clicks Launch]) --> Input[Input: Topic + Keywords]
    Input --> Strategy[Strategy: Search Engine]

    Strategy --> Check[Check Cache / Env URLs]
    Check -- Empty --> Error[RuntimeError: Scraper Disabled]
    Check -- Found --> URLs[Valid URLs]

    URLs --> Fetch[Fetch Page Content]
    Fetch --> Clean[Clean & Chunk Text]

    Clean --> Router[AI Router (NotebookLM / DeepSeek)]
    Router --> Output[Synthesis]
```
