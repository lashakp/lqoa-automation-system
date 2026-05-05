import logging
from pathlib import Path
from fastapi import Depends

from fastapi import FastAPI

from pipeline.api.routers.search_router import router as search_router
from pipeline.api.routers.personalization_router import router as personalization_router
from pipeline.api.routers.recommendation_router import router as recommendation_router
from pipeline.api.routers.metadata_router import router as metadata_router
from pipeline.api.routers.system_router import router as system_router
from pipeline.api.security.access_control import get_access_mode


# ==============================
# Logging
# ==============================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# ==============================
# Database Path
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATH = (

    BASE_DIR

    / "pipeline"

    / "ingestion"

    / "data"

    / "yc_database.db"
)


# ==============================
# Tags Metadata
# ==============================

tags_metadata = [

    {
        "name": "Search",
        "description":
        "Semantic search for discovering and ranking companies."
    },

    {
        "name": "Recommendations",
        "description":
        "Find companies similar to a given company."
    },

    {
        "name": "Personalization",
        "description":
        "Generate personalized outreach emails."
    },

    {
        "name": "Metadata",
        "description":
        "Reference data like batches, industries, and locations."
    },

    {
        "name": "System",
        "description":
        "Health checks, version, and system information."
    }
]


# ==============================
# FastAPI App
# ==============================

app = FastAPI(

    title="LQOA - YC Startup Intelligence API",

    version="1.0.0",

    description="""
Search companies, generate personalized outreach,
and find similar organizations using AI.

Features:

• Vector embeddings  
• Lead scoring  
• Structured filtering  
• Similar company recommendations  
• AI-powered personalization
""",

    contact={
        "name": "LQOA Team",
        "email": "akporarhe@gmail.com"
    },

    openapi_tags=tags_metadata
)


# ==============================
# Register Routers
# ==============================

# ==============================
# Protected Routers
# ==============================

app.include_router(

    search_router,

    prefix="/api/v1"
)

app.include_router(

    recommendation_router,

    prefix="/api/v1"
)

app.include_router(

    personalization_router,

    prefix="/api/v1"
)

app.include_router(

    metadata_router,

    prefix="/api/v1"
)

app.include_router(

    system_router,

    prefix="/api/v1"
)


# ==============================
# Run Server
# ==============================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "pipeline.api.app:app",

        host="0.0.0.0",

        port=8000,

        reload=True
    )
