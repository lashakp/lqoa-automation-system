from fastapi import APIRouter, HTTPException
import time
import logging
import sqlite3

from pipeline.api.dependencies.database import get_connection
from pipeline.api.models.response_models import BatchResponse, IndustryResponse, LocationResponse
from pipeline.api.models.request_models import BatchRequest, IndustryRequest, LocationRequest

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/metadata"
)
@router.get(
    "/stats",
    tags=["Analytics"]
)
def stats():

    with get_connection() as conn:

        total = conn.execute(
            "SELECT COUNT(*) FROM yc_companies"
        ).fetchone()[0]

        batches = conn.execute(
            "SELECT COUNT(DISTINCT batch) FROM yc_companies"
        ).fetchone()[0]

        industries = conn.execute(
            "SELECT COUNT(DISTINCT industries) FROM yc_companies"
        ).fetchone()[0]

        locations = conn.execute(
            "SELECT COUNT(DISTINCT location) FROM yc_companies"
        ).fetchone()[0]

    return {

        "total_companies": total,

        "unique_batches": batches,

        "unique_industries": industries,

        "unique_locations": locations
    }

# ==============================
# Metadata
# ==============================

@router.get(
    "/batches",
    tags=["Metadata"]
)
def batches():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT batch,
                   COUNT(*)
            FROM yc_companies
            GROUP BY batch
            ORDER BY batch DESC
            """
        ).fetchall()

    return {

        "batches": [

            {
                "batch": row[0],
                "company_count": row[1]
            }

            for row in rows
        ]
    }


@router.get(
    "/industries",
    tags=["Metadata"]
)
def industries():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT industries,
                   COUNT(*)
            FROM yc_companies
            GROUP BY industries
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

    return {

        "industries": [

            {
                "industry": row[0],
                "company_count": row[1]
            }

            for row in rows
        ]
    }


@router.get(
    "/locations",
    tags=["Metadata"]
)
def locations():

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT location,
                   COUNT(*)
            FROM yc_companies
            GROUP BY location
            ORDER BY COUNT(*) DESC
            LIMIT 20
            """
        ).fetchall()

    return {

        "top_locations": [

            {
                "location": row[0],
                "company_count": row[1]
            }

            for row in rows
        ]
    }