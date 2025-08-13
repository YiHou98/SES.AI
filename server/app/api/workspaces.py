from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, Workspace
from app.crud import crud_workspace

router = APIRouter()

@router.post("", response_model=Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Create a new workspace for the current user.
    """
    return crud_workspace.create_workspace(db=db, owner_id=user.id, workspace=workspace_in)

@router.get("", response_model=List[Workspace])
def get_workspaces(
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Get all workspaces owned by the current user.
    """
    return crud_workspace.get_workspaces_by_owner(db=db, owner_id=user.id)

@router.get("/{workspace_id}", response_model=Workspace)
def get_workspace_details(
    workspace_id: int,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Get details for a specific workspace.
    """
    workspace = crud_workspace.get_workspace(db, workspace_id=workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace