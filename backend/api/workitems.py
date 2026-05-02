from fastapi import APIRouter, HTTPException
from config.database import get_pg_pool, get_redis, get_mongo_db
from models.signal import RCARequest, WorkItemStatus
from workflow.state_machine import get_next_status, can_transition_to_closed

router = APIRouter(prefix="/api/v1", tags=["Work Items"])

@router.get("/workitems")
async def list_work_items():
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id::text, component_id, priority, status,
                   signal_count, start_time, end_time, mttr_seconds, created_at
            FROM work_items
            ORDER BY
                CASE priority
                    WHEN 'P0' THEN 1
                    WHEN 'P1' THEN 2
                    WHEN 'P2' THEN 3
                    WHEN 'P3' THEN 4
                END,
                created_at DESC
        """)
    return [dict(r) for r in rows]

@router.get("/workitems/{work_item_id}")
async def get_work_item(work_item_id: str):
    pool = await get_pg_pool()
    db = await get_mongo_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id::text, component_id, priority, status, signal_count, start_time, end_time, mttr_seconds, created_at FROM work_items WHERE id = $1",
            work_item_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Work item not found")
    signals = await db.raw_signals.find(
        {"work_item_id": work_item_id},
        {"_id": 0}
    ).limit(100).to_list(length=100)
    return {"work_item": dict(row), "signals": signals}

@router.patch("/workitems/{work_item_id}/transition")
async def transition_work_item(work_item_id: str):
    pool = await get_pg_pool()
    redis = await get_redis()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status FROM work_items WHERE id = $1", work_item_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Work item not found")
        current_status = WorkItemStatus(row["status"])
        if current_status == WorkItemStatus.CLOSED:
            raise HTTPException(status_code=400, detail="Work item is already CLOSED")
        next_status = get_next_status(current_status)
        await conn.execute(
            "UPDATE work_items SET status = $1, updated_at = NOW() WHERE id = $2",
            next_status.value, work_item_id
        )
    await redis.hset(f"work_item:{work_item_id}", "status", next_status.value)
    return {"work_item_id": work_item_id, "status": next_status.value}

@router.post("/workitems/{work_item_id}/rca")
async def submit_rca(work_item_id: str, rca: RCARequest):
    pool = await get_pg_pool()
    redis = await get_redis()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status FROM work_items WHERE id = $1", work_item_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Work item not found")
        current_status = WorkItemStatus(row["status"])
        if not can_transition_to_closed(current_status):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot close from {current_status}. Must be RESOLVED first."
            )
        if not rca.root_cause_category.strip():
            raise HTTPException(status_code=422, detail="root_cause_category is required")
        if not rca.fix_applied.strip():
            raise HTTPException(status_code=422, detail="fix_applied is required")
        if not rca.prevention_steps.strip():
            raise HTTPException(status_code=422, detail="prevention_steps is required")
        mttr = int((rca.incident_end - rca.incident_start).total_seconds())
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO rca_records
                    (work_item_id, incident_start, incident_end, root_cause_category, fix_applied, prevention_steps)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, work_item_id, rca.incident_start, rca.incident_end,
                rca.root_cause_category, rca.fix_applied, rca.prevention_steps)
            await conn.execute("""
                UPDATE work_items
                SET status = 'CLOSED', end_time = $1, mttr_seconds = $2, updated_at = NOW()
                WHERE id = $3
            """, rca.incident_end, mttr, work_item_id)
    await redis.hset(f"work_item:{work_item_id}", mapping={
        "status": "CLOSED", "mttr_seconds": str(mttr)
    })
    return {"work_item_id": work_item_id, "status": "CLOSED", "mttr_seconds": mttr}

@router.get("/workitems/{work_item_id}/rca")
async def get_rca(work_item_id: str):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM rca_records WHERE work_item_id = $1", work_item_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="RCA not found for this work item")
    return dict(row)
