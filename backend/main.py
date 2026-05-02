import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware = allows frontend (port 5173) to talk to backend (port 8000)
# browsers block requests between different ports by default
# CORS = Cross Origin Resource Sharing — permission system for this

from contextlib import asynccontextmanager
# asynccontextmanager = lets us write startup and shutdown code
# in one place using yield

# import all our pieces
from config.database import close_connections
from config.init_db import init_db
from ingestion.producer import flush_buffer_to_kafka
from consumer.consumer import run_consumer
from api.ingestion import router as ingestion_router
# "as ingestion_router" = rename it so we can have multiple routers
from api.workitems import router as workitems_router
from api.health import router as health_router
from ingestion.rate_limiter import RateLimiter
from config.settings import settings

# ─── Lifespan = Startup + Shutdown Code ───────────────────────
@asynccontextmanager
# @asynccontextmanager = makes this function work with "async with"
async def lifespan(app: FastAPI):
    # Everything BEFORE yield runs on startup
    # Everything AFTER yield runs on shutdown

    # ── STARTUP ──
    print("[STARTUP] Initializing database tables...")
    await init_db()
    # create tables in postgres if they don't exist

    print("[STARTUP] Starting Kafka buffer flusher...")
    asyncio.create_task(flush_buffer_to_kafka())
    # create_task = run this function in background WITHOUT waiting
    # flush_buffer_to_kafka runs forever in background
    # while it runs, our server can still handle requests

    print("[STARTUP] Starting Kafka consumer...")
    asyncio.create_task(run_consumer())
    # run_consumer also runs forever in background
    # reads from kafka and creates work items

    print("[STARTUP] IMS Backend is ready!")

    yield
    # yield = pause here, server runs normally
    # when server is shutting down, code after yield runs

    # ── SHUTDOWN ──
    print("[SHUTDOWN] Closing connections...")
    await close_connections()
    # cleanly close all database connections

# ─── Create the FastAPI App ───────────────────────────────────
app = FastAPI(
    title="Incident Management System",
    version="1.0.0",
    lifespan=lifespan  # use our startup/shutdown code
)

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins = which websites can talk to our backend
    # "*" = allow ALL origins (any website)
    # in production you would list specific URLs

    allow_credentials=False,
    # credentials = cookies and auth headers
    # False = don't allow credentials with wildcard origin

    allow_methods=["*"],
    # allow all HTTP methods: GET, POST, PATCH, DELETE etc

    allow_headers=["*"],
    # allow all headers
)

# ─── Rate Limiter Middleware ──────────────────────────────────
rate_limiter = RateLimiter(max_requests=settings.rate_limit_per_second)
# create one rate limiter object

app.middleware("http")(rate_limiter)
# attach it to app as HTTP middleware
# middleware = runs for EVERY request before reaching the route handler
# order: request → rate_limiter → route handler → response

# ─── Attach All Routers ───────────────────────────────────────
app.include_router(health_router)
# adds GET /health route

app.include_router(ingestion_router)
# adds POST /api/v1/signals and POST /api/v1/signals/batch

app.include_router(workitems_router)
# adds GET/PATCH/POST /api/v1/workitems/...

# ─── Root Route ───────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "IMS Backend Running",
        "docs": "/docs"
        # /docs = auto-generated API documentation page
        # FastAPI creates this for free!
    }

# ─── HOW THE WHOLE SYSTEM FLOWS ───────────────────────────────
# 1. Server starts → init_db() creates tables
# 2. flush_buffer_to_kafka() starts in background
# 3. run_consumer() starts in background
# 4. Server is ready to accept requests
#
# When a signal arrives:
# POST /api/v1/signals
#   → rate_limiter checks if too many requests
#   → ingest_signal() puts signal in buffer
#   → returns 202 immediately
#   → (background) flush_buffer sends to Kafka
#   → (background) consumer reads from Kafka
#   → consumer saves to MongoDB
#   → consumer creates/updates Work Item in Postgres
#   → consumer sets debounce key in Redis