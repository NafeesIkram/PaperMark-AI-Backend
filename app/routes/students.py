from collections import OrderedDict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Evaluation


router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


# ============================================================
# GET STUDENTS
# ============================================================

@router.get("")
def get_students(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get students belonging only to the currently
    logged-in instructor.

    Students are connected to evaluations.
    Evaluations are connected to the instructor/user.
    Therefore we collect students from the current
    user's evaluations.
    """

    evaluations = (
        db.query(Evaluation)
        .filter(
            Evaluation.user_id == current_user.id
        )
        .order_by(
            Evaluation.id.desc()
        )
        .all()
    )

    students_map = OrderedDict()

    for evaluation in evaluations:

        for student in evaluation.students:

            student_key = (
                student.student_id.strip()
            )

            # ------------------------------------------------
            # Create student entry if not already present
            # ------------------------------------------------

            if student_key not in students_map:

                students_map[student_key] = {
                    "id": student.id,
                    "student_id": student.student_id,
                    "name": student.name,
                    "submissions": 0,
                    "evaluated": 0,
                    "status": "Active",
                }

            # ------------------------------------------------
            # Every occurrence means one submission
            # ------------------------------------------------

            students_map[
                student_key
            ]["submissions"] += 1

            # ------------------------------------------------
            # Result exists = evaluated
            # ------------------------------------------------

            if student.result is not None:

                students_map[
                    student_key
                ]["evaluated"] += 1

            # ------------------------------------------------
            # Keep available student name
            # ------------------------------------------------

            if (
                not students_map[
                    student_key
                ]["name"]
                and student.name
            ):

                students_map[
                    student_key
                ]["name"] = student.name

    return list(
        students_map.values()
    )