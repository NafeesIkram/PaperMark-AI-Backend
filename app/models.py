from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.database import Base


# =========================================================
# USER
# =========================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# =========================================================
# EVALUATION
# =========================================================

class Evaluation(Base):

    __tablename__ = "evaluations"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    course = Column(
        String(255),
        nullable=True,
    )

    total_marks = Column(
        Float,
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
        default="Processing",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="evaluations",
    )

    questions = relationship(
        "Question",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="Question.id",
    )

    students = relationship(
        "Student",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="Student.id",
    )

    overall_rules = relationship(
        "OverallMarkingRule",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="OverallMarkingRule.id",
    )

    extensions = relationship(
        "EvaluationExtension",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="EvaluationExtension.id",
    )

    results = relationship(
        "EvaluationResult",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.id",
    )


# =========================================================
# QUESTION
# =========================================================

class Question(Base):

    __tablename__ = "questions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey(
            "evaluations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_text = Column(
        Text,
        nullable=False,
    )

    marks = Column(
        Float,
        nullable=False,
    )

    expected_answer = Column(
        Text,
        nullable=True,
    )

    evaluation_method = Column(
        String(50),
        nullable=False,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="questions",
    )

    answers = relationship(
        "StudentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    rubric_points = relationship(
        "RubricPoint",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="RubricPoint.id",
    )

    custom_rules = relationship(
        "QuestionCustomRule",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionCustomRule.id",
    )

    result_details = relationship(
        "QuestionResult",
        back_populates="question",
        cascade="all, delete-orphan",
    )


# =========================================================
# RUBRIC POINT
# =========================================================

class RubricPoint(Base):

    __tablename__ = "rubric_points"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    question_id = Column(
        Integer,
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=False,
    )

    marks = Column(
        Float,
        nullable=False,
    )

    question = relationship(
        "Question",
        back_populates="rubric_points",
    )


# =========================================================
# QUESTION CUSTOM MARKING RULE
# =========================================================

class QuestionCustomRule(Base):

    __tablename__ = "question_custom_rules"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    question_id = Column(
        Integer,
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    type = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    marks = Column(
        Float,
        nullable=True,
    )

    question = relationship(
        "Question",
        back_populates="custom_rules",
    )


# =========================================================
# OVERALL CUSTOM MARKING RULE
# =========================================================

class OverallMarkingRule(Base):

    __tablename__ = "overall_marking_rules"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey(
            "evaluations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    type = Column(
        String(100),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    marks = Column(
        Float,
        nullable=True,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="overall_rules",
    )


# =========================================================
# EVALUATION EXTENSION
# =========================================================

class EvaluationExtension(Base):

    __tablename__ = "evaluation_extensions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey(
            "evaluations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    extension_key = Column(
        String(100),
        nullable=False,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="extensions",
    )


# =========================================================
# STUDENT
# =========================================================

class Student(Base):

    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey(
            "evaluations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    student_id = Column(
        String(100),
        nullable=False,
    )

    name = Column(
        String(255),
        nullable=True,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="students",
    )

    answers = relationship(
        "StudentAnswer",
        back_populates="student",
        cascade="all, delete-orphan",
        order_by="StudentAnswer.question_id",
    )

    result = relationship(
        "EvaluationResult",
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
    )


# =========================================================
# STUDENT ANSWER
# =========================================================

class StudentAnswer(Base):

    __tablename__ = "student_answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    student_id = Column(
        Integer,
        ForeignKey(
            "students.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id = Column(
        Integer,
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    answer_text = Column(
        Text,
        nullable=False,
    )

    student = relationship(
        "Student",
        back_populates="answers",
    )

    question = relationship(
        "Question",
        back_populates="answers",
    )


# =========================================================
# EVALUATION RESULT
# =========================================================

class EvaluationResult(Base):

    __tablename__ = "evaluation_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_id = Column(
        Integer,
        ForeignKey(
            "evaluations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    student_id = Column(
        Integer,
        ForeignKey(
            "students.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    total_marks = Column(
        Float,
        nullable=False,
    )

    obtained_marks = Column(
        Float,
        nullable=False,
    )

    percentage = Column(
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="results",
    )

    student = relationship(
        "Student",
        back_populates="result",
    )

    question_results = relationship(
        "QuestionResult",
        back_populates="evaluation_result",
        cascade="all, delete-orphan",
        order_by="QuestionResult.id",
    )


# =========================================================
# QUESTION RESULT
# =========================================================

class QuestionResult(Base):

    __tablename__ = "question_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_result_id = Column(
        Integer,
        ForeignKey(
            "evaluation_results.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id = Column(
        Integer,
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    student_answer = Column(
        Text,
        nullable=False,
    )

    max_marks = Column(
        Float,
        nullable=False,
    )

    marks_awarded = Column(
        Float,
        nullable=False,
    )

    match_percentage = Column(
        Float,
        nullable=False,
    )

    evaluation_method = Column(
        String(50),
        nullable=False,
    )

    matched_concepts = Column(
        Text,
        nullable=True,
    )

    missing_concepts = Column(
        Text,
        nullable=True,
    )

    incorrect_concepts = Column(
        Text,
        nullable=True,
    )

    feedback = Column(
        Text,
        nullable=True,
    )

    evaluation_result = relationship(
        "EvaluationResult",
        back_populates="question_results",
    )

    question = relationship(
        "Question",
        back_populates="result_details",
    )