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

app = APIRouter(prefix='/files', tags=['files'])
storage = FileStorage()


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_metadata = storage.save_file(file, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"file_id": file_metadata.id, "message": "File uploaded successfully."}

@app.get("/{file_id}")
async def get_file(file_id: str, db: Session = Depends(get_db)):
    file_path = storage.get_file_metadata(file_id, db)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path)


@app.get("/streaming/files/{file_id}")
async def get_file(file_id: str, db: Session = Depends(get_db), stream_range: Optional[str] = Header(None), token: str = Depends(oauth2_scheme)):
    token = token.replace("Bearer ", "")
    token_data = auth.verify_token(token)
    logged_in_user = crud.get_user_by_email(db, email=token_data.username)
    return storage.get_streaming_response(file_id, db, stream_range)
