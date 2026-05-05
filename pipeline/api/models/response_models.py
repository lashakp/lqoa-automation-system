from pydantic import BaseModel, Field
from typing import Optional, List


class EmailResponse(BaseModel):

    company_id: str

    company_name: str

    subject: str

    body: str

    execution_time_seconds: float


class CompanyResult(BaseModel):

    id: str

    name: str

    industry: str

    batch: str

    location: str

    score: float

    similarity_score: float

    lead_score: float

    summary: str


class SearchResponse(BaseModel):

    query: str

    results: List[CompanyResult]

    total_matched: int

    warning: Optional[str] = None


class RecommendationResponse(BaseModel):

    company_id: str

    company_name: str

    recommendations: List[CompanyResult]

    total_recommended: int


class BatchResponse(BaseModel):

    batches: List[str]


class IndustryResponse(BaseModel):

    industries: List[str]


class LocationResponse(BaseModel):

    locations: List[str]


class HealthResponse(BaseModel):

    status: str

    service: str

    version: str


class VersionResponse(BaseModel):

    api_version: str

    system: str

    status: str

    description: str
