from pydantic import BaseModel

class Chunk(BaseModel):
    chunk_id: int
    source_heading: str
    source_title: str = "Unknown"
    text: str
    token_estimate: int
    metadata: dict = {}

    class Config:
        extra = "allow"
