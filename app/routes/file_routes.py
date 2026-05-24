from uuid import uuid4, UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.mino import ensure_bucket_exists, upload_fileobj, generate_presigned_download_url, delete_object
from app.models import FileUpload, User
from app.utils.JWT import get_current_user
from io import BytesIO
from typing import List

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    ensure_bucket_exists()
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file not allowed")
    
    storage_key = f"{current_user.id}/{uuid4()}-{file.filename}"

    upload_fileobj(file_obj=BytesIO(contents), key=storage_key, content_type=file.content_type or "application/octet-stream")

    record = FileUpload(
        user_id=current_user.id,
        original_filename=file.filename,
        storage_key=storage_key,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents)
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return{
        "id": str(record.id),
        "original_filename": record.original_filename,
        "mime_type": record.mime_type,
        "size_bytes": record.size_bytes,
        "created_at": record.created_at
    }

@router.post("/upload-multiple", status_code=status.HTTP_201_CREATED)
async def upload_multiple_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    ensure_bucket_exists()
    uploaded = []
    for file in files:
        contents = await file.read()
        if not contents:
            continue

        storage_key = f"{current_user.id}/{uuid4()}-{file.filename}"
        upload_fileobj(file_obj=BytesIO(contents), key=storage_key, content_type=file.content_type or "application/octet-stream")

        record = FileUpload(
            user_id=current_user.id,
            original_filename=file.filename,
            storage_key=storage_key,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents)
        )
        db.add(record)
        db.flush()
        uploaded.append({
            "id": str(record.id),
            "original_filename": record.original_filename,
            "mime_type": record.mime_type,
            "size_bytes": record.size_bytes,
            "created_at": record.created_at,
            "storage_key": record.storage_key
        })
    db.commit()
    return {"uploaded_files": uploaded}

@router.get("/{file_id}/download_url")
def get_download_url(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = (db.query(FileUpload)
    .filter(FileUpload.id == file_id, FileUpload.user_id == current_user.id).first())
   
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    url = generate_presigned_download_url(record.storage_key, expires_in=300)
    return {"download_url": url}

@router.get("/files")
def list_files(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = (db.query(FileUpload)
               .filter(FileUpload.user_id == current_user.id)
               .order_by(FileUpload.created_at.desc())
               .all())
    
    return [{
        "id": str(record.id),
        "original_filename": record.original_filename,
        "mime_type": record.mime_type,
        "size_bytes": record.size_bytes,
        "created_at": record.created_at
    } for record in records]

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = (db.query(FileUpload)
    .filter(FileUpload.id == file_id, FileUpload.user_id == current_user.id).first())
    
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    delete_object(record.storage_key)
    db.delete(record)
    db.commit()