from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
import time
import logging

from pipeline.api.models.response_models import RecommendationResponse
from pipeline.recommendation.recommend_similar_companies import (
    recommend_similar_companies
)
from pipeline.api.security.access_control import get_access_mode

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommend",
    tags=["Recommendations"]
)


@router.get(
    "",
    response_model=RecommendationResponse,
    summary="Find similar companies",
    description="""
Retrieve companies similar to a specified company.

Demo Mode:
- Returns up to 10 results

Full Mode:
- Returns full configured limit
"""
)
def recommend(
    access_mode: str = Depends(get_access_mode),

    company_id: Optional[str] = Query(
        None,
        description="Company ID to find similar companies for",
        example="cfe6c73b4b9de5aeb1a820e29ae92eb4"
    ),

    name: Optional[str] = Query(
        None,
        description="Company name if ID is unavailable",
        example="Stripe"
    ),

    limit: int = Query(
        15,
        ge=1,
        le=25,
        description="Maximum number of recommendations"
    )
):

    if not company_id and not name:

        raise HTTPException(
            status_code=400,
            detail="You must provide company_id or name"
        )

    if access_mode == "demo":

        limit = min(limit, 10)

    start_time = time.time()

    logger.info(
        f"Recommendation request received: "
        f"company_id={company_id}, name={name}"
    )

    try:

        results = recommend_similar_companies(
            company_id=company_id,
            name=name,
            limit=limit
        )

        execution_time = round(
            time.time() - start_time,
            3
        )

        if not results:

            return {
                "company_id": company_id,
                "company_name": name,
                "total_recommended": 0,
                "recommendations": [],
                "execution_time_seconds": execution_time
            }

        company_name = results[0][1]["name"]

        formatted = []

        for score, company in results:

            formatted.append({
                "id": company["id"],
                "name": company["name"],
                "industry": company.get("industries") or "",
                "batch": company.get("batch") or "",
                "location": company.get("location") or "",
                "summary": company.get("summary") or "",
                "score": round(score, 4),
                "similarity_score": round(score, 4),
                "lead_score": float(
                    company.get("lead_score", 0.0)
                )
            })

        return {
            "company_id": company_id,
            "company_name": company_name,
            "total_recommended": len(formatted),
            "recommendations": formatted,
            "execution_time_seconds": execution_time
        }

    except Exception as e:

        logger.error(
            f"Recommendation failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations"
        )
