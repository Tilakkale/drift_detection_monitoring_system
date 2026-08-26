from fastapi import APIRouter, HTTPException, Query
from backend.app.services.drift_service import analyze_machine_drift
router = APIRouter()


@router.get("/analyze-drift")
def analyze_drift(
    machine_id: int = Query(1, ge=1, le=3),
    buckets: int = Query(10, ge=5, le=50)
):

    try:
        return analyze_machine_drift(
            machine_id=machine_id,
            buckets=buckets
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )
