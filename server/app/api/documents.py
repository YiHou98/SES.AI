import shutil
from sqlalchemy.orm import Session
import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from app.crud import crud_job, crud_workspace, crud_document

from app.api import deps
from app.models.user import User
from app.services.rag_service import RAGService
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    workspace_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user),
    rag_service: RAGService = Depends(deps.get_rag_service),
):
    #Verify that the user owns the workspace they are uploading to
    workspace = crud_workspace.get_workspace(db, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    
    job_id = str(uuid.uuid4())
    crud_job.create_job(db, job_id=job_id, user_id=user.id)
    db_document = crud_document.create_document(db, workspace_id=workspace_id, filename=file.filename)

    temp_file_path = None
    try:
        temp_dir = os.path.join(settings.VECTOR_STORE_PATH, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        background_tasks.add_task(
            rag_service.process_document_in_background,
            file_path=temp_file_path,
            workspace_id=workspace_id, # <-- 3. Pass workspace_id instead of user_id
            document_id=db_document.id,
            job_id=job_id
        )
        return {"message": "Upload accepted. Processing in background.", "job_id": job_id}
    finally:
        file.file.close()

@router.get("/upload/status/{job_id}")
def get_upload_status(
    job_id: str,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    job = crud_job.get_job(db, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job.status, "details": job.details}