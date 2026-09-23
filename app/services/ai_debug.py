import json
from typing import Any


# =========================================================
# AI DEBUG LOGGER
# =========================================================

def debug_prompt(
    *,
    model: str,
    question: str,
    expected_answer: str,
    student_answer: str,
    prompt: str,
):
    """
    Temporary development logger.

    This prints the exact information sent to Gemini.

    Delete this file and its imports/calls before production
    if you no longer want terminal debugging.
    """

    print("\n")
    print("=" * 100)
    print("                 PAPERMARK AI — LIVE AI DEBUG")
    print("=" * 100)

    print("\n[MODEL]")
    print(model)

    print("\n[QUESTION]")
    print("-" * 100)
    print(question or "[EMPTY]")
    print("-" * 100)

    print("\n[TEACHER EXPECTED / MODEL ANSWER]")
    print("-" * 100)
    print(expected_answer or "[EMPTY]")
    print("-" * 100)

    print("\n[STUDENT ANSWER]")
    print("-" * 100)
    print(student_answer or "[EMPTY]")
    print("-" * 100)

    print("\n[EXACT PROMPT SENT TO GEMINI]")
    print("=" * 100)
    print(prompt)
    print("=" * 100)


def debug_response(
    response_text: str,
):
    """
    Print the raw response received from Gemini.
    """

    print("\n")
    print("[RAW GEMINI RESPONSE]")
    print("=" * 100)

    print(
        response_text
        or "[EMPTY RESPONSE]"
    )

    print("=" * 100)


def debug_result(
    result: dict[str, Any],
):
    """
    Print parsed AI result.
    """

    print("\n")
    print("[PARSED AI JSON]")
    print("-" * 100)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("-" * 100)

    print("\n[FINAL AI RESULT]")

    print(
        f"Marks Awarded : "
        f"{result.get('marksAwarded', 0)}"
    )

    print(
        f"Concept Match : "
        f"{result.get('matchPercentage', 0)}%"
    )

    print(
        f"Feedback      : "
        f"{result.get('feedback', '')}"
    )

    print("\nMatched Concepts:")

    matched = result.get(
        "matchedConcepts",
        [],
    )

    if matched:

        for item in matched:

            print(
                f"  ✓ {item}"
            )

    else:

        print("  None")


    print("\nMissing Concepts:")

    missing = result.get(
        "missingConcepts",
        [],
    )

    if missing:

        for item in missing:

            print(
                f"  ! {item}"
            )

    else:

        print("  None")


    print("\nIncorrect Concepts:")

    incorrect = result.get(
        "incorrectConcepts",
        [],
    )

    if incorrect:

        for item in incorrect:

            print(
                f"  ✗ {item}"
            )

    else:

        print("  None")

    print("\n")
    print("=" * 100)
    print("                    AI EVALUATION COMPLETE")
    print("=" * 100)
    print("\n")


def debug_error(
    error: Exception,
):
    """
    Print Gemini/API errors in a cleaner format.
    """

    print("\n")
    print("=" * 100)
    print("                    PAPERMARK AI — AI ERROR")
    print("=" * 100)

    print(
        f"\n{type(error).__name__}:"
    )

    print(
        str(error)
    )

    print("=" * 100)
    print("\n")