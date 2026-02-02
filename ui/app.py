import streamlit as st
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment
load_dotenv()
ENV_PATH = Path(".env")

st.set_page_config(page_title="Orchestration Cockpit", layout="wide")
st.title("Orchestration Cockpit")

# Tabs
tab_dashboard, tab_artifacts, tab_settings = st.tabs(["🚀 Dashboard", "📂 Artifacts", "⚙️ Settings"])

# --- SETTINGS TAB ---
with tab_settings:
    st.header("Pipeline Configuration")

    with st.form("settings_form"):
        col1, col2 = st.columns(2)

        with col1:
            target_url = st.text_input("Target URL", value=os.getenv("TARGET_URL", ""))
            max_tokens = st.number_input("Max Tokens", value=int(os.getenv("MAX_TOKENS", 1200)))
            grade = st.text_input("Grade", value=os.getenv("CR_GRADE", "Grade 8"))
            topic = st.text_input("Topic", value=os.getenv("CR_TOPIC", "Exponents"))

        with col2:
            headless_val = os.getenv("HEADLESS", "false").lower() == "true"
            headless = st.checkbox("Headless Mode", value=headless_val)

            current_strategy = os.getenv("CHUNKING_STRATEGY", "section_aware")
            strategy_index = 0
            if current_strategy == "fixed_size":
                strategy_index = 1
            strategy = st.selectbox("Chunking Strategy", ["section_aware", "fixed_size"], index=strategy_index)

            # Content Request Settings
            output_type_val = os.getenv("CR_OUTPUT_TYPE", "study_material")
            output_opts = ["study_material", "questionnaire", "handout"]
            output_idx = output_opts.index(output_type_val) if output_type_val in output_opts else 0
            output_type = st.selectbox("Output Type", output_opts, index=output_idx)

            source_type_val = os.getenv("CR_SOURCE_TYPE", "trusted")
            source_opts = ["trusted", "general"]
            source_idx = source_opts.index(source_type_val) if source_type_val in source_opts else 0
            source_type = st.selectbox("Source Type", source_opts, index=source_idx)

        subtopics = st.text_input("Subtopics (comma-separated)", value=os.getenv("CR_SUBTOPICS", "laws,zero exponent"))

        st.subheader("Domain Management")
        col3, col4 = st.columns(2)
        with col3:
            default_trusted = "byjus.com, vedantu.com, khanacademy.org"
            trusted_domains = st.text_area(
                "Trusted Domains (comma-separated)",
                value=os.getenv("TRUSTED_DOMAINS", default_trusted),
                help="Domains used when Source Type is 'trusted'."
            )

        with col4:
            default_blocked = "duckduckgo.com, youtube.com, facebook.com, twitter.com, instagram.com, pinterest.com, linkedin.com, amazon.com"
            blocked_domains = st.text_area(
                "Blocked Domains (comma-separated)",
                value=os.getenv("BLOCKED_DOMAINS", default_blocked),
                help="Domains excluded from search results."
            )

        st.info("Technical settings are grouped here to keep the dashboard clean.")

        if st.form_submit_button("Save Configuration"):
            # Update .env file manually to be safe or use set_key
            # We'll try set_key, if it fails (not installed), we fallback?
            # But requirements.txt has python-dotenv.
            try:
                if not ENV_PATH.exists():
                    ENV_PATH.touch()

                # set_key might return (success, key, value) or bool
                set_key(ENV_PATH, "TARGET_URL", target_url)
                set_key(ENV_PATH, "MAX_TOKENS", str(max_tokens))
                set_key(ENV_PATH, "HEADLESS", str(headless).lower())
                set_key(ENV_PATH, "CHUNKING_STRATEGY", strategy)
                set_key(ENV_PATH, "CR_GRADE", grade)
                set_key(ENV_PATH, "CR_TOPIC", topic)
                set_key(ENV_PATH, "CR_SUBTOPICS", subtopics)
                set_key(ENV_PATH, "CR_OUTPUT_TYPE", output_type)
                set_key(ENV_PATH, "CR_SOURCE_TYPE", source_type)
                set_key(ENV_PATH, "TRUSTED_DOMAINS", trusted_domains)
                set_key(ENV_PATH, "BLOCKED_DOMAINS", blocked_domains)

                st.success("Settings saved! Configuration updated.")

                # Update current session env
                os.environ["TARGET_URL"] = target_url
                os.environ["MAX_TOKENS"] = str(max_tokens)
                os.environ["HEADLESS"] = str(headless).lower()
                os.environ["CHUNKING_STRATEGY"] = strategy
                os.environ["CR_GRADE"] = grade
                os.environ["CR_TOPIC"] = topic
                os.environ["CR_SUBTOPICS"] = subtopics
                os.environ["CR_OUTPUT_TYPE"] = output_type
                os.environ["CR_SOURCE_TYPE"] = source_type
                os.environ["TRUSTED_DOMAINS"] = trusted_domains
                os.environ["BLOCKED_DOMAINS"] = blocked_domains

            except Exception as e:
                st.error(f"Failed to save settings: {e}")

# --- DASHBOARD TAB ---
with tab_dashboard:
    st.header("Mission Control")

    col_action, col_log = st.columns([1, 3])

    with col_action:
        st.write("Ready to launch?")
        if st.button("▶️ Run Pipeline", type="primary"):
            with st.spinner("Pipeline running..."):
                # Run run.py as subprocess
                try:
                    # We pass the current env to the subprocess
                    env = os.environ.copy()
                    result = subprocess.run(
                        [sys.executable, "run.py"],
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd(),
                        env=env
                    )

                    if result.returncode == 0:
                        st.success("Pipeline completed successfully!")
                    else:
                        st.error("Pipeline failed!")
                        st.expander("Show Error Details").code(result.stderr)

                except Exception as e:
                    st.error(f"Execution failed: {e}")

    with col_log:
        st.subheader("Live Telemetry")
        log_file = Path("logs/app.log")
        if log_file.exists():
            # Tail last 50 lines
            with open(log_file, "r") as f:
                lines = f.readlines()
                last_lines = lines[-50:]
            st.code("".join(last_lines), language="text")

            if st.button("Refresh Logs"):
                st.rerun()
        else:
            st.info("No logs found yet.")

# --- ARTIFACTS TAB ---
with tab_artifacts:
    st.header("Artifact Inspector")

    base_dir = Path("outputs")

    artifact_type = st.selectbox("Artifact Type", ["Final Results (JSON/TXT)", "Cleaned HTML", "Raw HTML"])

    target_dir = None
    if artifact_type == "Final Results (JSON/TXT)":
        target_dir = base_dir / "final"
    elif artifact_type == "Cleaned HTML":
        target_dir = base_dir / "html/cleaned"
    else:
        target_dir = base_dir / "html/raw"

    if target_dir and target_dir.exists():
        files = sorted(list(target_dir.glob("*")))
        if files:
            selected_file = st.selectbox("Select File", files, format_func=lambda x: x.name)

            if selected_file:
                st.subheader(f"Viewing: {selected_file.name}")
                content = selected_file.read_text(encoding="utf-8", errors="replace")

                if selected_file.suffix == ".json":
                    st.json(content)
                elif selected_file.suffix == ".html":
                    st.components.v1.html(content, height=600, scrolling=True)
                    with st.expander("View Source"):
                        st.code(content, language="html")
                else:
                    st.text(content)
        else:
            st.info("No artifacts found in this category.")
    else:
        st.warning(f"Directory {target_dir} does not exist yet.")
