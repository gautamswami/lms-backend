from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
from auth import pwd_context
from database import engine
from dependencies import get_db
from routers.auth_routers import app as auth_router
from routers.um_routers import app as um_routers
from routers.file_routers import app as file_routers
from routers.course_routers import app as courses_routers
from routers.stats_routers import app as stats_routers
from routers.enrollment import app as enrollment
from routers.quiz import app as quiz
from routers.learning_path_routers import app as learning_path_routers
from routers.feedback_routers import app as feedback_routers
from routers.external_certifications import app as external_certifications
from routers.app_status import app as app_status

# from create_sample_db import create_sample_data

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# create_sample_data()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event(db: Session = Depends(get_db)):
    service_lines = [
        "Business Risk",
        "Assurance",
        "Stat Audit",
        "Accounting Advisory",
        "Tech Risk",
        "HR",
        "Operations",
        "Pursuits",
        "IT Operations",
        "Content Writer",
        "Website Operation Specialist",
        "Financial Due Diligence",
        "Brands, Marketing and Communications",
    ]
    designations = [
        "Co-Founder - Assurance and Advisory Leader",
        "Director",
        "Senior Consultant",
        "Senior",
        "Manager",
        "Associate Director",
        "Assistant Manager",
        "Consultant",
        "Associate",
        "Executive - Operations",
        "Executive",
        "Executive Assistant",
        "Associate (Support) – Operations",
        "Trainee",
    ]
    external_roles = [
        "Business Risk",
        "Assurance",
        "Stat Audit",
        "Accounting Advisory",
        "Tech Risk",
        "HR",
        "Operations",
        "Pursuits",
        "IT Operations",
        "Content Writer",
        "Website Operation Specialist",
        "Financial Due Diligence",
        "Brands, Marketing and Communications",
    ]

    # Add service lines
    for name in service_lines:
        service_line = models.ServiceLine(name=name)
        db.add(service_line)

    # Add designations
    for name in designations:
        designation = models.Designations(name=name)
        db.add(designation)

    # Add external roles
    for name in external_roles:
        external_role = models.ExternalRoles(name=name)
        db.add(external_role)

    try:
        db.commit()
    except:
        pass
    # Create roles

    roles = [
        models.Role(RoleName="Super Admin", Description="Manages the whole system"),
        models.Role(RoleName="Admin", Description="Manages a specific LOB or department"),
        models.Role(RoleName="Instructor", Description="Manages own courses and can propose new ones"),
        models.Role(RoleName="Employee", Description="Can view and enroll in courses"),
    ]
    db.add_all(roles)
    try:
        db.commit()
    except:
        pass

    # Create service lines
    service_lines = [
        models.ServiceLine(name="Software Development"),
        models.ServiceLine(name="Data Science"),
    ]
    db.add_all(service_lines)
    try:
        db.commit()
    except:
        pass

    # Create users
    super_admin = models.User(
        email="superadmin@example.com",
        password=pwd_context.hash("password"),
        first_name="Super",
        last_name="Admin",
        role_name="Super Admin",
        employee_id="SA001",
        designation="Manager",
        service_line_id=service_lines[0].name,
        external_role_name="Assurance",
    )
    from datetime import datetime
    new_status = models.AppStatus(
        status_update=True, update_datetime=datetime.now()
    )
    db.add(new_status)
    db.add_all([super_admin])
    try:
        db.commit()
    except:
        pass


app.include_router(auth_router)
app.include_router(um_routers)
app.include_router(file_routers)
app.include_router(courses_routers)
app.include_router(stats_routers)
app.include_router(enrollment)
app.include_router(quiz)
app.include_router(learning_path_routers)
app.include_router(external_certifications)
app.include_router(feedback_routers)
app.include_router(app_status)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8800,
        ssl_keyfile="Cert/nginx.key",
        ssl_certfile="Cert/nginx.crt",
    )
