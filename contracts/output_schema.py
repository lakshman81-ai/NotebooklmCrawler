from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class OutputMetadata(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    output_type: str
    pipeline_version: str = "1.0.0"
    ai_metadata: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None

class FinalOutput(BaseModel):
    summary: str
    metadata: OutputMetadata
    format: str
    content: Dict[str, Any]
