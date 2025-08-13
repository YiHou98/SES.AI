from sqlalchemy.orm import Session
from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.workspace import WorkspaceCreate

def get_workspace(db: Session, workspace_id: int):
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()

def get_workspaces_by_owner(db: Session, owner_id: int):
    return db.query(Workspace).filter(Workspace.owner_id == owner_id).all()

def get_workspace_by_name(db: Session, owner_id: int, name: str) -> Workspace | None:
    """
    Finds a workspace by its name for a specific user.
    """
    return db.query(Workspace).filter(Workspace.owner_id == owner_id, Workspace.name == name).first()

def create_workspace(db: Session, owner_id: int, workspace: WorkspaceCreate) -> Workspace:
    db_workspace_with_same_name = get_workspace_by_name(db, owner_id=owner_id, name=workspace.name)
    if db_workspace_with_same_name:
        # We'll just return the existing workspace instead of raising an error.
        # This prevents creating duplicates if the user clicks the button twice.
        return db_workspace_with_same_name
    
    db_workspace = Workspace(**workspace.model_dump(), owner_id=owner_id)
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace

def add_document_to_workspace(db: Session, workspace_id: int, filename: str) -> Document:
    db_document = Document(workspace_id=workspace_id, filename=filename)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document