from typing import List, Optional

from pydantic import BaseModel, EmailStr


# =========================================================
# AUTHENTICATION
# =========================================================

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


# =========================================================
# RUBRIC / CUSTOM RULES
# =========================================================

class RubricPointCreate(BaseModel):
    description: str
    marks: float


class CustomRuleCreate(BaseModel):
    type: str
    description: str
    marks: Optional[float] = None


# =========================================================
# QUESTIONS
# =========================================================

class QuestionCreate(BaseModel):
    question: str
    marks: float

    expected_answer: Optional[str] = None

    evaluation_method: str

    rubric_points: List[RubricPointCreate] = []

    custom_rules: List[CustomRuleCreate] = []


# =========================================================
# STUDENT ANSWERS
# =========================================================

class StudentAnswerCreate(BaseModel):
    question_index: int
    answer: str


class StudentCreate(BaseModel):
    student_id: str

    name: Optional[str] = None

    answers: List[StudentAnswerCreate]


# =========================================================
# EVALUATION
# =========================================================

class EvaluationCreate(BaseModel):
    title: str

    course: Optional[str] = None

    total_marks: float

    questions: List[QuestionCreate]

    students: List[StudentCreate]

    overall_custom_rules: List[
        CustomRuleCreate
    ] = []

    extensions: List[str] = []


class EvaluationResponse(BaseModel):
    id: int

    title: str

    course: Optional[str]

    total_marks: float

    status: str

    class Config:
        from_attributes = True