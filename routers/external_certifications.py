from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session

from auth import get_current_user
from dependencies import get_db
from file_storage import FileStorage
from models import ExternalCertification, User
from schemas import ExternalCertificationDisplay, ExternalCertificationCreate

app = APIRouter(tags=["external_certifications"])


@app.post("/external_certifications/", response_model=ExternalCertificationDisplay)
def create_external_certification(certification: ExternalCertificationCreate = Form(...),
                                  files: UploadFile = File(...),
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)):
    file_storage = FileStorage()
    file_metadata = file_storage.save_file(
        files, db, type="External Certificate"
    )

    new_certification = ExternalCertification(**certification.dict(),
                                              uploaded_by_id=current_user.id,
                                              file_id=file_metadata.FileID)
    db.add(new_certification)
    db.commit()
    db.refresh(new_certification)
    return new_certification


@app.get("/external_certifications/", response_model=List[ExternalCertificationDisplay])
def read_external_certifications(db: Session = Depends(get_db)):
    certifications = db.query(ExternalCertification).all()
    return certifications


@app.put("/external_certifications/{certification_id}", response_model=ExternalCertificationDisplay)
def update_external_certification(certification_id: int, certification_data: ExternalCertificationCreate,
                                  db: Session = Depends(get_db)):
    certification = db.query(ExternalCertification).filter(ExternalCertification.id == certification_id).first()
    if certification is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    for key, value in certification_data.dict().items():
        setattr(certification, key, value)
    db.commit()
    return certification


@app.delete("/external_certifications/{certification_id}", status_code=204)
def delete_external_certification(certification_id: int, db: Session = Depends(get_db)):
    certification = db.query(ExternalCertification).filter(ExternalCertification.id == certification_id).first()
    if certification is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    db.delete(certification)
    db.commit()
    return Response(status_code=204)