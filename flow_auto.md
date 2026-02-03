# Intelligence Source: AUTO Execution Path

*This path attempts to find resources automatically using search engines or a local discovery cache. It is the default "Research" mode.*

## Logic Flow

1.  **Trigger**: User selects "AUTO" (or leaves default) and ensures "Web Search" is ON.
2.  **Discovery**:
    *   System checks `outputs/discovery/urls.json` for cached URLs.
    *   **CRITICAL**: In the current version, the automated scraper is **disabled**.
    *   **If Cache Empty**: The process raises a `RuntimeError` and stops.
    *   **If Cache Found**: It proceeds to Collection.
3.  **Collection**:
    *   Found URLs are visited using Playwright.
    *   HTML is cleaned and split into text chunks.
4.  **AI Routing**:
    *   **Mode A (NotebookLM Available)**: Chunks are uploaded to NotebookLM -> Evidence generated -> Evidence sent to DeepSeek -> Final Report.
    *   **Mode B (NotebookLM Unavailable)**: Chunks are sent directly to DeepSeek -> Final Report.

## Mermaid Diagram

```mermaid
graph TD
    Start([User Clicks Launch]) --> Input[Input: Topic + Grade]
    Input --> Config{Web Search ON?}

    Config -- Yes --> Cache{Check Discovery Cache}
    Cache -- Found --> URLs[List of URLs]
    Cache -- Empty --> Error[RuntimeError: No URLs Found]

    URLs --> Fetch[Fetch HTML Content]
    Fetch --> Clean[Clean & Chunk Text]

    Clean --> AI_Gate{NotebookLM Available?}

    %% Mode A: Two-Stage
    AI_Gate -- Yes --> NBLM_Upload[Upload to NotebookLM]
    NBLM_Upload --> NBLM_Gen[NotebookLM Evidence]
    NBLM_Gen --> DeepSeek_A[DeepSeek Synthesis]

    %% Mode B: Fallback
    AI_Gate -- No --> DeepSeek_B[DeepSeek Direct Synthesis]

    DeepSeek_A --> End([Task Complete])
    DeepSeek_B --> End
```
