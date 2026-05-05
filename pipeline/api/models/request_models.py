from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):

    query: str = Field(
        ...,
        description="Describe the type of companies you are searching for using natural language",
        example="AI fraud detection for banks"
    )

    industry: Optional[str] = Field(
        default=None,
        description="Filter results by industry",
        example="Fintech"
    )

    batch: Optional[str] = Field(
        default=None,
        description="Filter companies by accelerator batch",
        example="Winter 2026"
    )

    location: Optional[str] = Field(
        default=None,
        description="Filter companies by geographic location",
        example="San Francisco"
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return (1 to 50)",
        example=10
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination",
        example=0
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "AI fraud detection for banks",
                "industry": "Fintech",
                "batch": "Winter 2026",
                "location": "San Francisco",
                "limit": 10,
                "offset": 0
            }
        }


class RecommendationRequest(BaseModel):

    company_id: Optional[str] = Field(
        default=None,
        description="Unique company identifier used to find similar companies",
        example="cfe6c73b4b9de5aeb1a820e29ae92eb4"
    )

    name: Optional[str] = Field(
        default=None,
        description="Company name used when company_id is not available",
        example="Stripe"
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum number of recommendations to return",
        example=10
    )

    class Config:

        json_schema_extra = {

            "example": {
                
                "name": "stripe",

                "company_id": "cfe6c73b4b9de5aeb1a820e29ae92eb4",

                "limit": 10
            }
        }


class EmailRequest(BaseModel):

    company_id: str = Field(
        ...,
        description="Unique identifier of the company you want to contact",
        example="cfe6c73b4b9de5aeb1a820e29ae92eb4"
    )

    sender_name: str = Field(
        ...,
        description="Full name of the person sending the email",
        example="John Doe"
    )

    sender_role: str = Field(
        ...,
        description="Job title of the sender",
        example="Business Development Manager"
    )

    sender_company: str = Field(
        ...,
        description="Name of the sender's company",
        example="Acme Solutions"
    )

    class Config:

        json_schema_extra = {

            "example": {

                "company_id": "cfe6c73b4b9de5aeb1a820e29ae92eb4",

                "sender_name": "John Doe",

                "sender_role": "Business Development Manager",

                "sender_company": "Acme Solutions"
            }
        }


class BatchRequest(BaseModel):

    batch: Optional[str] = Field(
        default=None,
        description="Accelerator batch name",
        example="Winter 2026"
    )


class IndustryRequest(BaseModel):

    industry: Optional[str] = Field(
        default=None,
        description="Industry category",
        example="Healthcare"
    )


class LocationRequest(BaseModel):

    location: Optional[str] = Field(
        default=None,
        description="Geographic location",
        example="New York"
    )


class HealthRequest(BaseModel):

    pass


class VersionRequest(BaseModel):

    pass
