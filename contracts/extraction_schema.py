from pydantic import BaseModel
from typing import List

class ExtractedSection(BaseModel):
    heading: str
    content: str

class ExtractedDocument(BaseModel):
    title: str
    sections: List[ExtractedSection]
    source_url: str
