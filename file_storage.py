import os
import uuid
from typing import Optional

from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models import FileMetadata


class FileStorage:
    def __init__(self, directory: str = "file_storage"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save_file(self, file: UploadFile, db: Session) -> FileMetadata:
        content_type = file.content_type
        allowed_types = {'application/vnd.ms-powerpoint', 'video/mp4', 'application/pdf', 'application/msword', 'audio/mpeg'}

        if content_type not in allowed_types:
            raise ValueError("Unsupported file type.")

        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(self.directory, f"{file_id}.{file_extension}")

        with open(file_path, "wb") as buffer:
            for chunk in file.file:
                buffer.write(chunk)

        file_metadata = FileMetadata(
            id=file_id,
            filename=file.filename,
            content_type=content_type,
            path=file_path
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
        return file_metadata

    def get_file_metadata(self, file_id: str, db: Session) -> FileMetadata:
        file_metadata = db.query(FileMetadata).filter(FileMetadata.id == file_id).first()
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found.")
        return file_metadata

    def download_file(self, file_path: str, start: int = 0, end: Optional[int] = None):
        file_size = os.path.getsize(file_path)
        if end is None:
            end = file_size - 1

        def iterfile():
            with open(file_path, "rb") as file:
                file.seek(start)
                bytes_to_read = (end - start) + 1 if end else None
                while bytes_to_read is None or bytes_to_read > 0:
                    chunk = file.read(min(4096, bytes_to_read) if bytes_to_read else 4096)
                    if not chunk:
                        break
                    if bytes_to_read:
                        bytes_to_read -= len(chunk)
                    yield chunk

        return iterfile(), file_size

    def get_streaming_response(self, file_id: str, db: Session, range_header: Optional[str]) -> StreamingResponse:
        file_metadata = self.get_file_metadata(file_id, db)
        file_path = file_metadata.path

        start, end = 0, None
        if range_header:
            range_header = range_header.strip().lower().replace("bytes=", "")
            start, end = map(lambda x: int(x) if x else None, range_header.split("-"))

        chunks, file_size = self.download_file(file_path, start=start, end=end)
        end = file_size - 1 if end is None else end

        headers = {
            'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(end - start + 1),
            'Content-Type': file_metadata.content_type
        }
        return StreamingResponse(chunks, headers=headers, status_code=206)
