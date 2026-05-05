from pipeline.search.search_faiss import semantic_search
from pipeline.search.search_linear import linear_search


def run_search(
    query,
    industry=None,
    batch=None,
    location=None,
    limit=10,
    offset=0,
    mode="semantic"
):

    if mode == "semantic":

        return semantic_search(
            query=query,
            industry=industry,
            batch=batch,
            location=location,
            limit=limit,
            offset=offset
        )

    return linear_search(
        query=query,
        industry=industry,
        batch=batch,
        location=location,
        limit=limit,
        offset=offset
    )
