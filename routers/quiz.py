from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Questions, QuizCompletions, Course, Chapter, Enrollment
from schemas import (
    QuestionDisplay,
    QuestionCreate,
    QuestionUpdate,
    QuestionGetRequest,
    QuestionSubmission,
    QuizCompletionResponse,
    QuestionAddToChapter,
)
from datetime import datetime
from typing import List, Optional
from fastapi import Query

app = APIRouter(tags=["course", "quiz"])


@app.post("/courses/{course_id}/question/", response_model=QuestionDisplay)
def add_quiz_question_to_course(
    course_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    new_question = Questions(course_id=course_id, **quiz_data.dict())
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


# Endpoint to add quiz questions to a course using bulk insert
@app.post("/courses/{course_id}/questions/")
def add_quiz_questions_to_course(
    course_id: int, quiz_data: QuestionAddToChapter, db: Session = Depends(get_db)
):
    try:
        questions_to_add = []
        for q_data in quiz_data.question_list:
            new_question = {
                "course_id": course_id,
                "question": q_data.question,
                "option_a": q_data.option_a,
                "option_b": q_data.option_b,
                "option_c": q_data.option_c,
                "option_d": q_data.option_d,
                "correct_answer": q_data.correct_answer,
            }
            questions_to_add.append(new_question)
        for q_id in quiz_data.question_ids:
            question = db.query(Questions).filter(Questions.id == q_id).first()
            if question:
                question.course_id = course_id
            else:
                raise HTTPException(
                    detail=f"Question id is not valid : {q_id}", status_code=404
                )
        if questions_to_add: 
            db.execute(Questions.__table__.insert(), questions_to_add)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chapters/{chapter_id}/question/", response_model=QuestionDisplay)
def add_quiz_question_to_chapter(
    chapter_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)
):
    new_question = Questions(chapter_id=chapter_id, **quiz_data.dict())
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


# Endpoint to add quiz questions to a chapter using bulk insert
@app.post("/chapters/{chapter_id}/questions/")
def add_quiz_questions_to_chapter(
    chapter_id: int, quiz_data: List[QuestionCreate], db: Session = Depends(get_db)
):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    try:
        questions_to_add = []
        for q_data in quiz_data:
            new_question = Questions(
                chapter_id=chapter_id,
                question=q_data.question,
                option_a=q_data.option_a,
                option_b=q_data.option_b,
                option_c=q_data.option_c,
                option_d=q_data.option_d,
                correct_answer=q_data.correct_answer,
            )
            db.add(new_question)
            db.commit()
            db.refresh(new_question)
            questions_to_add.append(new_question)

        return True

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_id}", response_model=QuestionDisplay)
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@app.get("/questions/{question_id}", response_model=QuestionDisplay)
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@app.put("/questions/{question_id}", response_model=QuestionDisplay)
def update_question(
    question_id: int, question_data: QuestionUpdate, db: Session = Depends(get_db)
):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    for var, value in vars(question_data).items():
        if value is not None:
            setattr(question, var, value)

    db.commit()
    return question


@app.post("/questions", response_model=List[QuestionDisplay])
def get_questions_by_course_or_chapter(
    request: QuestionGetRequest, db: Session = Depends(get_db)
):
    query = db.query(Questions)

    # Check if course_id list is not empty and apply filter
    if request.course_id:
        query = query.filter(Questions.course_id.in_(request.course_id))

    # Check if chapter_id list is not empty and apply filter
    if request.chapter_id:
        query = query.filter(Questions.chapter_id.in_(request.chapter_id))

    questions = query.all()
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions found for the specified courses or chapters",
        )

    return questions


@app.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}


# @app.post("/questions/submission/", response_model=QuizCompletionResponse)
# def submit_question(
#     submission: QuestionSubmission = Depends(),
#     db: Session = Depends(get_db),
# ):
#     # Retrieve the question to check the correct answer
#     question = (
#         db.query(Questions).filter(Questions.id == submission.question_id).first()
#     )
#     if not question:
#         raise HTTPException(status_code=404, detail="Question not found")

#     # Check if the selected option is correct
#     is_correct = submission.selected_option == question.correct_answer

#     # Create a new quiz completion record
#     new_quiz_completion = QuizCompletions(
#         question_id=submission.question_id,
#         correct_answer=is_correct,
#         source=submission.source,
#         enrollment_id=submission.enrollment_id,
#         attempt_datetime=datetime.now(),
#     )
#     # Calculate the attempt number before committing
#     new_quiz_completion.attempt_no = new_quiz_completion.calculate_attempt_no(db)

#     db.add(new_quiz_completion)
#     db.commit()

#     return new_quiz_completion


@app.post("/questions/submission/", response_model=QuizCompletionResponse)
def submit_question(
    submission: QuestionSubmission = Depends(),
    db: Session = Depends(get_db),
):
    # Retrieve the question to check the correct answer
    question = (
        db.query(Questions).filter(Questions.id == submission.question_id).first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Find the corresponding enrollment
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == submission.user_id,
            Enrollment.course_id == submission.course_id,
            # Enrollment.status
            # != "Completed",  # Assuming you want to filter out completed courses
        )
        .first()
    )
    print(enrollment)
    if not enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found for the given course and user"
        )

    # Check if the selected option is correct
    is_correct = submission.selected_option == question.correct_answer

    # Create a new quiz completion record
    new_quiz_completion = QuizCompletions(
        question_id=submission.question_id,
        correct_answer=is_correct,
        source=submission.source,
        enrollment_id=enrollment.id,
        attempt_datetime=datetime.now(),
    )
    # Calculate the attempt number before committing
    new_quiz_completion.attempt_no = new_quiz_completion.calculate_attempt_no(db)

    db.add(new_quiz_completion)
    db.commit()

    return new_quiz_completion
