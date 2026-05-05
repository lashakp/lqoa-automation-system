from pipeline.recommendation.recommend_similar_companies import (
    recommend_similar_companies
)


def run_recommendation(
    company_id=None,
    name=None,
    limit=10
):

    return recommend_similar_companies(

        company_id=company_id,

        name=name,

        limit=limit
    )
