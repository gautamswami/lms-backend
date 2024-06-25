from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Questions
from schemas import QuestionDisplay, QuestionCreate, QuestionUpdate, QuestionGetRequest

from typing import List, Optional
from fastapi import Query

app = APIRouter(tags=["course", "quiz"])


@app.post("/courses/{course_id}/question/", response_model=QuestionDisplay)
def add_quiz_question_to_course(
    course_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)
):
    new_question = Questions(course_id=course_id, **quiz_data.dict())
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


# Endpoint to add quiz questions to a course using bulk insert
@app.post("/courses/{course_id}/questions", response_model=List[dict])
def add_quiz_questions_to_course(
    course_id: int, quiz_data: List[QuestionCreate], db: Session = Depends(get_db)
):
    try:
        questions_to_add = []
        for q_data in quiz_data:
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

        db.execute(Questions.__table__.insert(), questions_to_add)
        db.commit()

        return [
            {"id": question_id, **q_data.dict()}
            for question_id, q_data in zip(range(len(questions_to_add)), quiz_data)
        ]

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chapters/{chapter_id}/question", response_model=QuestionDisplay)
def add_quiz_question_to_chapter(
    chapter_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)
):
    new_question = Questions(chapter_id=chapter_id, **quiz_data.dict())
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


# Endpoint to add quiz questions to a chapter using bulk insert
@app.post("/chapters/{chapter_id}/questions", response_model=List[dict])
def add_quiz_questions_to_chapter(
    chapter_id: int, quiz_data: List[QuestionCreate], db: Session = Depends(get_db)
):
    try:
        questions_to_add = []
        for q_data in quiz_data:
            new_question = {
                "chapter_id": chapter_id,
                "question": q_data.question,
                "option_a": q_data.option_a,
                "option_b": q_data.option_b,
                "option_c": q_data.option_c,
                "option_d": q_data.option_d,
                "correct_answer": q_data.correct_answer,
            }
            questions_to_add.append(new_question)

        db.execute(Questions.__table__.insert(), questions_to_add)
        db.commit()

        return [
            {"id": question_id, **q_data.dict()}
            for question_id, q_data in zip(range(len(questions_to_add)), quiz_data)
        ]

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
