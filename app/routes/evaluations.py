import json
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Evaluation,
    Question,
    Student,
    StudentAnswer,
)
from app.schemas import (
    EvaluationCreate,
    EvaluationResponse,
)
from app.auth import get_current_user
from app.services.evaluation_service import (
    evaluate_assignment,
    evaluate_student,
    get_groq_client,
    get_question_marks,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"],
)


# ============================================================
# CREATE EVALUATION
# ============================================================

@router.post(
    "",
    response_model=EvaluationResponse,
)
def create_evaluation(
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        evaluation = Evaluation(
            user_id=current_user.id,
            title=data.title,
            course=data.course,
            total_marks=data.total_marks,
            status="Pending",
        )

        db.add(evaluation)
        db.flush()

        # ====================================================
        # QUESTIONS
        # ====================================================

        for question_data in data.questions:

            question = Question(
                evaluation_id=evaluation.id,
                question_text=question_data.question,
                marks=question_data.marks,
                expected_answer=question_data.expected_answer,
                evaluation_method=(
                    question_data.evaluation_method
                ),
            )

            db.add(question)
            db.flush()

        # ====================================================
        # STUDENTS
        # ====================================================

        for student_data in data.students:

            student = Student(
                evaluation_id=evaluation.id,
                student_id=student_data.student_id,
                name=student_data.name,
            )

            db.add(student)
            db.flush()

            # =================================================
            # STUDENT ANSWERS
            # =================================================

            for answer_data in student_data.answers:

                if (
                    answer_data.question_index < 0
                    or answer_data.question_index
                    >= len(data.questions)
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Invalid question index: "
                            f"{answer_data.question_index}"
                        ),
                    )

                question = evaluation.questions[
                    answer_data.question_index
                ]

                answer = StudentAnswer(
                    student_id=student.id,
                    question_id=question.id,
                    answer_text=answer_data.answer,
                )

                db.add(answer)

        db.commit()
        db.refresh(evaluation)

        return evaluation

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:

        db.rollback()

        print()
        print("=" * 80)
        print("CREATE EVALUATION ERROR")
        print("=" * 80)
        print(str(error))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# LIST EVALUATIONS
# ============================================================

@router.get("")
def get_evaluations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    evaluations = (
        db.query(Evaluation)
        .filter(
            Evaluation.user_id
            == current_user.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .all()
    )

    result = []

    for evaluation in evaluations:

        result.append(
            {
                "id": evaluation.id,
                "title": evaluation.title,
                "course": evaluation.course,
                "total_marks": evaluation.total_marks,
                "status": evaluation.status,
                "created_at": (
                    evaluation.created_at
                ),
                "students": len(
                    evaluation.students
                ),
                "questions": len(
                    evaluation.questions
                ),
            }
        )

    return result


# ============================================================
# GET SINGLE EVALUATION
# ============================================================

@router.get("/{evaluation_id}")
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    evaluation = (
        db.query(Evaluation)
        .filter(
            Evaluation.id
            == evaluation_id,
            Evaluation.user_id
            == current_user.id,
        )
        .first()
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    questions = []

    for question in evaluation.questions:

        questions.append(
            {
                "id": question.id,
                "question": (
                    question.question_text
                ),
                "marks": question.marks,
                "expected_answer": (
                    question.expected_answer
                ),
                "evaluation_method": (
                    question.evaluation_method
                ),
            }
        )

    students = []

    for student in evaluation.students:

        answers = []

        for answer in student.answers:

            answers.append(
                {
                    "id": answer.id,
                    "question_id": (
                        answer.question_id
                    ),
                    "answer": (
                        answer.answer_text
                    ),
                }
            )

        students.append(
            {
                "id": student.id,
                "student_id": (
                    student.student_id
                ),
                "name": student.name,
                "answers": answers,
            }
        )

    return {
        "id": evaluation.id,
        "title": evaluation.title,
        "course": evaluation.course,
        "total_marks": evaluation.total_marks,
        "status": evaluation.status,
        "created_at": evaluation.created_at,
        "questions": questions,
        "students": students,
    }


# ============================================================
# EVALUATE COMPLETE ASSIGNMENT
# ============================================================

@router.post(
    "/{evaluation_id}/evaluate"
)
def evaluate_full_assignment(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    evaluation = (
        db.query(Evaluation)
        .filter(
            Evaluation.id
            == evaluation_id,
            Evaluation.user_id
            == current_user.id,
        )
        .first()
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    try:

        evaluation.status = "Evaluating"
        db.commit()

        result = evaluate_assignment(
            evaluation
        )

        evaluation.status = "Completed"
        db.commit()

        return result

    except Exception as error:

        evaluation.status = "Failed"
        db.commit()

        print()
        print("=" * 80)
        print("FULL EVALUATION ERROR")
        print("=" * 80)
        print(str(error))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# STREAM EVALUATION
# ============================================================

@router.post(
    "/{evaluation_id}/evaluate-stream"
)
def evaluate_stream(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    evaluation = (
        db.query(Evaluation)
        .filter(
            Evaluation.id
            == evaluation_id,
            Evaluation.user_id
            == current_user.id,
        )
        .first()
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    evaluation.status = "Evaluating"
    db.commit()

    evaluation_id_value = evaluation.id

    # --------------------------------------------------------
    # Capture IDs/data before generator starts
    # --------------------------------------------------------

    question_list = list(
        evaluation.questions
    )

    student_list = list(
        evaluation.students
    )

    def event(
        event_type: str,
        data: dict,
    ) -> str:

        payload = {
            "type": event_type,
            **data,
        }

        return (
            json.dumps(
                payload,
                ensure_ascii=False,
            )
            + "\n"
        )

    def generate() -> Generator[
        str,
        None,
        None
    ]:

        print()
        print("#" * 80)
        print(
            "PAPERMARK AI — STREAM EVALUATION"
        )
        print(
            f"Evaluation ID: "
            f"{evaluation_id_value}"
        )
        print(
            f"Students: "
            f"{len(student_list)}"
        )
        print(
            f"Questions: "
            f"{len(question_list)}"
        )
        print("#" * 80)

        yield event(
            "start",
            {
                "evaluation_id": (
                    evaluation_id_value
                ),
                "total_students": (
                    len(student_list)
                ),
                "total_questions": (
                    len(question_list)
                ),
            },
        )

        try:

            client = get_groq_client()

            all_results = []

            # =================================================
            # STUDENT BY STUDENT
            # =================================================

            for student_index, student in enumerate(
                student_list
            ):

                student_identifier = (
                    student.student_id
                )

                print()
                print("=" * 80)
                print(
                    f"START STUDENT "
                    f"{student_index + 1}/"
                    f"{len(student_list)}: "
                    f"{student_identifier}"
                )
                print("=" * 80)

                yield event(
                    "student_start",
                    {
                        "student_id": (
                            student.id
                        ),
                        "student_identifier": (
                            student_identifier
                        ),
                        "student_name": (
                            student.name
                        ),
                        "index": (
                            student_index
                        ),
                        "total": (
                            len(student_list)
                        ),
                    },
                )

                try:

                    result = evaluate_student(
                        client=client,
                        student=student,
                        questions=question_list,
                        marking_rules={
                            "semanticMeaning": True,
                            "keywordCheck": False,
                            "formulaCheck": False,
                            "instructorReview": False,
                            "customRules": [],
                            "rubricPoints": [],
                        },
                    )

                    all_results.append(
                        result
                    )

                    yield event(
                        "student_complete",
                        {
                            "student_id": (
                                student.id
                            ),
                            "student_identifier": (
                                student_identifier
                            ),
                            "student_name": (
                                student.name
                            ),
                            "obtained_marks": (
                                result.get(
                                    "obtainedMarks",
                                    0,
                                )
                            ),
                            "total_marks": (
                                result.get(
                                    "totalMarks",
                                    0,
                                )
                            ),
                            "percentage": (
                                result.get(
                                    "percentage",
                                    0,
                                )
                            ),
                            "question_results": (
                                result.get(
                                    "questionResults",
                                    [],
                                )
                            ),
                            "index": (
                                student_index
                            ),
                            "total": (
                                len(student_list)
                            ),
                        },
                    )

                    print()
                    print(
                        f"✓ STUDENT COMPLETED: "
                        f"{student_identifier}"
                    )

                except Exception as student_error:

                    print()
                    print("!" * 80)
                    print(
                        f"STUDENT FAILED: "
                        f"{student_identifier}"
                    )
                    print(
                        str(student_error)
                    )
                    print("!" * 80)

                    yield event(
                        "student_error",
                        {
                            "student_id": (
                                student.id
                            ),
                            "student_identifier": (
                                student_identifier
                            ),
                            "student_name": (
                                student.name
                            ),
                            "error": str(
                                student_error
                            ),
                            "index": (
                                student_index
                            ),
                            "total": (
                                len(student_list)
                            ),
                        },
                    )

            # =================================================
            # FINAL RESULT
            # =================================================

            total_marks = sum(
                get_question_marks(
                    question
                )
                for question in question_list
            )

            average_percentage = 0.0

            if all_results:

                average_percentage = (
                    sum(
                        float(
                            result.get(
                                "percentage",
                                0,
                            )
                        )
                        for result in all_results
                    )
                    / len(all_results)
                )

            final_result = {
                "evaluationId": (
                    evaluation_id_value
                ),
                "evaluationTitle": (
                    evaluation.title
                ),
                "totalMarks": (
                    total_marks
                ),
                "students": (
                    all_results
                ),
                "averagePercentage": round(
                    average_percentage,
                    2,
                ),
            }

            # -------------------------------------------------
            # Mark evaluation complete
            # -------------------------------------------------

            try:

                local_db = next(
                    get_db()
                )

                try:

                    local_evaluation = (
                        local_db.query(
                            Evaluation
                        )
                        .filter(
                            Evaluation.id
                            == evaluation_id_value
                        )
                        .first()
                    )

                    if local_evaluation:

                        local_evaluation.status = (
                            "Completed"
                        )

                        local_db.commit()

                finally:

                    local_db.close()

            except Exception as status_error:

                print(
                    "Could not update "
                    f"evaluation status: "
                    f"{status_error}"
                )

            yield event(
                "complete",
                {
                    "evaluation_id": (
                        evaluation_id_value
                    ),
                    "result": (
                        final_result
                    ),
                },
            )

            print()
            print("#" * 80)
            print(
                "PAPERMARK AI — "
                "STREAM EVALUATION COMPLETED"
            )
            print("#" * 80)

        except Exception as error:

            print()
            print("!" * 80)
            print(
                "STREAM EVALUATION FAILED"
            )
            print(
                str(error)
            )
            print("!" * 80)

            # Update status.
            try:

                local_db = next(
                    get_db()
                )

                try:

                    local_evaluation = (
                        local_db.query(
                            Evaluation
                        )
                        .filter(
                            Evaluation.id
                            == evaluation_id_value
                        )
                        .first()
                    )

                    if local_evaluation:

                        local_evaluation.status = (
                            "Failed"
                        )

                        local_db.commit()

                finally:

                    local_db.close()

            except Exception:
                pass

            yield event(
                "student_error",
                {
                    "student_id": None,
                    "student_identifier": None,
                    "error": str(error),
                },
            )

    return StreamingResponse(
        generate(),
        media_type=(
            "application/x-ndjson"
        ),
    )


# ============================================================
# STUDENT RESULT
# ============================================================

@router.get(
    "/{evaluation_id}/students/"
    "{student_id}/result"
)
def get_student_result(
    evaluation_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    evaluation = (
        db.query(Evaluation)
        .filter(
            Evaluation.id
            == evaluation_id,
            Evaluation.user_id
            == current_user.id,
        )
        .first()
    )

    if not evaluation:

        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.evaluation_id
            == evaluation.id,
        )
        .first()
    )

    if not student:

        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    try:

        client = get_groq_client()

        result = evaluate_student(
            client=client,
            student=student,
            questions=list(
                evaluation.questions
            ),
            marking_rules={
                "semanticMeaning": True,
                "keywordCheck": False,
                "formulaCheck": False,
                "instructorReview": False,
                "customRules": [],
                "rubricPoints": [],
            },
        )

        # ====================================================
        # FRONTEND-FRIENDLY RESPONSE
        # ====================================================

        question_results = []

        for item in result.get(
            "questionResults",
            [],
        ):

            question_results.append(
                {
                    "id": item.get(
                        "questionId"
                    ),
                    "question": item.get(
                        "question",
                        "",
                    ),
                    "expected_answer": item.get(
                        "expectedAnswer",
                        "",
                    ),
                    "student_answer": item.get(
                        "studentAnswer",
                        "",
                    ),
                    "max_marks": item.get(
                        "maxMarks",
                        0,
                    ),
                    "marks_awarded": item.get(
                        "marksAwarded",
                        0,
                    ),
                    "match_percentage": item.get(
                        "matchPercentage",
                        0,
                    ),
                    "matched_concepts": item.get(
                        "matchedConcepts",
                        [],
                    ),
                    "missing_concepts": item.get(
                        "missingConcepts",
                        [],
                    ),
                    "incorrect_concepts": item.get(
                        "incorrectConcepts",
                        [],
                    ),
                    "what_should_have_been_included": (
                        item.get(
                            "whatShouldHaveBeenIncluded",
                            [],
                        )
                    ),
                    "what_was_missing": (
                        item.get(
                            "whatWasMissing",
                            [],
                        )
                    ),
                    "what_was_incorrect": (
                        item.get(
                            "whatWasIncorrect",
                            [],
                        )
                    ),
                    "what_was_done_well": (
                        item.get(
                            "whatWasDoneWell",
                            [],
                        )
                    ),
                    "positive_comment": (
                        item.get(
                            "positiveComment",
                            "",
                        )
                    ),
                    "feedback": item.get(
                        "feedback",
                        "",
                    ),
                }
            )

        return {
            "evaluation": {
                "id": evaluation.id,
                "title": evaluation.title,
            },
            "student": {
                "id": student.id,
                "student_id": (
                    student.student_id
                ),
                "name": student.name,
            },
            "result": {
                "obtained_marks": (
                    result.get(
                        "obtainedMarks",
                        0,
                    )
                ),
                "total_marks": (
                    result.get(
                        "totalMarks",
                        evaluation.total_marks,
                    )
                ),
                "percentage": (
                    result.get(
                        "percentage",
                        0,
                    )
                ),
                "question_results": (
                    question_results
                ),
            },
        }

    except Exception as error:

        print()
        print("=" * 80)
        print(
            "STUDENT RESULT ERROR"
        )
        print("=" * 80)
        print(str(error))
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )