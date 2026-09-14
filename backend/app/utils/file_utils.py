import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# Config (ideally moved to core/config.py later)
UPLOAD_DIR = Path("uploads")
ALLOWED_MIME_TYPES = {"application/pdf", "text/plain"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def validate_file(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Only PDF and TXT are allowed."
        )
    
    # Check file size by seeking
    file.file.seek(0, 2) # Seek to end
    file_size = file.file.tell()
    file.file.seek(0) # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Max size is {MAX_FILE_SIZE / (1024*1024)}MB."
        )

def generate_safe_filename(original_filename: str) -> str:
    # Extract extension securely
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        ext = ".bin" # Fallback if someone spoofed MIME type
        
    return f"{uuid.uuid4().hex}{ext}"

def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
    ensure_upload_dir()
    validate_file(upload_file)
    
    safe_filename = generate_safe_filename(upload_file.filename or "unknown")
    file_path = UPLOAD_DIR / safe_filename
    
    # Path traversal protection is inherently handled by generating a UUID filename
    # and combining it with a fixed UPLOAD_DIR
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        return str(file_path), file_size
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file."
        )

def delete_physical_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists() and path.is_file():
        # Simple path traversal check before deletion: must be within UPLOAD_DIR
        try:
            path.resolve().relative_to(UPLOAD_DIR.resolve())
            path.unlink()
        except ValueError:
            pass # File is outside UPLOAD_DIR, ignore for security
