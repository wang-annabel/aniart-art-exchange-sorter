from pydantic import BaseModel
from fastapi_users import schemas
from uuid import UUID
#from app.matching import Artist

class UnmatchedArtist(BaseModel):
    name: str
    email: str
    discord: str

class MatchResponse(BaseModel):
    matching_id: UUID
    success: bool
    matched_count: int
    total_count: int
    unmatched: list[UnmatchedArtist]
