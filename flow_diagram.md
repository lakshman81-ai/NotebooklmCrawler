# Intelligence Source Program Flow & Logic

## 1. System Architecture Diagram

This diagram visualizes how user actions, configuration settings, and backend logic interact to execute the Research Pipeline.

```mermaid
graph TD
    %% --- STYLE DEFINITIONS ---
    classDef ui fill:#eef2ff,stroke:#4f46e5,stroke-width:2px;
    classDef backend fill:#f0fdf4,stroke:#16a34a,stroke-width:2px;
    classDef config fill:#fffbeb,stroke:#d97706,stroke-width:2px,stroke-dasharray: 5 5;
    classDef logic fill:#f8fafc,stroke:#475569,stroke-width:1px;

    %% --- NODES ---

    subgraph Frontend_UI [Frontend Layer]
        User((User))
        ConfigTab[ConfigTab.jsx]:::ui
        AutoMode[AutoMode.jsx]:::ui
        GuidedPopup[GuidedModePopup]:::ui
    end

    subgraph Configuration_Store [Configuration State]
        EnvFile[.env File]:::config
        BrowserStorage[LocalStorage]:::config
    end

    subgraph Backend_Server [Backend Layer]
        Bridge[bridge.py]:::backend
        Orchestrator[run.py]:::backend
    end

    subgraph Execution_Logic [Intelligence Logic]
        AIRouter[ai_router.py]:::logic

        subgraph Drivers
            NotebookLM[notebooklm.py]:::logic
            DeepSeek[deepseek.py]:::logic
            Browser[Playwright Browser]:::logic
        end
    end

    %% --- FLOWS ---

    %% 1. Configuration Flow
    User -- "1. Sets API Keys & Modules" --> ConfigTab
    ConfigTab -- "POST /api/config/save" --> Bridge
    Bridge -- "Writes Variables" --> EnvFile
    ConfigTab -.-> |"Syncs State"| BrowserStorage

    %% 2. Execution Trigger Flow
    User -- "2. Clicks 'Research Pipeline'" --> AutoMode

    %% Decision Gate: GUIDED MODE
    EnvFile -.-> |"NOTEBOOKLM_GUIDED=true"| AutoMode
    AutoMode -- "Check Guided Mode" --> Gate_Guided{Is Guided Mode ON?}
    Gate_Guided -- Yes --> GuidedPopup
    GuidedPopup -- "Show Manual Prompts" --> User

    Gate_Guided -- No --> Payload[Construct JSON Payload]
    Payload -- "POST /api/auto/execute" --> Bridge

    %% 3. Backend Orchestration
    Bridge -- "Spawns Subprocess" --> Orchestrator
    EnvFile -.-> |"Loads Variables"| Orchestrator

    Orchestrator -- "Check Discovery Method" --> Gate_Method{Method?}

    %% BRANCH A: NOTEBOOKLM (Discovery)
    Gate_Method -- "NOTEBOOKLM" --> AIRouter
    AIRouter -- "Route: NotebookLM" --> NotebookLM
    NotebookLM -- "Automate UI" --> Browser
    Browser -- "Search & Generate" --> NotebookLM

    %% BRANCH B: AUTO / DIRECT
    Gate_Method -- "AUTO / DIRECT" --> UrlLogic[URL Collection]
    UrlLogic -- "Fetch & Chunk" --> Chunks[Content Chunks]
    Chunks --> AIRouter

    %% Decision Gate: AI BACKEND
    EnvFile -.-> |"NOTEBOOKLM_AVAILABLE=true"| AIRouter
    AIRouter -- "Check Available AI" --> Gate_AI{NotebookLM Available?}

    Gate_AI -- Yes --> NotebookLM
    NotebookLM -- "Upload Chunks" --> Browser
    Browser -- "Process Content" --> NotebookLM

    Gate_AI -- No --> DeepSeek
    DeepSeek -- "LLM Inference" --> FinalOutput[Final Output]

```

---

## 2. General Process Explanations

### **A. Intelligence Source: NOTEBOOKLM**
*   **What it does:** This source treats Google NotebookLM as an end-to-end research assistant. It uses the browser to "drive" the NotebookLM website, asking it to search the web for your topic.
*   **Detailed Flow:** See `flow_notebooklm.md`

### **B. Intelligence Source: AUTO (Web Search ON)**
*   **What it does:** This mode acts like a traditional search engine. It automatically finds relevant URLs for your topic, reads them, and then synthesizes the information.
*   **Detailed Flow:** See `flow_auto.md`

### **C. Intelligence Source: GOOGLE / DUCKDUCKGO (Explicit Search)**
*   **What it does:** Functionally similar to AUTO, but explicitly selects the search strategy. This path emphasizes the discovery phase.
*   **Detailed Flow:** See `flow_search.md`

### **D. Intelligence Source: DIRECT (Web Search OFF)**
*   **What it does:** This is the "Precision Mode". You give it specific URLs, and it analyzes exactly those pages—nothing else.
*   **Detailed Flow:** See `flow_direct.md`

---

## 3. Configuration Linkage: "Intelligence Modules" & "API Keys"

The settings in the **Config Tab** directly control the "Decision Gates" in the diagram above. Here is how they link:

### **A. "Intelligence Modules" (The Switches)**

1.  **Variable:** `NotebookLM Guided Mode`
    *   **In the Code:** `NOTEBOOKLM_GUIDED` (Environment Variable).
    *   **What it controls:** The **"User Interruption" Gate**.
    *   **Example:** If you switch this **ON**, clicking "Launch Pipeline" will **STOP** the automated process. Instead, a popup appears with prompts for you to copy-paste manually. The code effectively says: *"Stop! Do not run the backend. Show the user instructions instead."*

2.  **Variable:** `NotebookLM Available`
    *   **In the Code:** `NOTEBOOKLM_AVAILABLE` (Environment Variable).
    *   **What it controls:** The **"AI Router" Gate**.
    *   **Example:** You have collected 10 pages of text about "Volcanoes".
        *   **If ON:** The system thinks, *"I will upload these 10 pages to NotebookLM to get a summary."*
        *   **If OFF:** The system thinks, *"I cannot use NotebookLM. I will check if DeepSeek is available to summarize these pages instead."*

### **B. "API Keys" (The Credentials)**

1.  **Variable:** `DeepSeek API Key`
    *   **In the Code:** `DEEPSEEK_API_KEY` (Environment Variable).
    *   **What it controls:** Access to the **DeepSeek Driver**.
    *   **Example:** If the "AI Router" Gate decides to use DeepSeek (because NotebookLM is off or failed), the code looks for this key.
        *   **If Key Exists:** The system sends your text to DeepSeek's cloud for processing.
        *   **If Key Missing:** The process will fail with an authentication error.
