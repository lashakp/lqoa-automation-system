from fastapi import APIRouter
import time
import logging

from pipeline.api.dependencies.database import get_connection
from pipeline.api.models.response_models import HealthResponse, VersionResponse
from pipeline.api.models.request_models import HealthRequest, VersionRequest


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/system"
)

@router.get(
    "/health",
    tags=["System"]
)
def health():

    return {

        "status": "healthy",

        "service": "LQOA API",

        "version": "1.0.0"
    }


@router.get(
    "/version",
    tags=["System"]
)
def version():

    return {

        "api_version": "v1",

        "system": "LQOA",

        "status": "stable",

        "description":
        "YC Startup Intelligence Platform"
    }