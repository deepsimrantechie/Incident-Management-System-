from fastapi import APIRouter
from config.database import get_pg_pool, get_redis, get_mongo_db
from ingestion.producer import signal_buffer

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    status = {"status": "ok", "services": {}}
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        status["services"]["postgres"] = "ok"
    except Exception as e:
        status["services"]["postgres"] = f"error: {e}"
        status["status"] = "degraded"
    try:
        redis = await get_redis()
        await redis.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {e}"
        status["status"] = "degraded"
    try:
        db = await get_mongo_db()
        await db.command("ping")
        status["services"]["mongodb"] = "ok"
    except Exception as e:
        status["services"]["mongodb"] = f"error: {e}"
        status["status"] = "degraded"
    status["buffer_size"] = signal_buffer.qsize()
    return status
