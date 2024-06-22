from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dependencies import get_db
from models import Questions
from schemas import QuestionDisplay, QuestionCreate, QuestionUpdate

from typing import List, Optional
from fastapi import Query

app = APIRouter(tags=['course', 'quiz'])


@app.post("/courses/{course_id}/question/", response_model=QuestionDisplay)
def add_quiz_question_to_course(course_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)):
    new_question = Questions(
        course_id=course_id,
        **quiz_data.dict()
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


@app.post("/chapters/{chapter_id}/question", response_model=QuestionDisplay)
def add_quiz_question_to_chapter(chapter_id: int, quiz_data: QuestionCreate, db: Session = Depends(get_db)):
    new_question = Questions(
        chapter_id=chapter_id,
        **quiz_data.dict()
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return QuestionDisplay(**quiz_data.dict(), id=new_question.id)


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
def update_question(question_id: int, question_data: QuestionUpdate, db: Session = Depends(get_db)):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    for var, value in vars(question_data).items():
        if value is not None:
            setattr(question, var, value)

    db.commit()
    return question


@app.get("/questions", response_model=List[QuestionDisplay])
def get_questions_by_course_or_chapter(course_id: Optional[int] = Query(None), chapter_id: Optional[int] = Query(None),
                                       db: Session = Depends(get_db)):
    query = db.query(Questions)
    if course_id is not None:
        query = query.filter(Questions.course_id == course_id)
    if chapter_id is not None:
        query = query.filter(Questions.chapter_id == chapter_id)

    questions = query.all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for the specified course or chapter")
    return questions


@app.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Questions).filter(Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}