from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8800,
        ssl_keyfile="Cert/nginx.key",
        ssl_certfile="Cert/nginx.crt",
    )
