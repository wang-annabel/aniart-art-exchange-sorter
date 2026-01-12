from pydantic import BaseModel
from fastapi_users import schemas
from uuid import UUID
#from app.matching import Artist

class UnmatchedArtist(BaseModel):
    name: str
    email: str
    discord: str

class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    participant_count: int


class MatchResponse(BaseModel):
    matching_id: UUID
    file_id: UUID
    success: bool
    matched_count: int
    total_count: int
    unmatched: list[UnmatchedArtist]

class GraphNode(BaseModel):
    id: str
    name: str
    discord: str
    email: str

class GraphLink(BaseModel):
    source: str
    target: str

class GraphResponse(BaseModel):
    matching_id: UUID
    nodes: list[GraphNode]
    links: list[GraphLink]
    participants: int
    cycles: int
    unmatched: int
    # also nodes and links

class UserRead(schemas.BaseUser[UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    name: str | None = None

class UserUpdate(schemas.BaseUserUpdate):
    pass
