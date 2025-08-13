from pydantic import BaseModel
from typing import List

class DocumentBase(BaseModel):
    filename: str

class Document(DocumentBase):
    id: int

    class Config:
        from_attributes = True

class WorkspaceBase(BaseModel):
    name: str
    domain: str | None = None

class WorkspaceCreate(WorkspaceBase):
    pass

class Workspace(WorkspaceBase):
    id: int
    owner_id: int
    documents: List[Document] = []

    class Config:
        from_attributes = True