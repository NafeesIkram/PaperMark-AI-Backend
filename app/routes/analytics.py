from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Evaluation


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ============================================================
# ANALYTICS
# ============================================================

@router.get("")
def get_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Account-level analytics.

    IMPORTANT:
    The current database's evaluation_results table stores
    question-level evaluation data:

        id
        student_id
        question_id
        marks_awarded
        coverage
        feedback
        created_at
        evaluation_id

    Therefore we DO NOT use:

        student.result

    because the SQLAlchemy EvaluationResult model represents
    a different student-summary structure.

    Instead, analytics calculates student scores directly
    from the actual evaluation_results table.
    """

    # ========================================================
    # 1. GET CURRENT USER'S EVALUATIONS
    # ========================================================

    evaluations = (
        db.query(Evaluation)
        .filter(
            Evaluation.user_id == current_user.id
        )
        .all()
    )

    total_evaluations = len(evaluations)

    evaluation_ids = [
        evaluation.id
        for evaluation in evaluations
    ]

    # ========================================================
    # EMPTY WORKSPACE
    # ========================================================

    if not evaluation_ids:
        return {
            "evaluations": 0,
            "students": 0,
            "submissions": 0,
            "evaluated": 0,
            "average_score": 0.0,
            "performance": [
                {
                    "label": "Evaluation Completion",
                    "value": 0,
                },
                {
                    "label": "Submission Coverage",
                    "value": 0,
                },
                {
                    "label": "Evaluated Scripts",
                    "value": 0,
                },
                {
                    "label": "Average Score",
                    "value": 0,
                },
            ],
            "distribution": [
                {
                    "label": "90–100",
                    "value": 0,
                    "percentage": 0,
                },
                {
                    "label": "80–89",
                    "value": 0,
                    "percentage": 0,
                },
                {
                    "label": "70–79",
                    "value": 0,
                    "percentage": 0,
                },
                {
                    "label": "60–69",
                    "value": 0,
                    "percentage": 0,
                },
                {
                    "label": "Below 60",
                    "value": 0,
                    "percentage": 0,
                },
            ],
        }

    # ========================================================
    # 2. COMPLETED EVALUATIONS
    # ========================================================

    completed_evaluations = sum(
        1
        for evaluation in evaluations
        if evaluation.status
        and evaluation.status.lower() == "completed"
    )

    # ========================================================
    # 3. TOTAL STUDENTS / SUBMISSIONS
    #
    # Each Student record represents one submission inside
    # an evaluation.
    # ========================================================

    total_submissions = sum(
        len(evaluation.students)
        for evaluation in evaluations
    )

    # Student IDs can technically appear in multiple
    # evaluations, so count unique student identifiers here.
    unique_student_identifiers = set()

    for evaluation in evaluations:
        for student in evaluation.students:

            identifier = (
                str(student.student_id).strip()
                if student.student_id is not None
                else ""
            )

            if identifier:
                unique_student_identifiers.add(
                    identifier
                )

    total_students = len(
        unique_student_identifiers
    )

    # ========================================================
    # 4. READ ACTUAL QUESTION-LEVEL RESULTS
    #
    # We intentionally use raw SQL here because the current
    # Supabase table structure does NOT contain:
    #
    # total_marks
    # obtained_marks
    # percentage
    #
    # Instead it contains:
    #
    # marks_awarded
    # question_id
    # student_id
    # evaluation_id
    # ========================================================

    placeholders = ", ".join(
        f":evaluation_id_{index}"
        for index in range(
            len(evaluation_ids)
        )
    )

    params = {
        f"evaluation_id_{index}": evaluation_id
        for index, evaluation_id in enumerate(
            evaluation_ids
        )
    }

    result_query = text(
        f"""
        SELECT
            er.evaluation_id,
            er.student_id,
            er.question_id,
            er.marks_awarded,
            q.marks AS max_marks
        FROM evaluation_results er
        LEFT JOIN questions q
            ON q.id = er.question_id
        WHERE er.evaluation_id IN ({placeholders})
        ORDER BY
            er.evaluation_id,
            er.student_id,
            er.question_id
        """
    )

    result_rows = (
        db.execute(
            result_query,
            params,
        )
        .mappings()
        .all()
    )

    # ========================================================
    # 5. BUILD STUDENT-WISE RESULTS
    # ========================================================

    student_scores = {}

    for row in result_rows:

        evaluation_id = row[
            "evaluation_id"
        ]

        student_id = row[
            "student_id"
        ]

        key = (
            int(evaluation_id),
            int(student_id),
        )

        if key not in student_scores:
            student_scores[key] = {
                "obtained_marks": 0.0,
                "total_marks": 0.0,
                "questions": 0,
            }

        # ----------------------------------------------------
        # MARKS AWARDED
        # ----------------------------------------------------

        marks_awarded = row[
            "marks_awarded"
        ]

        try:
            marks_awarded = float(
                marks_awarded or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            marks_awarded = 0.0

        student_scores[key][
            "obtained_marks"
        ] += marks_awarded

        # ----------------------------------------------------
        # MAXIMUM QUESTION MARKS
        # ----------------------------------------------------

        max_marks = row[
            "max_marks"
        ]

        try:
            max_marks = float(
                max_marks or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            max_marks = 0.0

        student_scores[key][
            "total_marks"
        ] += max_marks

        student_scores[key][
            "questions"
        ] += 1

    # ========================================================
    # 6. CALCULATE PERCENTAGES
    # ========================================================

    evaluated_student_results = []

    for key, data in student_scores.items():

        total_marks = float(
            data["total_marks"]
        )

        obtained_marks = float(
            data["obtained_marks"]
        )

        if total_marks > 0:

            percentage = (
                obtained_marks
                / total_marks
            ) * 100

        else:
            percentage = 0.0

        percentage = max(
            0.0,
            min(
                100.0,
                percentage,
            ),
        )

        evaluated_student_results.append(
            {
                "evaluation_id": key[0],
                "student_id": key[1],
                "obtained_marks": round(
                    obtained_marks,
                    2,
                ),
                "total_marks": round(
                    total_marks,
                    2,
                ),
                "percentage": round(
                    percentage,
                    2,
                ),
            }
        )

    # ========================================================
    # 7. EVALUATED COUNT
    # ========================================================

    evaluated_count = len(
        evaluated_student_results
    )

    # ========================================================
    # 8. AVERAGE SCORE
    # ========================================================

    percentages = [
        item["percentage"]
        for item in evaluated_student_results
    ]

    if percentages:

        average_score = round(
            sum(percentages)
            / len(percentages),
            2,
        )

    else:

        average_score = 0.0

    # ========================================================
    # 9. EVALUATION COMPLETION
    # ========================================================

    if total_evaluations > 0:

        evaluation_completion = round(
            (
                completed_evaluations
                / total_evaluations
            )
            * 100,
            2,
        )

    else:

        evaluation_completion = 0.0

    # ========================================================
    # 10. SUBMISSION COVERAGE
    # ========================================================

    if total_submissions > 0:

        submission_coverage = round(
            (
                evaluated_count
                / total_submissions
            )
            * 100,
            2,
        )

    else:

        submission_coverage = 0.0

    # ========================================================
    # 11. SCORE DISTRIBUTION
    # ========================================================

    distribution = [
        {
            "label": "90–100",
            "value": 0,
            "percentage": 0,
        },
        {
            "label": "80–89",
            "value": 0,
            "percentage": 0,
        },
        {
            "label": "70–79",
            "value": 0,
            "percentage": 0,
        },
        {
            "label": "60–69",
            "value": 0,
            "percentage": 0,
        },
        {
            "label": "Below 60",
            "value": 0,
            "percentage": 0,
        },
    ]

    # ========================================================
    # PUT STUDENTS INTO SCORE RANGES
    # ========================================================

    for score in percentages:

        if score >= 90:

            distribution[0]["value"] += 1

        elif score >= 80:

            distribution[1]["value"] += 1

        elif score >= 70:

            distribution[2]["value"] += 1

        elif score >= 60:

            distribution[3]["value"] += 1

        else:

            distribution[4]["value"] += 1

    # ========================================================
    # DISTRIBUTION PERCENTAGES
    # ========================================================

    if evaluated_count > 0:

        for item in distribution:

            item["percentage"] = round(
                (
                    item["value"]
                    / evaluated_count
                )
                * 100,
                2,
            )

    # ========================================================
    # 12. RESPONSE
    # ========================================================

    return {
        "evaluations": total_evaluations,

        # Number of unique student IDs
        "students": total_students,

        # Number of student submissions across evaluations
        "submissions": total_submissions,

        # Number of evaluated student submissions
        "evaluated": evaluated_count,

        "average_score": average_score,

        "performance": [
            {
                "label": "Evaluation Completion",
                "value": evaluation_completion,
            },
            {
                "label": "Submission Coverage",
                "value": submission_coverage,
            },
            {
                "label": "Evaluated Scripts",
                "value": (
                    round(
                        (
                            evaluated_count
                            / total_submissions
                        )
                        * 100,
                        2,
                    )
                    if total_submissions
                    else 0
                ),
            },
            {
                "label": "Average Score",
                "value": average_score,
            },
        ],

        "distribution": distribution,
    }