from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
import sys
import os
import json
import asyncio
import io
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import set_key
import pandas as pd
from discovery.edu_search_pipeline import EduSearchPipeline

app = FastAPI()

class DiscoveryRequest(BaseModel):
    grade: str
    subject: str
    topic: str
    subtopics: Optional[str] = None
    maxResults: Optional[int] = 10
    region: Optional[str] = "us-en"
    trustedDomains: Optional[str] = None
    blockedDomains: Optional[str] = None

class ConfigSaveRequest(BaseModel):
    maxTokens: int
    strategy: str
    outputType: str
    headless: bool
    chromeUserDataDir: Optional[str] = None
    discoveryMethod: Optional[str] = None
    notebooklmAvailable: Optional[bool] = None
    deepseekAvailable: Optional[bool] = None
    notebooklmGuided: Optional[bool] = None
    trustedDomains: Optional[str] = None
    blockedDomains: Optional[str] = None

class AdminSaveRequest(BaseModel):
    deepseek: str
    gemini: str
    notebooklm: str

class TemplateFileRequest(BaseModel):
    filepath: str  # Relative path like "Harshitha/biology.xlsx"

# Enable CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"

class ExecutionRequest(BaseModel):
    targetUrl: str
    grade: str
    topic: str
    subtopics: str
    materialType: str
    customPrompt: Optional[str] = ""
    sourceType: str
    config: dict

@app.post("/api/auto/execute")
async def execute_pipeline(req: ExecutionRequest):
    try:
        # 1. Update .env or OS surroundings
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        
        # Mapping UI fields to Pipeline ENV
        # Robustly handle sourceType if it comes as "Web Content" or "Trusted Handlers"
        st_raw = req.sourceType.lower()
        if "web" in st_raw or "general" in st_raw:
            source_type = "general"
        else:
            source_type = "trusted"

        env_map = {
            "TARGET_URL": req.targetUrl,
            "CR_GRADE": req.grade,
            "CR_TOPIC": req.topic,
            "CR_SUBTOPICS": req.subtopics,
            "CR_OUTPUT_TYPE": req.materialType,
            "CR_SOURCE_TYPE": source_type,
            "HEADLESS": str(req.config.get("headless", False)).lower(),
            "MAX_TOKENS": str(req.config.get("maxTokens", 1200)),
            "CHUNKING_STRATEGY": req.config.get("strategy", "section_aware"),
            "NOTEBOOKLM_AVAILABLE": str(req.config.get("modes", {}).get("D", True)).lower(),
            "DISCOVERY_METHOD": req.config.get("discoveryMethod", "Auto").lower(),
            "CR_CUSTOM_PROMPT": req.customPrompt or "",
            "CR_DIFFICULTY": req.config.get("difficulty", "Medium"),
            "CR_KEYWORDS_REPORT": req.config.get("keywordsReport", ""),
            "CR_OUTPUT_CONFIG": json.dumps(req.config.get("outputs", {})),
            "CR_LOCAL_FILE_PATH": req.config.get("localFilePath", ""),
            "CR_QUIZ_CONFIG": json.dumps(req.config.get("quizConfig", {}))
        }

        for key, value in env_map.items():
            set_key(str(ENV_PATH), key, value)
            os.environ[key] = value

        # 2. Run run.py as a subprocess
        # Kill any existing run.py processes to avoid browser lock conflicts
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq Orchestrator:*"], capture_output=True)
        
        # We'll set a custom title if possible, or just rely on the fact that only one mission should run.
        # Redirect logs to a dedicated pipeline log file for observability
        log_dir = PROJECT_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        pipeline_log = open(log_dir / "pipeline.log", "w") # Overwrite to keep logs fresh for current run

        process = await asyncio.create_subprocess_exec(
            sys.executable, "run.py",
            stdout=pipeline_log,
            stderr=pipeline_log,
            cwd=str(PROJECT_ROOT)
        )

        # Return success immediately to let UI show 'RUNNING'
        return {
            "success": True,
            "snapshotId": f"snpt_{int(asyncio.get_event_loop().time())}",
            "message": "Pipeline initiated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(since: Optional[str] = None):
    log_file = PROJECT_ROOT / "logs" / "app.log"
    pipeline_log = PROJECT_ROOT / "logs" / "pipeline.log"

    logs = []
    status_found = "IDLE"

    # 1. Determine Status from pipeline.log (legacy/robust)
    if pipeline_log.exists():
        try:
            with open(pipeline_log, "r") as f:
                lines = f.readlines()
                last_100_raw = lines[-100:]
                content_lower = "".join(last_100_raw).lower()
                
                if "mission complete" in content_lower or "saved outputs to" in content_lower:
                    status_found = "COMPLETED"
                elif any(kw in content_lower for kw in ["failed", "runtimeerror", "traceback", "timeout 15000ms", "error"]):
                    status_found = "FAILED"
                elif len(lines) > 0:
                    status_found = "RUNNING"
        except Exception:
            pass

    # 2. Read Structured Logs
    if log_file.exists():
        try:
            with open(log_file, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        entry = json.loads(line)
                        if since:
                            if entry.get("timestamp") > since:
                                logs.append(entry)
                        else:
                            logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading app.log: {e}")
            pass

    # Sort logs by timestamp
    logs.sort(key=lambda x: x.get("timestamp", ""))

    # Limit if no sync provided (initial load)
    if not since and len(logs) > 200:
        logs = logs[-200:]

    return {
        "logs": logs,
        "status": status_found
    }

@app.get("/api/config/load")
async def load_config():
    """Load all configuration values from .env file"""
    from dotenv import dotenv_values
    try:
        config = dotenv_values(str(ENV_PATH)) if ENV_PATH.exists() else {}
        return {
            "maxTokens": int(config.get("MAX_TOKENS", 2000)),
            "strategy": config.get("CHUNKING_STRATEGY", "section_aware"),
            "outputType": config.get("CR_OUTPUT_TYPE", "mixed_outputs"),
            "headless": config.get("HEADLESS", "false").lower() == "true",
            "chromeUserDataDir": config.get("CHROME_USER_DATA_DIR", ""),
            "discoveryMethod": config.get("DISCOVERY_METHOD", "notebooklm"),
            "notebooklmAvailable": config.get("NOTEBOOKLM_AVAILABLE", "true").lower() == "true",
            "deepseekAvailable": config.get("DEEPSEEK_AVAILABLE", "false").lower() == "true",
            "notebooklmGuided": config.get("NOTEBOOKLM_GUIDED", "false").lower() == "true",
            "trustedDomains": config.get("TRUSTED_DOMAINS", "byjus.com, vedantu.com, khanacademy.org"),
            "blockedDomains": config.get("BLOCKED_DOMAINS", "duckduckgo.com, youtube.com, facebook.com, twitter.com, instagram.com, pinterest.com, linkedin.com, amazon.com"),
            "targetUrl": config.get("TARGET_URL", ""),
            "grade": config.get("CR_GRADE", "General"),
            "topic": config.get("CR_TOPIC", "Analysis"),
            "subtopics": config.get("CR_SUBTOPICS", ""),
            "sourceType": config.get("CR_SOURCE_TYPE", "trusted"),
            "customPrompt": config.get("CR_CUSTOM_PROMPT", ""),
            "difficulty": config.get("CR_DIFFICULTY", "Connect"),
            "keywordsReport": config.get("CR_KEYWORDS_REPORT", ""),
            "outputConfig": config.get("CR_OUTPUT_CONFIG", '{"studyGuide": true, "quiz": true, "handout": false}'),
            "localFilePath": config.get("CR_LOCAL_FILE_PATH", ""),
            "quizConfig": config.get("CR_QUIZ_CONFIG", '{"mcq": 10, "ar": 5, "detailed": 3, "custom": ""}')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/save")
async def save_config(req: ConfigSaveRequest):
    try:
        if not ENV_PATH.exists(): ENV_PATH.touch()
        set_key(str(ENV_PATH), "MAX_TOKENS", str(req.maxTokens))
        set_key(str(ENV_PATH), "CHUNKING_STRATEGY", req.strategy)
        set_key(str(ENV_PATH), "CR_OUTPUT_TYPE", req.outputType)
        set_key(str(ENV_PATH), "HEADLESS", str(req.headless).lower())
        if req.chromeUserDataDir is not None:
            set_key(str(ENV_PATH), "CHROME_USER_DATA_DIR", req.chromeUserDataDir)
        if req.discoveryMethod is not None:
            set_key(str(ENV_PATH), "DISCOVERY_METHOD", req.discoveryMethod)
        if req.notebooklmAvailable is not None:
            set_key(str(ENV_PATH), "NOTEBOOKLM_AVAILABLE", str(req.notebooklmAvailable).lower())
        if req.deepseekAvailable is not None:
            set_key(str(ENV_PATH), "DEEPSEEK_AVAILABLE", str(req.deepseekAvailable).lower())
        if req.notebooklmGuided is not None:
            set_key(str(ENV_PATH), "NOTEBOOKLM_GUIDED", str(req.notebooklmGuided).lower())
        if req.trustedDomains is not None:
            set_key(str(ENV_PATH), "TRUSTED_DOMAINS", req.trustedDomains)
        if req.blockedDomains is not None:
            set_key(str(ENV_PATH), "BLOCKED_DOMAINS", req.blockedDomains)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/save")
async def save_admin(req: AdminSaveRequest):
    try:
        if not ENV_PATH.exists(): ENV_PATH.touch()
        set_key(str(ENV_PATH), "DEEPSEEK_API_KEY", req.deepseek)
        set_key(str(ENV_PATH), "GEMINI_API_KEY", req.gemini)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/discovery/fetch")
async def fetch_discovery_urls(req: DiscoveryRequest):
    try:
        pipeline = EduSearchPipeline()

        # Parse extra trusted domains
        extra_domains = None
        if req.trustedDomains:
            extra_domains = [d.strip() for d in req.trustedDomains.split(",") if d.strip()]

        # Parse blocked domains
        blocked_domains = None
        if req.blockedDomains:
            blocked_domains = [d.strip() for d in req.blockedDomains.split(",") if d.strip()]

        # Run search
        # Note: pipeline.search expects subtopic as a single string (if any).
        # We pass the raw subtopics string from UI, or maybe the first one?
        # For now, let's just pass it as is.

        results = pipeline.search(
            grade=int(req.grade) if req.grade.isdigit() else 8,
            subject=req.subject,
            topic=req.topic,
            subtopic=req.subtopics,
            max_results=req.maxResults,
            region=req.region,
            extra_domains=extra_domains,
            blocked_domains=blocked_domains
        )

        return {
            "success": True,
            "results": [r.to_dict() for r in results]
        }
    except Exception as e:
        print(f"Discovery Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/list")
async def list_projects():
    artifacts = []
    
    # Scan outputs/final
    final_dir = PROJECT_ROOT / "outputs" / "final"
    if final_dir.exists():
        for f in final_dir.iterdir():
            if f.is_file():
                artifacts.append({
                    "id": f.name,
                    "name": f.name,
                    "type": "FINAL",
                    "date": os.path.getmtime(str(f)),
                    "size": f"{f.stat().st_size / 1024:.1f}KB",
                    "path": str(f.relative_to(PROJECT_ROOT))
                })

    # Scan outputs/html/cleaned
    cleaned_dir = PROJECT_ROOT / "outputs" / "html" / "cleaned"
    if cleaned_dir.exists():
        for f in cleaned_dir.iterdir():
            if f.is_file():
                artifacts.append({
                    "id": f.name,
                    "name": f.name,
                    "type": "CLEANED",
                    "date": os.path.getmtime(str(f)),
                    "size": f"{f.stat().st_size / 1024:.1f}KB",
                    "path": str(f.relative_to(PROJECT_ROOT))
                })

    return {"artifacts": sorted(artifacts, key=lambda x: x["date"], reverse=True)}

@app.get("/api/explore")
async def explore_path(path: str):
    """Opens a file or folder in Windows Explorer."""
    try:
        # Normalize slashes for Windows compatibility
        safe_path = path.replace("/", os.sep).replace("\\", os.sep).strip(os.sep)
        full_path = (PROJECT_ROOT / safe_path).resolve()
        
        print(f"DEBUG: Attempting to explore: {full_path}")
        
        if not full_path.exists():
            print(f"DEBUG: Path NOT FOUND: {full_path}")
            raise HTTPException(status_code=404, detail=f"Path not found: {safe_path}")
        
        # On Windows, os.startfile opens the file/folder with the default app
        os.startfile(str(full_path))
        return {"success": True}
    except Exception as e:
        print(f"DEBUG: Explore ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
async def list_templates():
    templates_dir = PROJECT_ROOT / "templates"
    if not templates_dir.exists():
        return []
    
    files = []
    for f in templates_dir.glob("*.html"):
        files.append({
            "name": f.stem.replace("_", " ").title(),
            "id": f.stem,
            "filename": f.name
        })
    return files



@app.post("/api/template/read")
async def read_template_file(request: TemplateFileRequest):
    """Read Excel/CSV file and return headers + sample data"""
    try:
        templates_dir = PROJECT_ROOT / "templates"
        file_path = templates_dir / request.filepath
        
        # Validation: Check file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.filepath}")
        
        # Validation: Check file is within templates directory (security)
        if not str(file_path.resolve()).startswith(str(templates_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: Path traversal detected")
        
        # Read based on extension
        ext = file_path.suffix.lower()
        if ext == '.xlsx':
            df = pd.read_excel(file_path, engine='openpyxl')
        elif ext == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Only .xlsx and .csv are supported.")
        
        # Validation: Check if file is empty
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Get sheet names for Excel files
        sheet_names = []
        if ext == '.xlsx':
            xl = pd.ExcelFile(file_path, engine='openpyxl')
            sheet_names = xl.sheet_names
        
        # Return structure
        return JSONResponse({
            "success": True,
            "filename": file_path.name,
            "sheets": sheet_names,
            "columns": df.columns.tolist(),
            "rowCount": len(df),
            "sampleData": df.head(5).fillna("").to_dict(orient='records'),
            "columnTypes": {col: str(df[col].dtype) for col in df.columns}
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.get("/api/proxy/headers")
async def proxy_headers(url: str):
    """Fetch CSV headers and structure from an external URL (e.g. GitHub raw)"""
    # SSRF Protection: Whitelist allowed domains
    allowed_domains = ["raw.githubusercontent.com", "github.com", "gist.githubusercontent.com"]
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    if parsed_url.netloc not in allowed_domains:
        raise HTTPException(status_code=403, detail="Domain not allowed for proxy. Only GitHub URLs are allowed.")

    try:
        # Use pandas to read sample data
        df = pd.read_csv(url, nrows=5)

        # Create a text-based structure preview for the UI
        structure_preview = f"Source URL: {url}\n"
        structure_preview += f"Detected Columns ({len(df.columns)}): {', '.join(df.columns)}\n\n"
        structure_preview += "--- Sample Data (First 5 Rows) ---\n"
        structure_preview += df.to_csv(index=False)

        return {
            "success": True,
            "headers": df.columns.tolist(),
            "structure": structure_preview,
            "sampleData": df.fillna("").to_dict(orient='records')
        }
    except Exception as e:
        # Fallback for non-CSV or errors
        raise HTTPException(status_code=500, detail=f"Failed to fetch headers: {str(e)}")

@app.post("/api/template/upload")
async def upload_template_file(file: UploadFile = File(...)):
    """Upload and parse user's Excel/CSV file"""
    try:
        # Validation: Check file extension
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.xlsx', '.csv']:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Only .xlsx and .csv are supported.")
        
        # Validation: Check file size (max 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Read file
        if ext == '.xlsx':
            df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        elif ext == '.csv':
            df = pd.read_csv(io.BytesIO(contents))
        
        # Validation: Check if file is empty
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "columns": df.columns.tolist(),
            "rowCount": len(df),
            "sampleData": df.head(5).fillna("").to_dict(orient='records'),
            "columnTypes": {col: str(df[col].dtype) for col in df.columns}
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


def scan_templates_recursive(path: Path, root_path: Path) -> Any:
    """
    Recursively scans directory for CSV/Excel files.
    Returns:
      - List of file objects if no subdirectories found.
      - Dictionary of folder_name -> content if subdirectories found.
    """
    if not path.exists():
        return []

    items = list(path.iterdir())
    # Sort for consistent order
    items.sort(key=lambda x: x.name)

    subdirs = [x for x in items if x.is_dir()]
    files = [x for x in items if x.is_file() and x.suffix.lower() in ['.csv', '.xlsx']]

    # Helper to extract metadata (headers)
    def get_file_metadata(f: Path):
        rel_path = f.relative_to(root_path)
        file_id = str(rel_path).replace(os.sep, '-').replace('.', '-').lower()
        metadata = {
            "id": file_id,
            "filename": f.name,
            "path": str(rel_path).replace(os.sep, '/'),
            "columns": [],
            "rowCount": 0
        }
        try:
            # Basic metadata extraction
            ext = f.suffix.lower()
            if ext == '.csv':
                df = pd.read_csv(f, nrows=5)
                metadata["columns"] = df.columns.tolist()
                metadata["rowCount"] = 0 # Not counting full rows for speed in scan
            elif ext == '.xlsx':
                df = pd.read_excel(f, nrows=5, engine='openpyxl')
                metadata["columns"] = df.columns.tolist()
                metadata["rowCount"] = 0
        except Exception as e:
            print(f"Error reading metadata for {f}: {e}")
        return metadata

    # If we have subdirectories, we must return a dictionary to match FileTree schema
    if subdirs:
        result = {}
        for subdir in subdirs:
            subdir_content = scan_templates_recursive(subdir, root_path)
            # Only include non-empty folders (or folders that might contain files)
            if subdir_content:
                result[subdir.name] = subdir_content

        # Handle mixed content (files alongside folders)
        if files:
            # Create a "_Files" entry for loose files in this folder
            file_list = [get_file_metadata(f) for f in files]
            result["_Files"] = file_list

        return result
    else:
        # Leaf directory (or root with no subdirs): Return list of files
        return [get_file_metadata(f) for f in files]

@app.post("/api/templates/refresh")
async def refresh_templates():
    """Scans templates dir and caches structure to public/templates.json"""
    try:
        templates_dir = PROJECT_ROOT / "templates"
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True)

        tree = scan_templates_recursive(templates_dir, templates_dir)

        # Save to frontend/public/templates.json
        public_dir = PROJECT_ROOT / "frontend" / "public"
        public_dir.mkdir(exist_ok=True, parents=True)

        cache_file = public_dir / "templates.json"
        with open(cache_file, "w") as f:
            json.dump(tree, f, indent=2)

        # Also save to frontend/dist/templates.json if dist exists (for production serving)
        dist_dir = PROJECT_ROOT / "frontend" / "dist"
        if dist_dir.exists():
            with open(dist_dir / "templates.json", "w") as f:
                json.dump(tree, f, indent=2)

        return {"success": True, "tree": tree, "message": "Template cache updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

