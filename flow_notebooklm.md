# Intelligence Source: NOTEBOOKLM Execution Path

*This path delegates the entire research process to Google's NotebookLM via browser automation. It relies on the internal search capabilities of NotebookLM.*

## Logic Flow

1.  **Trigger**: User selects "NOTEBOOKLM" in the UI and clicks Launch.
2.  **Gate**: The system checks if `NOTEBOOKLM_GUIDED` is OFF. If ON, it stops and asks for manual input.
3.  **Browser Action**:
    *   Navigates to `notebooklm.google.com`.
    *   Checks for login state.
    *   Creates a new notebook or selects an existing one.
4.  **Source Addition**:
    *   Selects "Add Source" -> "Web".
    *   Types the `Topic` + `Grade` into the search bar.
    *   Selects discovered sources and imports them.
5.  **Synthesis**:
    *   Uses a "Custom Report" prompt to generate the final PDF.

## Mermaid Diagram

```mermaid
graph TD
    Start([User Clicks Launch]) --> Input[Input: Topic + Grade]
    Input --> Logic{Is NotebookLM Selected?}
    Logic -- Yes --> Browser[Launch Browser]

    Browser -- "Navigate" --> Login{Is Logged In?}
    Login -- No --> Wait[Wait for User Login]
    Login -- Yes --> Search[Click 'Add Source' -> 'Web']

    Search -- "Type Topic" --> NotebookLM_UI[NotebookLM Interface]
    NotebookLM_UI -- "Find Sources" --> Select[Select All Sources]
    Select -- "Import" --> Process[Processing Sources...]

    Process --> Generate[Click 'Generate Report']
    Generate --> Output[Download PDF]
    Output --> End([Task Complete])
```
