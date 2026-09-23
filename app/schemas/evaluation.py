from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

class RubricPoint(BaseModel):
    description: str = Field(min_length=1)
    marks: float = Field(ge=0)

class CustomRule(BaseModel):
    type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    marks: float = 0

class MarkingRules(BaseModel):
    semanticMeaning: bool = True
    keywordCheck: bool = True
    formulaCheck: bool = True
    instructorReview: bool = True
    customRules: List[CustomRule] = Field(default_factory=list)

class Question(BaseModel):
    id: int
    question: str = Field(min_length=1)
    marks: float = Field(gt=0)
    answer: str = ""
    evaluationMethod: str = "semantic"
    rubricPoints: List[RubricPoint] = Field(default_factory=list)

    @field_validator("evaluationMethod")
    @classmethod
    def validate_method(cls, value: str) -> str:
        if value not in {"semantic", "exact", "rubric"}:
            raise ValueError("evaluationMethod must be semantic, exact, or rubric")
        return value

class Student(BaseModel):
    studentId: str = Field(min_length=1)
    studentName: Optional[str] = ""
    answers: Dict[str, str] = Field(default_factory=dict)

class EvaluationRequest(BaseModel):
    title: str = Field(min_length=1)
    course: Optional[str] = ""
    totalMarks: float = Field(gt=0)
    questions: List[Question] = Field(min_length=1)
    markingRules: MarkingRules = Field(default_factory=MarkingRules)
    students: List[Student] = Field(min_length=1)
    customApiKey: Optional[str] = None
    model: str = "gemini-2.5-flash"

class QuestionEvaluation(BaseModel):
    questionId: int
    question: str
    maxMarks: float
    marksAwarded: float
    matchPercentage: float
    evaluationMethod: str
    matchedConcepts: List[str] = Field(default_factory=list)
    missingConcepts: List[str] = Field(default_factory=list)
    incorrectConcepts: List[str] = Field(default_factory=list)
    feedback: str

class StudentEvaluation(BaseModel):
    studentId: str
    studentName: str
    totalMarks: float
    obtainedMarks: float
    percentage: float
    questionResults: List[QuestionEvaluation]

class EvaluationResponse(BaseModel):
    evaluationTitle: str
    totalMarks: float
    students: List[StudentEvaluation]
