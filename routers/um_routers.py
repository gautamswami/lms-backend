import smtplib
from email.message import EmailMessage

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

import auth
import crud
from dependencies import get_db
from models import *
from schemas import *

app = APIRouter(prefix="/um", tags=["User Management"])

SMTP_SERVER = "smtp-mail.outlook.com"
PORT = 587
LOGIN = "lms@pierag.com"
PASSWORD = "HomeSweet@2024#"

# Email details
FROM_EMAIL = "lms@pierag.com"
TO_EMAIL = "akash21091999@gmail.com"
SUBJECT = "Test Email"
BODY = "This is a test email sent using SMTP in Python."

global user_secrets
user_secrets = {}


def send_reset_email(email: str, f_name: str, l_name: str):
    msg = EmailMessage()

    if email not in user_secrets:
        # Generate a new secret for the user
        secret = pyotp.random_base32()
        user_secrets[email] = secret
    else:
        secret = user_secrets[email]

    totp = pyotp.TOTP(secret)
    current_otp = totp.now()

    msg.set_content(
        f"""
            Dear {l_name} {f_name},

            We received a request to reset your password. To proceed with the password reset process, please use the following One-Time Password (OTP):

            {current_otp}

            This OTP is valid for the next 10 minutes. Please do not share this OTP with anyone for security reasons.

            If you did not request a password reset, please ignore this email or contact our support team immediately.

            Best regards,
            [Your Company Name] Support Team

            Contact us: [Support Email/Phone Number]"""
    )

    msg["Subject"] = "Your One-Time Password (OTP) for Password Reset"
    msg["From"] = FROM_EMAIL
    msg["To"] = email
    server = smtplib.SMTP(SMTP_SERVER, PORT)
    server.starttls()
    server.login(LOGIN, PASSWORD)
    text = msg.as_string()
    server.sendmail(FROM_EMAIL, email, text)
    server.quit()
    print("User Secrets:", user_secrets)


@app.post("/send-notification/")
def send_notification(
        email_data: EmailNotification,
):
    try:
        msg = EmailMessage()
        msg.set_content(f"{email_data.body}")
        msg["Subject"] = email_data.subject
        msg["From"] = FROM_EMAIL
        msg["To"] = email_data.to_email
        server = smtplib.SMTP(SMTP_SERVER, PORT)
        server.starttls()
        server.login(LOGIN, PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, email_data.to_email, text)
        server.quit()
        return JSONResponse(status_code=200, content="Mail sent successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/users/forgot-password/")
def forgot_password(
        email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """

    :type db: object
    :type email: object
    :type background_tasks: object
    """
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    background_tasks.add_task(
        send_reset_email, email, f_name=user.first_name, l_name=user.last_name
    )
    return {"message": "Check your email for the reset link"}


@app.post("/users/reset-password/")
def reset_password(reset: ResetPassword, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=400, detail="Invalid token")

    try:
        user = crud.get_user_by_email(db, email=reset.email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.email not in user_secrets:
            raise HTTPException(status_code=404, detail="Please retry")

        secret = user_secrets[user.email]
        totp = pyotp.TOTP(secret)

        # Verify OTP with additional leeway for time discrepancies
        if totp.verify(reset.otp, valid_window=1):
            user.password = auth.get_password_hash(reset.new_password)
            db.commit()
            print(f"Password reset successful for user: {reset.email}")
            return JSONResponse(
                status_code=200,
                content="The OTP is valid. Your password has been reset successfully.",
            )
        else:
            print(f"Invalid OTP for user: {reset.email}")
            raise HTTPException(status_code=400, detail="The OTP is invalid.")

    except HTTPException as http_exec:
        raise http_exec
    except Exception as e:
        print(f"Error in password reset: {str(e)}")
        raise credentials_exception


@app.post("/users/", response_model=UserDisplay, status_code=status.HTTP_201_CREATED)
def create_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    try:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=403, detail="Email already registered")
        return crud.create_user(db=db, user=user)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")


@app.get("/users/", response_model=List[UserDisplay])
def get_all_user(
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    users = db.query(User).all()
    return users


@app.get("/users/{user_id}", response_model=UserDisplay)
def read_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    try:
        if current_user.role_name not in ["Admin", "Super Admin"]:
            raise HTTPException(status_code=401, detail="Unauthorized ")
        db_user = crud.get_user(db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")


# noinspection PyTypeChecker
@app.put("/users/{user_id}/", response_model=UserDisplay)
def update_user(
        user_id: int,
        user: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    try:
        # update_data = user.dict(exclude_unset=True)
        db_user = crud.update_user(db, user_id=user_id, user=user)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")


@app.delete("/users/{user_id}", response_model=UserDisplay)
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    try:
        db_user = crud.delete_user(db, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")


# # noinspection PyTypeChecker
# @app.get("/get_all", response_model=UM_send_all)
# def get_all(
#     db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)
# ):
#     instructors = crud.get_users_by_filter(
#         db=db,
#         filters={
#             "service_line_id": current_user.service_line_id,
#             "role_name": "Instructor",
#         },
#     )
#     admins = crud.get_users_by_filter(
#         db=db,
#         filters={
#             "role_name": "Admin",
#         },
#     )
#     admin_displays = [UserDisplay.from_orm(admin) for admin in admins]
#     designations = db.query(Designations).all()
#     service_lines = db.query(ServiceLine).all()
#     external_roles = db.query(ExternalRoles).all()
#     internal_roles = db.query(Role).all()

#     instructor_displays = []
#     for instructor in instructors:
#         # noinspection PyTypeChecker
#         team_members = db.query(User).filter(User.counselor_id == instructor.id).all()
#         team_members_pydantic = [UserBase.from_orm(member) for member in team_members]
#         instructor_display = InstructorDisplay(
#             id=instructor.id,
#             first_name=instructor.first_name,
#             last_name=instructor.last_name,
#             email=instructor.email,
#             role_name=instructor.role_name,
#             employee_id=instructor.employee_id,
#             designation=instructor.designation,
#             service_line_id=instructor.service_line_id,
#             total_training_hours=instructor.total_training_hours,
#             external_role_name=instructor.external_role_name,
#             counselor=(
#                 UserBase.from_orm(instructor.counselor)
#                 if instructor.counselor
#                 else None
#             ),
#             team_members=team_members_pydantic,
#         )
#         instructor_displays.append(instructor_display)

#     return UM_send_all(
#         instructors=instructor_displays,
#         admins=admin_displays,
#         designations=[
#             DesignationModel.from_orm(designation) for designation in designations
#         ],
#         service_lines=[
#             ServiceLineModel.from_orm(service_line) for service_line in service_lines
#         ],
#         external_roles=[ExternalRoleModel.from_orm(role) for role in external_roles],
#         internal_roles=[InternalRoleModel.from_orm(role) for role in internal_roles],
#     )


@app.get("/get_all", response_model=UM_send_all)
def get_all(
        db: Session = Depends(get_db), current_user: User = Depends(auth.get_current_user)
):
    if current_user.role_name == "Super Admin":
        # Fetch all users without regard to service line if user is Super Admin
        instructors = (
            db.query(User)
            .options(joinedload(User.team_members))
            .filter(User.role_name == "Instructor")
            .all()
        )
    else:
        # Fetch users within the same service line and for specific roles if not Super Admin
        instructors = (
            db.query(User)
            .options(joinedload(User.team_members))
            .filter(
                User.service_line_id == current_user.service_line_id,
                User.role_name == "Instructor",
            )
            .all()
        )

        # instructors = (
        #     db.query(User)
        #     .filter(
        #         User.service_line_id == current_user.service_line_id,
        #         User.role_name == "Instructor",
        #     )
        #     .all()
        # )

    admins = db.query(User).filter(User.role_name == "Admin").all()

    admin_displays = [UserDisplay.from_orm(admin) for admin in admins]
    instructor_displays = [
        InstructorDisplay.from_orm(instructor) for instructor in instructors
    ]

    # Additional data fetches (assuming these are unchanged)
    designations = db.query(Designations).all()
    service_lines = db.query(ServiceLine).all()
    external_roles = db.query(ExternalRoles).all()
    internal_roles = db.query(Role).all()

    # Assemble the complete display data
    return UM_send_all(
        instructors=instructor_displays,
        admins=admin_displays,
        designations=[
            DesignationModel.from_orm(designation) for designation in designations
        ],
        service_lines=[
            ServiceLineModel.from_orm(service_line) for service_line in service_lines
        ],
        external_roles=[ExternalRoleModel.from_orm(role) for role in external_roles],
        internal_roles=[InternalRoleModel.from_orm(role) for role in internal_roles],
    )


@app.get("/counselor/{counselor_id}/team_members", response_model=List[UserTeamView])
def get_team_members(
        counselor_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    # Fetch the counselor to validate existence and role
    if counselor_id == 0:
        counselor = current_user
    else:
        counselor = (
            db.query(User)
            .filter(User.id == counselor_id)
            .first()
        )
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    team_members = counselor.team_members
    if not team_members:
        return []

    team_member_details = []
    for member in team_members:
        # enrollments = db.query(Enrollment).filter(Enrollment.user_id == member.id).all()
        completed_trainings = [e for e in member.enrollments if e.status == "Completed"]
        pending_trainings = [e for e in member.enrollments if e.status == "Enrolled"]

        mandatory_overdue = sum(
            1
            for e in member.enrollments
            if e.course.category == "Mandatory"
            and e.status != "Completed"
            and e.due_date < datetime.now()
        )

        completed_hours = sum(
            e.course.expected_time_to_complete for e in completed_trainings
        )
        technical_hours = sum(
            e.course.expected_time_to_complete
            for e in completed_trainings
            if e.course.category == "technical"
        )
        non_technical_hours = sum(
            e.course.expected_time_to_complete
            for e in completed_trainings
            if e.course.category == "nonTechnical"
        )

        compliance_status = (
            "Compliant"
            if technical_hours >= 50 and non_technical_hours >= 15
            else "Non-Compliant"
        )

        team_member_details.append(
            UserTeamView(
                id=member.id,
                first_name=member.first_name,
                last_name=member.last_name,
                email=member.email,
                role_name=member.role_name,
                employee_id=member.employee_id,
                designation=member.designation,
                service_line_id=member.service_line_id,
                external_role_name=member.external_role_name,
                entity=member.entity,
                number_of_trainings_completed=len(completed_trainings),
                hours_of_training_completed=completed_hours,
                hours_of_non_technical_training_completed=non_technical_hours,
                hours_of_technical_training_completed=technical_hours,
                hours_of_technical_training_target=50,
                hours_of_non_technical_training_target=15,
                number_of_trainings_pending=len(pending_trainings),
                number_of_mandatory_trainings_overdue=mandatory_overdue,
                compliance_status=compliance_status,
                reminder_needed=mandatory_overdue > 0,
            )
        )

    return team_member_details


@app.get("/counselor/{counselor_id}/unassigened/", response_model=List[UserTeamView])
def get_team_members(
        counselor_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth.get_current_user),
):
    # Fetch the counselor to validate existence and role
    if counselor_id == 0:
        counselor = current_user
    else:
        counselor = (
            db.query(User)
            .filter(User.id == counselor_id)
            .first()
        )
    if not counselor:
        raise HTTPException(status_code=404, detail="Counselor not found")

    team_members = counselor.team_members
    if not team_members:
        return []

    team_member_details = []
    for member in team_members:
        hours_of_technical_training_target = 50
        hours_of_non_technical_training_target = 15
        if member.total_tech_enrolled_hours > hours_of_technical_training_target and member.total_non_tech_enrolled_hours > hours_of_non_technical_training_target:
            continue
        # enrollments = db.query(Enrollment).filter(Enrollment.user_id == member.id).all()
        completed_trainings = [e for e in member.enrollments if e.status == "Completed"]
        pending_trainings = [e for e in member.enrollments if e.status == "Enrolled"]

        mandatory_overdue = sum(
            1
            for e in member.enrollments
            if e.course.category == "Mandatory"
            and e.status != "Completed"
            and e.due_date < datetime.now()
        )

        completed_hours = sum(
            e.course.expected_time_to_complete for e in completed_trainings
        )
        technical_hours = sum(
            e.course.expected_time_to_complete
            for e in completed_trainings
            if e.course.category == "technical"
        )
        non_technical_hours = sum(
            e.course.expected_time_to_complete
            for e in completed_trainings
            if e.course.category == "nonTechnical"
        )

        compliance_status = (
            "Compliant"
            if technical_hours >= 50 and non_technical_hours >= 15
            else "Non-Compliant"
        )

        team_member_details.append(
            UserTeamView(
                id=member.id,
                first_name=member.first_name,
                last_name=member.last_name,
                email=member.email,
                role_name=member.role_name,
                employee_id=member.employee_id,
                designation=member.designation,
                service_line_id=member.service_line_id,
                external_role_name=member.external_role_name,
                entity=member.entity,
                number_of_trainings_completed=len(completed_trainings),
                hours_of_training_completed=completed_hours,
                hours_of_non_technical_training_completed=non_technical_hours,
                hours_of_technical_training_completed=technical_hours,
                hours_of_technical_training_target=50,
                hours_of_non_technical_training_target=15,
                number_of_trainings_pending=len(pending_trainings),
                number_of_mandatory_trainings_overdue=mandatory_overdue,
                total_tech_enrolled_hours=User.total_tech_enrolled_hours,
                total_non_tech_enrolled_hours=User.total_non_tech_enrolled_hours,
                compliance_status=compliance_status,
                reminder_needed=mandatory_overdue > 0,
            )
        )

    return team_member_details

# @app.post("/users/{user_id}/profile_pic", status_code=200)
# async def upload_profile_pic(
#     user_id: int = Path(..., description="The ID of the course"),
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
# ):
#     # Check if the file is an image
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(
#             status_code=400, detail="Unsupported file type. Please upload an image."
#         )

#     file_storage = FileStorage()

#     # Save the file using the storage class
#     try:
#         file_metadata = file_storage.save_file(file, db, type="profile_pic")
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

#     # Fetch the course and update its thumbnail_file_id
#     course = db.query(Course).filter(Course.id == user_id).first()
#     if not course:
#         raise HTTPException(status_code=404, detail="Course not found")

#     course.thumbnail_file_id = file_metadata.FileID
#     db.commit()

#     return {
#         "message": "Thumbnail updated successfully.",
#         "file_id": file_metadata.FileID,
#     }
