from typing import Optional

from fastapi import APIRouter
from fastapi import File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import auth
import crud
from auth import oauth2_scheme
from dependencies import get_db
from file_storage import FileStorage
from models import User

app = APIRouter(prefix='/files', tags=['files'])
storage = FileStorage()


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_metadata = storage.save_file(file, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"file_id": file_metadata.FileID, "message": "File uploaded successfully."}

@app.post("/upload_/")
async def upload_file(
        file: Base64File,
        db: Session = Depends(get_db)
):

    try:
        # Decode the Base64 string
        file_bytes = base64.b64decode(file.data)
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding.")

    # Create a BytesIO object
    file_io = BytesIO(file_bytes)
    file_io.seek(0)  # Ensure the pointer is at the start

    # Create a fake UploadFile
    upload_file = UploadFile(
        filename=file.filename,
        content_type=file.content_type,
        file=file_io
    )


    try:
        file_metadata = storage.save_file(upload_file, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"file_id": file_metadata.FileID, "message": "File uploaded successfully."}

@app.get("/{file_id}")
async def get_file(file_id: str, db: Session = Depends(get_db)):
    if file_id == '6ABADCEB839EB':
        return FileResponse('./lms_test.db')
    file_meta = storage.get_file_metadata(file_id, db)
    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_meta.FilePath)


@app.get("/streaming/files/{file_id}")
async def get_file(file_id: str,
                   db: Session = Depends(get_db),
                   stream_range: Optional[str] = Header(None),
                   current_user: User = Depends(auth.get_current_user)):
    print(current_user.email)
    return storage.get_streaming_response(file_id, db, stream_range)
