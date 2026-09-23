from typing import List, Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    question: str
    marks: float
    expected_answer: Optional[str] = None
    evaluation_method: str


class StudentAnswerCreate(BaseModel):
    question_id: int
    answer: str


class StudentCreate(BaseModel):
    student_id: str
    name: Optional[str] = None
    answers: List[StudentAnswerCreate]


class EvaluationCreate(BaseModel):
    title: str
    course: Optional[str] = None
    total_marks: float
    questions: List[QuestionCreate]
    students: List[StudentCreate]


class EvaluationResponse(BaseModel):
    id: int
    title: str
    course: Optional[str]
    total_marks: float
    status: str

    class Config:
        from_attributes = True