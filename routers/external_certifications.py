from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy import desc
from sqlalchemy.orm import Session

from auth import get_current_user
from dependencies import get_db
from file_storage import FileStorage
from models import ExternalCertification, User
from schemas import ExternalCertificationDisplay, ExternalCertificationCreate, CertificationFilter, \
    ExternalCertificationUpdate

app = APIRouter(tags=["external_certifications"])


@app.post("/external_certifications/", response_model=ExternalCertificationDisplay)
def create_external_certification(certification: ExternalCertificationCreate,
                                  db: Session = Depends(get_db),
                                  current_user: User = Depends(get_current_user)):
    new_certification = ExternalCertification(**certification.dict(),
                                              uploaded_by_id=current_user.id)
    db.add(new_certification)
    db.commit()
    db.refresh(new_certification)
    return new_certification


@app.get("/external_certifications/", response_model=List[ExternalCertificationDisplay])
def read_external_certifications(db: Session = Depends(get_db)):
    certifications = db.query(ExternalCertification).order_by(desc(ExternalCertification.id)).all()
    return certifications


@app.get("/external_certifications/filter/", response_model=List[ExternalCertificationDisplay])
def get_certifications_by_filters(filters: CertificationFilter = Depends(), db: Session = Depends(get_db)):
    query = db.query(ExternalCertification)

    if filters.category:
        query = query.filter(ExternalCertification.category == filters.category)
    if filters.uploaded_by_id:
        query = query.filter(ExternalCertification.uploaded_by_id == filters.uploaded_by_id)

    certifications = query.all()
    if not certifications:
        raise HTTPException(status_code=404, detail="No certifications found matching the criteria")

    return certifications

@app.put("/external_certifications/{certification_id}", response_model=ExternalCertificationDisplay)
def update_external_certification(certification_id: int, certification_data: ExternalCertificationUpdate,
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



@app.patch("/external_certifications/{certification_id}/approve")
def approve_external_certifications(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name in ["Employee"]:
        raise HTTPException(status_code=403, detail="Only admins can approve courses")
    course = db.query(ExternalCertification).filter(ExternalCertification.id == certification_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="external_certifications not found")
    if course.status == "approve":
        raise HTTPException(status_code=404, detail="already approved")

    course.status = "approve"
    course.approved_by = current_user.id
    course.approved_date = datetime.now()
    db.commit()
    return {"message": "external_certifications approved successfully"}


@app.patch("/external_certifications/{certification_id}/reject")
def reject_external_certifications(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role_name in ["Employee"]:
        raise HTTPException(status_code=403, detail="Only admins can approve courses")
    course = db.query(ExternalCertification).filter(ExternalCertification.id == certification_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="external_certifications not found")
    if course.status == "approve":
        raise HTTPException(status_code=404, detail="already approved")

    course.status = "reject"
    course.approved_by = current_user.id
    course.approved_date = datetime.now()
    db.commit()
    return {"message": "external_certifications reject successfully"}

