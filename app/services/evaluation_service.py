import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.replace("%", "").strip()

        return float(value)

    except (TypeError, ValueError):
        return default


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def get_field(
    obj: Any,
    field: str,
    default: Any = None,
) -> Any:

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def ensure_list(
    value: Any,
) -> List[str]:

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        return [value]

    return [str(value).strip()]


# ============================================================
# QUESTION HELPERS
# ============================================================

def get_question_marks(
    question: Any,
) -> float:
    """
    Return maximum marks for a question.
    """

    return safe_float(
        get_field(
            question,
            "marks",
            0,
        )
    )


def get_question_text(
    question: Any,
) -> str:

    return str(
        get_field(
            question,
            "question_text",
            get_field(
                question,
                "question",
                "",
            ),
        )
        or ""
    )


def get_expected_answer(
    question: Any,
) -> str:

    return str(
        get_field(
            question,
            "expected_answer",
            "",
        )
        or ""
    )


def get_evaluation_method(
    question: Any,
) -> str:

    return str(
        get_field(
            question,
            "evaluation_method",
            "semantic",
        )
        or "semantic"
    ).lower()


def get_rubric_points(
    question: Any,
) -> List[Any]:

    points = get_field(
        question,
        "rubric_points",
        [],
    )

    if points is None:
        return []

    try:
        return list(points)
    except TypeError:
        return []


def get_custom_rules(
    question: Any,
) -> List[Any]:

    rules = get_field(
        question,
        "custom_rules",
        [],
    )

    if rules is None:
        return []

    try:
        return list(rules)
    except TypeError:
        return []


# ============================================================
# DEBUG / TERMINAL LOGGING
# ============================================================

def debug_prompt(
    student_id: Any,
    question_number: int,
    prompt: str,
):

    print()
    print("=" * 90)
    print(
        f"PROMPT SENT TO GROQ | "
        f"Student: {student_id} | "
        f"Question: {question_number}"
    )
    print("=" * 90)
    print(prompt)
    print("=" * 90)


def debug_response(
    student_id: Any,
    question_number: int,
    response: str,
):

    print()
    print("=" * 90)
    print(
        f"RAW GROQ RESPONSE | "
        f"Student: {student_id} | "
        f"Question: {question_number}"
    )
    print("=" * 90)
    print(response)
    print("=" * 90)


def debug_error(
    student_id: Any,
    question_number: int,
    error: Exception,
):

    print()
    print("!" * 90)
    print(
        f"AI EVALUATION ERROR | "
        f"Student: {student_id} | "
        f"Question: {question_number}"
    )
    print("-" * 90)
    print(str(error))
    print("!" * 90)


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client() -> Groq:

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Please add GROQ_API_KEY to the backend .env file."
        )

    return Groq(
        api_key=api_key
    )


# ============================================================
# JSON PARSER
# ============================================================

def extract_json(
    text: str,
) -> Dict[str, Any]:

    if not text:
        raise ValueError(
            "Groq returned an empty response."
        )

    text = text.strip()

    # Remove markdown fences if model returns them.
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    # Direct JSON
    try:

        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # Extract JSON object from surrounding text.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        candidate = text[
            start:end + 1
        ]

        try:

            result = json.loads(
                candidate
            )

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Could not parse Groq response as valid JSON."
    )


# ============================================================
# RUBRIC FORMATTER
# ============================================================

def build_rubric_text(
    rubric_points: List[Any],
) -> str:

    if not rubric_points:
        return "No rubric points defined."

    lines = []

    for index, point in enumerate(
        rubric_points,
        start=1,
    ):

        description = str(
            get_field(
                point,
                "description",
                "",
            )
            or ""
        )

        marks = safe_float(
            get_field(
                point,
                "marks",
                0,
            )
        )

        lines.append(
            f"{index}. {description} "
            f"— {marks} marks"
        )

    return "\n".join(lines)


# ============================================================
# CUSTOM RULE FORMATTER
# ============================================================

def build_custom_rules_text(
    custom_rules: List[Any],
) -> str:

    if not custom_rules:
        return "No question-specific custom rules."

    lines = []

    for index, rule in enumerate(
        custom_rules,
        start=1,
    ):

        rule_type = str(
            get_field(
                rule,
                "type",
                "Custom",
            )
            or "Custom"
        )

        description = str(
            get_field(
                rule,
                "description",
                "",
            )
            or ""
        )

        marks = get_field(
            rule,
            "marks",
            None,
        )

        if marks is not None:

            lines.append(
                f"{index}. [{rule_type}] "
                f"{description} "
                f"(marks: {marks})"
            )

        else:

            lines.append(
                f"{index}. [{rule_type}] "
                f"{description}"
            )

    return "\n".join(lines)


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_question_prompt(
    question: Any,
    student_answer: str,
    marking_rules: Optional[
        Dict[str, Any]
    ] = None,
) -> str:

    marking_rules = (
        marking_rules or {}
    )

    question_text = (
        get_question_text(question)
    )

    expected_answer = (
        get_expected_answer(question)
    )

    max_marks = (
        get_question_marks(question)
    )

    evaluation_method = (
        get_evaluation_method(question)
    )

    rubric_points = (
        marking_rules.get(
            "rubricPoints"
        )
    )

    if not rubric_points:
        rubric_points = (
            get_rubric_points(question)
        )

    custom_rules = (
        marking_rules.get(
            "customRules"
        )
    )

    if not custom_rules:
        custom_rules = (
            get_custom_rules(question)
        )

    rubric_text = (
        build_rubric_text(
            rubric_points
        )
    )

    custom_rules_text = (
        build_custom_rules_text(
            custom_rules
        )
    )

    semantic_meaning = marking_rules.get(
        "semanticMeaning",
        True,
    )

    keyword_check = marking_rules.get(
        "keywordCheck",
        False,
    )

    formula_check = marking_rules.get(
        "formulaCheck",
        False,
    )

    instructor_review = marking_rules.get(
        "instructorReview",
        False,
    )

    prompt = f"""
You are PaperMark AI, an academic assignment
evaluation engine used by instructors.

Evaluate ONE student's answer against the instructor's
question and expected/model answer.

========================================================
QUESTION
========================================================

{question_text}

========================================================
MAXIMUM MARKS
========================================================

{max_marks}

========================================================
EXPECTED / MODEL ANSWER
========================================================

{expected_answer}

========================================================
STUDENT ANSWER
========================================================

{student_answer}

========================================================
EVALUATION METHOD
========================================================

{evaluation_method}

========================================================
MARKING PRINCIPLES
========================================================

The expected/model answer is the primary reference.

Evaluate conceptual and semantic correctness, not simply
word overlap.

Different wording is acceptable if the student expresses
the same correct meaning.

Do NOT require students to copy the model answer.

Do NOT award marks simply because keywords appear.

Do NOT penalize valid paraphrasing.

Do NOT invent requirements that are not supported by the
question, expected answer, rubric, or instructor rules.

Give partial marks when the student demonstrates genuine
partial understanding.

Never award more than the maximum marks.

Never award negative marks.

========================================================
SEMANTIC MEANING
========================================================

Semantic meaning evaluation:
{semantic_meaning}

Keyword checking:
{keyword_check}

Formula checking:
{formula_check}

Instructor review:
{instructor_review}

========================================================
POINT-BASED RUBRIC
========================================================

If the evaluation method is rubric, evaluate every rubric
point independently.

Award partial credit where appropriate.

Rubric:

{rubric_text}

========================================================
CUSTOM MARKING RULES
========================================================

Follow these instructor-defined rules when applicable.

{custom_rules_text}

========================================================
MATCH PERCENTAGE
========================================================

matchPercentage represents conceptual coverage of the
important information in the expected answer.

It is NOT word similarity.

It is NOT copied text percentage.

It is NOT sentence similarity.

========================================================
DETAILED FEEDBACK
========================================================

Identify:

1. What the student did correctly.
2. What important information should have been included.
3. What concepts were missing.
4. What concepts/statements were incorrect.
5. A useful instructor-facing feedback comment.

Do not invent errors.

If there are no errors, say so through the positive
comment and return an empty incorrectConcepts list.

If nothing important is missing, return an empty
missingConcepts list.

========================================================
OUTPUT FORMAT
========================================================

Return ONLY valid JSON.

Use exactly these fields:

{{
  "marksAwarded": 0,
  "matchPercentage": 0,
  "matchedConcepts": [],
  "missingConcepts": [],
  "incorrectConcepts": [],
  "whatShouldHaveBeenIncluded": [],
  "whatWasMissing": [],
  "whatWasIncorrect": [],
  "whatWasDoneWell": [],
  "positiveComment": "",
  "feedback": ""
}}

Definitions:

marksAwarded:
Marks awarded from 0 to {max_marks}.

matchPercentage:
Conceptual coverage from 0 to 100.

matchedConcepts:
Important concepts correctly demonstrated.

missingConcepts:
Important concepts not demonstrated.

incorrectConcepts:
Incorrect concepts or statements.

whatShouldHaveBeenIncluded:
Important information that should have appeared.

whatWasMissing:
Specific information absent from the answer.

whatWasIncorrect:
Specific mistakes made by the student.

whatWasDoneWell:
Specific things correctly answered.

positiveComment:
Positive comment when the answer is correct or
constructive comment when improvement is needed.

feedback:
Short explanation of the final score.

Return arrays as arrays of strings.

Return JSON only.
"""

    return prompt.strip()


# ============================================================
# EVALUATE ONE QUESTION
# ============================================================

def evaluate_question(
    client: Groq,
    question: Any,
    student_answer: str,
    marking_rules: Optional[
        Dict[str, Any]
    ] = None,
    student_id: Any = "unknown",
    question_number: int = 1,
) -> Dict[str, Any]:

    max_marks = (
        get_question_marks(question)
    )

    expected_answer = (
        get_expected_answer(question)
    )

    question_text = (
        get_question_text(question)
    )

    prompt = build_question_prompt(
        question=question,
        student_answer=student_answer,
        marking_rules=marking_rules,
    )

    # --------------------------------------------------------
    # Show prompt in terminal
    # --------------------------------------------------------

    debug_prompt(
        student_id=student_id,
        question_number=question_number,
        prompt=prompt,
    )

    try:

        # ====================================================
        # GROQ API REQUEST
        # ====================================================

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are PaperMark AI. "
                        "Evaluate academic answers accurately. "
                        "Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
            response_format={
                "type": "json_object"
            },
        )

        raw_response = (
            response
            .choices[0]
            .message
            .content
            or ""
        )

        # ----------------------------------------------------
        # Show raw AI response in terminal
        # ----------------------------------------------------

        debug_response(
            student_id=student_id,
            question_number=question_number,
            response=raw_response,
        )

        parsed = extract_json(
            raw_response
        )

        # ====================================================
        # SCORE
        # ====================================================

        marks_awarded = clamp(
            safe_float(
                parsed.get(
                    "marksAwarded",
                    0,
                )
            ),
            0,
            max_marks,
        )

        match_percentage = clamp(
            safe_float(
                parsed.get(
                    "matchPercentage",
                    0,
                )
            ),
            0,
            100,
        )

        # ====================================================
        # FEEDBACK
        # ====================================================

        matched_concepts = ensure_list(
            parsed.get(
                "matchedConcepts",
                [],
            )
        )

        missing_concepts = ensure_list(
            parsed.get(
                "missingConcepts",
                [],
            )
        )

        incorrect_concepts = ensure_list(
            parsed.get(
                "incorrectConcepts",
                [],
            )
        )

        what_should_have_been_included = (
            ensure_list(
                parsed.get(
                    "whatShouldHaveBeenIncluded",
                    [],
                )
            )
        )

        what_was_missing = ensure_list(
            parsed.get(
                "whatWasMissing",
                [],
            )
        )

        what_was_incorrect = ensure_list(
            parsed.get(
                "whatWasIncorrect",
                [],
            )
        )

        what_was_done_well = ensure_list(
            parsed.get(
                "whatWasDoneWell",
                [],
            )
        )

        positive_comment = str(
            parsed.get(
                "positiveComment",
                "",
            )
            or ""
        ).strip()

        feedback = str(
            parsed.get(
                "feedback",
                "",
            )
            or ""
        ).strip()

        # ====================================================
        # FALLBACK FEEDBACK
        # ====================================================

        if not what_should_have_been_included:

            what_should_have_been_included = (
                missing_concepts.copy()
            )

        if not what_was_missing:

            what_was_missing = (
                missing_concepts.copy()
            )

        if not what_was_incorrect:

            what_was_incorrect = (
                incorrect_concepts.copy()
            )

        if (
            not positive_comment
            and not missing_concepts
            and not incorrect_concepts
        ):

            positive_comment = (
                "The student correctly addressed "
                "the important concepts required "
                "by the expected answer."
            )

        if not feedback:

            if (
                not missing_concepts
                and not incorrect_concepts
            ):

                feedback = (
                    "The answer correctly covers "
                    "the important concepts in the "
                    "expected answer."
                )

            else:

                feedback = (
                    "The answer demonstrates some "
                    "required concepts but is missing "
                    "or incorrect on important parts "
                    "of the expected answer."
                )

        # ====================================================
        # FINAL RESULT
        # ====================================================

        result = {
            "questionId": get_field(
                question,
                "id",
                None,
            ),
            "question": question_text,
            "expectedAnswer": expected_answer,
            "studentAnswer": student_answer,
            "maxMarks": max_marks,
            "marksAwarded": round(
                marks_awarded,
                2,
            ),
            "matchPercentage": round(
                match_percentage,
                2,
            ),
            "evaluationMethod": (
                get_evaluation_method(
                    question
                )
            ),
            "matchedConcepts": (
                matched_concepts
            ),
            "missingConcepts": (
                missing_concepts
            ),
            "incorrectConcepts": (
                incorrect_concepts
            ),
            "whatShouldHaveBeenIncluded": (
                what_should_have_been_included
            ),
            "whatWasMissing": (
                what_was_missing
            ),
            "whatWasIncorrect": (
                what_was_incorrect
            ),
            "whatWasDoneWell": (
                what_was_done_well
            ),
            "positiveComment": (
                positive_comment
            ),
            "feedback": feedback,
        }

        # ----------------------------------------------------
        # Terminal final result
        # ----------------------------------------------------

        print()
        print("-" * 90)
        print(
            f"FINAL RESULT | "
            f"Student: {student_id} | "
            f"Question: {question_number}"
        )
        print("-" * 90)
        print(
            f"Marks: "
            f"{result['marksAwarded']} / "
            f"{max_marks}"
        )
        print(
            f"Match: "
            f"{result['matchPercentage']}%"
        )
        print(
            f"Done Well: "
            f"{result['whatWasDoneWell']}"
        )
        print(
            f"Missing: "
            f"{result['whatWasMissing']}"
        )
        print(
            f"Incorrect: "
            f"{result['whatWasIncorrect']}"
        )
        print(
            f"Feedback: "
            f"{result['feedback']}"
        )
        print("-" * 90)

        return result

    except Exception as error:

        debug_error(
            student_id=student_id,
            question_number=question_number,
            error=error,
        )

        # API failure should NOT silently become zero marks.
        raise


# ============================================================
# GET STUDENT ANSWERS
# ============================================================

def get_student_answers(
    student: Any,
) -> Dict[int, str]:

    answers: Dict[int, str] = {}

    student_answers = getattr(
        student,
        "answers",
        [],
    ) or []

    for answer in student_answers:

        question_id = getattr(
            answer,
            "question_id",
            None,
        )

        answer_text = getattr(
            answer,
            "answer_text",
            "",
        )

        if question_id is not None:

            answers[
                int(question_id)
            ] = str(
                answer_text or ""
            )

    return answers


# ============================================================
# EVALUATE ONE STUDENT
# ============================================================

def evaluate_student(
    client: Groq,
    student: Any,
    questions: List[Any],
    marking_rules: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    student_identifier = getattr(
        student,
        "student_id",
        getattr(
            student,
            "id",
            "unknown",
        ),
    )

    student_name = getattr(
        student,
        "name",
        None,
    )

    print()
    print("#" * 90)
    print(
        f"STARTING STUDENT EVALUATION: "
        f"{student_identifier}"
    )

    if student_name:
        print(
            f"Student Name: {student_name}"
        )

    print("#" * 90)

    answers = get_student_answers(
        student
    )

    question_results = []

    obtained_marks = 0.0
    total_marks = 0.0

    for index, question in enumerate(
        questions,
        start=1,
    ):

        question_id = getattr(
            question,
            "id",
            None,
        )

        max_marks = (
            get_question_marks(
                question
            )
        )

        total_marks += max_marks

        # ----------------------------------------------------
        # Find student's answer
        # ----------------------------------------------------

        student_answer = ""

        if question_id is not None:

            student_answer = str(
                answers.get(
                    int(question_id),
                    "",
                )
                or ""
            ).strip()

        # ----------------------------------------------------
        # Empty answer
        # ----------------------------------------------------

        if not student_answer:

            empty_result = {
                "questionId": question_id,
                "question": (
                    get_question_text(
                        question
                    )
                ),
                "expectedAnswer": (
                    get_expected_answer(
                        question
                    )
                ),
                "studentAnswer": "",
                "maxMarks": max_marks,
                "marksAwarded": 0.0,
                "matchPercentage": 0.0,
                "evaluationMethod": (
                    get_evaluation_method(
                        question
                    )
                ),
                "matchedConcepts": [],
                "missingConcepts": [
                    "No answer was provided."
                ],
                "incorrectConcepts": [],
                "whatShouldHaveBeenIncluded": [
                    "A relevant answer addressing "
                    "the question was required."
                ],
                "whatWasMissing": [
                    "No student answer was provided."
                ],
                "whatWasIncorrect": [],
                "whatWasDoneWell": [],
                "positiveComment": "",
                "feedback": (
                    "No answer was provided, "
                    "so no marks were awarded."
                ),
            }

            question_results.append(
                empty_result
            )

            print()
            print(
                f"Question {index}: "
                f"NO ANSWER → 0 / {max_marks}"
            )

            continue

        # ----------------------------------------------------
        # AI evaluation
        # ----------------------------------------------------

        result = evaluate_question(
            client=client,
            question=question,
            student_answer=student_answer,
            marking_rules=marking_rules,
            student_id=student_identifier,
            question_number=index,
        )

        obtained_marks += safe_float(
            result.get(
                "marksAwarded",
                0,
            )
        )

        question_results.append(
            result
        )

    # ========================================================
    # STUDENT TOTAL
    # ========================================================

    percentage = 0.0

    if total_marks > 0:

        percentage = (
            obtained_marks
            / total_marks
        ) * 100

    final_result = {
        "studentId": student_identifier,
        "studentName": student_name,
        "totalMarks": round(
            total_marks,
            2,
        ),
        "obtainedMarks": round(
            obtained_marks,
            2,
        ),
        "percentage": round(
            percentage,
            2,
        ),
        "questionResults": question_results,
    }

    print()
    print("=" * 90)
    print(
        f"STUDENT COMPLETED: "
        f"{student_identifier}"
    )
    print("=" * 90)
    print(
        f"FINAL SCORE: "
        f"{final_result['obtainedMarks']} / "
        f"{final_result['totalMarks']}"
    )
    print(
        f"PERCENTAGE: "
        f"{final_result['percentage']}%"
    )
    print("=" * 90)

    return final_result


# ============================================================
# EVALUATE COMPLETE ASSIGNMENT
# ============================================================

def evaluate_assignment(
    evaluation: Any,
) -> Dict[str, Any]:

    print()
    print("#" * 90)
    print(
        "PAPERMARK AI — GROQ EVALUATION STARTED"
    )
    print("#" * 90)

    client = get_groq_client()

    questions = list(
        getattr(
            evaluation,
            "questions",
            [],
        )
        or []
    )

    students = list(
        getattr(
            evaluation,
            "students",
            [],
        )
        or []
    )

    # --------------------------------------------------------
    # Default marking settings
    # --------------------------------------------------------

    marking_rules = {
        "semanticMeaning": True,
        "keywordCheck": False,
        "formulaCheck": False,
        "instructorReview": False,
        "customRules": [],
        "rubricPoints": [],
    }

    results = []

    for student in students:

        result = evaluate_student(
            client=client,
            student=student,
            questions=questions,
            marking_rules=marking_rules,
        )

        results.append(
            result
        )

    # ========================================================
    # FINAL ASSIGNMENT RESULT
    # ========================================================

    total_marks = sum(
        get_question_marks(
            question
        )
        for question in questions
    )

    average_percentage = 0.0

    if results:

        average_percentage = (
            sum(
                safe_float(
                    result.get(
                        "percentage",
                        0,
                    )
                )
                for result in results
            )
            / len(results)
        )

    final_result = {
        "evaluationId": getattr(
            evaluation,
            "id",
            None,
        ),
        "evaluationTitle": getattr(
            evaluation,
            "title",
            "",
        ),
        "totalMarks": total_marks,
        "students": results,
        "averagePercentage": round(
            average_percentage,
            2,
        ),
    }

    print()
    print("#" * 90)
    print(
        "PAPERMARK AI — EVALUATION COMPLETED"
    )
    print("#" * 90)
    print(
        f"Students evaluated: "
        f"{len(results)} / {len(students)}"
    )
    print(
        f"Average percentage: "
        f"{final_result['averagePercentage']}%"
    )
    print("#" * 90)

    return final_result