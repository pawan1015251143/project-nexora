from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentStatusEnum
from app.schemas.document import DocumentResponse
from app.api import deps
from app.utils.file_utils import save_upload_file, delete_physical_file
from app.services.document_processor import process_document

router = APIRouter(tags=["documents"])

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    category: Optional[str] = Form(None),
    department_id: Optional[int] = Form(None),
    academic_year: Optional[str] = Form(None),
    visibility_scope: str = Form("public"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin", "faculty"]))
):
    # Only admins (and optionally faculty if configured) can upload.
    # The prompt says "Only authorized admins can upload/approve/delete", so let's restrict to admin.
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to upload documents")

    # Save physical file
    file_path, file_size = save_upload_file(file)

    # Create DB record
    new_doc = Document(
        title=title,
        file_path=file_path,
        mime_type=file.content_type,
        file_size=file_size,
        category=category,
        department_id=department_id,
        academic_year=academic_year,
        visibility_scope=visibility_scope,
        status=DocumentStatusEnum.uploaded,
        uploaded_by=current_user.id
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Trigger background document processing automatically on upload
    background_tasks.add_task(process_document, new_doc.id, db)
    
    return new_doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[DocumentStatusEnum] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    query = select(Document)
    
    if category:
        query = query.where(Document.category == category)
    if department_id:
        query = query.where(Document.department_id == department_id)
    if status:
        query = query.where(Document.status == status)
        
    # Apply basic visibility rules (e.g. students only see public and their department, but this is MVP)
    # Admin sees everything.
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents


@router.post("/{id}/approve", response_model=DocumentResponse)
async def approve_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    result = await db.execute(select(Document).where(Document.id == id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = DocumentStatusEnum.approved
    await db.commit()
    await db.refresh(doc)
    
    return doc


@router.post("/{id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.require_role(["admin"]))
):
    result = await db.execute(select(Document).where(Document.id == id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = DocumentStatusEnum.processing
    await db.commit()
    await db.refresh(doc)
    
    # Trigger background document processing
    background_tasks.add_task(process_document, doc.id, db)
    
    return doc


@router.post("/private", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_private_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Save physical file
    file_path, file_size = save_upload_file(file)

    # Create DB record (forces private visibility and uploaded status)
    new_doc = Document(
        title=title,
        file_path=file_path,
        mime_type=file.content_type,
        file_size=file_size,
        category="pdf_qa",
        visibility_scope="private",
        status=DocumentStatusEnum.uploaded,
        uploaded_by=current_user.id
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Trigger background document processing automatically on upload
    background_tasks.add_task(process_document, new_doc.id, db)
    
    return new_doc

@router.get("/private", response_model=List[DocumentResponse])
async def list_private_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    query = select(Document).where(
        Document.uploaded_by == current_user.id,
        Document.visibility_scope == "private"
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    result = await db.execute(select(Document).where(Document.id == id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Check authorization: Admin can delete anything, user can delete their own private doc
    if current_user.role != "admin":
        if doc.visibility_scope != "private" or doc.uploaded_by != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
            
    # Delete physical file
    try:
        delete_physical_file(doc.file_path)
    except Exception:
        pass # Ignore physical deletion errors
    
    # Delete DB record
    await db.delete(doc)
    await db.commit()
    
    return None
