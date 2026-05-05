from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
import time
import logging

from pipeline.api.models.response_models import SearchResponse
from pipeline.search.search_faiss import semantic_search
from pipeline.api.security.access_control import get_access_mode
from pipeline.api.models.filter_enums import (
    IndustryEnum,
    BatchEnum,
    LocationEnum
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search companies using natural language",
    description="""
Semantic company search with structured filters.

Demo Mode:
- Maximum limit: 15
- Offset capped at 10

Full Mode:
- Full pagination access
"""
)
def search(
    access_mode: str = Depends(get_access_mode),

    query: str = Query(
        ...,
        description="Describe the companies to search for",
        example="AI fraud detection for banks"
    ),

    industry: Optional[IndustryEnum] = Query(
        None,
        description="Filter by industry"
    ),

    batch: Optional[BatchEnum] = Query(
        None,
        description="Filter by accelerator batch"
    ),

    location: Optional[LocationEnum] = Query(
        None,
        description="Filter by geographic location"
    ),

    limit: int = Query(
        20,
        ge=1,
        le=50,
        description="Maximum number of results"
    ),

    offset: int = Query(
        0,
        ge=0,
        description="Pagination offset"
    )
):

    if not query:

        raise HTTPException(
            status_code=400,
            detail="Search query is required"
        )

    if access_mode == "demo":

        limit = min(limit, 15)
        offset = min(offset, 10)

    start_time = time.time()

    logger.info(
        f"Search request received: {query}"
    )

    try:

        results, warning, total_matches = semantic_search(
            mode=access_mode,
            query=query,
            industry=industry.value if industry else None,
            batch=batch.value if batch else None,
            location=location.value if location else None,
            limit=limit,
            offset=offset
        )

        response_items = []

        for score, company in results:

            response_items.append({
                "id": company.get("id", ""),
                "name": company.get("name", ""),
                "industry": company.get("industries", ""),
                "batch": company.get("batch", ""),
                "location": company.get("location", ""),
                "score": company.get("final_score", 0.0),
                "similarity_score": company.get(
                    "similarity_score",
                    0.0
                ),
                "lead_score": company.get(
                    "lead_score",
                    0.0
                ),
                "summary": company.get(
                    "summary",
                    ""
                )
            })

        execution_time = round(
            time.time() - start_time,
            3
        )

        logger.info(
            f"Search completed in {execution_time} seconds"
        )

        return {
            "query": query,
            "results": response_items,
            "total_matched": total_matches,
            "warning": warning,
            "execution_time_seconds": execution_time
        }

    except Exception as e:

        logger.error(
            f"Search failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Search failed"
        )
