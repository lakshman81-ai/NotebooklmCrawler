# Intelligence Source: DIRECT Execution Path

*This is the "Precision Mode" where the user provides specific URLs, bypassing the discovery/search phase.*

## Logic Flow

1.  **Trigger**: User toggles "Web Search" **OFF** in the UI and enters URLs in the "Target URLs" field.
2.  **Validation**: Frontend ensures at least one URL is provided.
3.  **Direct Access**:
    *   The `run.py` script detects the `TARGET_URL` environment variable.
    *   It skips cache checks and scrapers.
    *   It immediately visits the provided URLs.
4.  **Synthesis**:
    *   Content is extracted and sent to the configured AI backend (NotebookLM or DeepSeek).

## Mermaid Diagram

```mermaid
graph TD
    Start([User Clicks Launch]) --> Input[Input: Target URLs]
    Input --> Validation{Are URLs Valid?}

    Validation -- Yes --> Fetch[Playwright: Visit URL]
    Fetch -- "Extract HTML" --> Cleaner[HTML Cleaner]
    Cleaner -- "Remove Ads/Nav" --> Content[Clean Text]

    Content --> Chunker[Split into Sections]
    Chunker --> AI_Router[AI Router]

    AI_Router --> Method{Config: NotebookLM?}

    %% Mode A
    Method -- Yes --> Upload[Upload to NotebookLM]
    Upload --> Evidence[Generate Evidence]
    Evidence --> DeepSeek[DeepSeek Synthesis]

    %% Mode B
    Method -- No --> LLM[DeepSeek Direct]

    DeepSeek --> Final[Final Report]
    LLM --> Final
```
