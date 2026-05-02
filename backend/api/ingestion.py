from fastapi import APIRouter, HTTPException
from models.signal import Signal
from ingestion.producer import buffer_signal

router = APIRouter(prefix="/api/v1", tags=["Ingestion"])

@router.post("/signals", status_code=202)
async def ingest_signal(signal: Signal):
    try:
        await buffer_signal(signal.model_dump(mode="json"))
        return {"status": "accepted", "component_id": signal.component_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signals/batch", status_code=202)
async def ingest_signals_batch(signals: list[Signal]):
    if len(signals) > 1000:
        raise HTTPException(status_code=400, detail="Max 1000 signals per batch")
    for signal in signals:
        await buffer_signal(signal.model_dump(mode="json"))
    return {"status": "accepted", "count": len(signals)}
