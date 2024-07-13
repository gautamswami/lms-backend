import os
import uuid
from typing import Optional, Type

from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models import File


class FileStorage:
    def __init__(self, directory: str = "file_storage"):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save_file(self, file: UploadFile, db: Session, type='Course content') -> File:
        content_type = file.content_type
        allowed_types = {'application/vnd.ms-powerpoint.addin.macroEnabled.12',
                         'application/vnd.ms-word.document.macroEnabled.12',
                         'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                         'application/msword', 'application/vnd.openxmlformats-officedocument.presentationml.template',
                         'application/vnd.ms-access',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
                         'application/vnd.ms-excel.addin.macroEnabled.12',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
                         'application/vnd.ms-powerpoint.slideshow.macroEnabled.12',
                         'application/vnd.ms-word.template.macroEnabled.12',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'application/vnd.ms-powerpoint.template.macroEnabled.12',
                         'application/vnd.ms-excel.sheet.macroEnabled.12',
                         'application/vnd.ms-powerpoint.presentation.macroEnabled.12', 'application/vnd.ms-powerpoint',
                         'application/vnd.ms-excel', 'application/vnd.ms-excel.template.macroEnabled.12',
                         'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
                         'video/mp4',
                         'application/pdf',
                         'application/msword',
                         'audio/mpeg',
                         'image/jpeg',
                         'image/png',
                         'image/gif'
                         }

        if content_type not in allowed_types:
            raise ValueError("Unsupported file type.")

        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(self.directory, f"{file_id}.{file_extension}")

        with open(file_path, "wb") as buffer:
            for chunk in file.file:
                buffer.write(chunk)

        file_metadata = File(
            FileID=file_id,
            FileName=file.filename,
            FileType=content_type,
            FilePath=file_path,
            type=type
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
        return file_metadata

    def get_file_metadata(self, file_id: str, db: Session) -> Type[File]:
        file_metadata = db.query(File).filter(File.FileID == file_id).first()
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
        file_path = file_metadata.FilePath

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
            'Content-Type': file_metadata.FileType
        }
        return StreamingResponse(chunks, headers=headers, status_code=206)
