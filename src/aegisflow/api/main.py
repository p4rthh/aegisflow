"""FastAPI Application Entry Point for AegisFlow Engine.

See PROJECT_ROADMAP.md §5 & Task 11.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegisflow.api.deps import get_app_state
from aegisflow.api.routes_meta import router as meta_router
from aegisflow.api.routes_stream import router as stream_router
from aegisflow.api.routes_backtest import router as backtest_router
from aegisflow.api.routes_stress import router as stress_router
from aegisflow.api.routes_logs import router as logs_router
from aegisflow.api.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load dataset and cached artifacts
    state = get_app_state()
    state.load_all()
    yield
    # Shutdown


app = FastAPI(
    title="AegisFlow Algorithmic Treasury & Liquidity Engine",
    description="Institutional-grade treasury management API for digital banking platforms moving >$20M/hr.",
    version="0.1.0",
    lifespan=lifespan,
)

# Open CORS for Google Stitch frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(meta_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(stress_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(ws_router)
