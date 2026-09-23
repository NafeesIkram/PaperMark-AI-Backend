from fastapi import APIRouter, HTTPException
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluation_service import evaluate_assignment

router = APIRouter(prefix="/api", tags=["Evaluation"])

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(evaluation: EvaluationRequest):
    try:
        return evaluate_assignment(evaluation)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        print("Evaluation error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Evaluation failed. Check backend logs, API key, model name, and request data."
        ) from error
