FULL PROJECT REPORT (A–Z)

This is structured like a technical whitepaper + portfolio documentation.

1. Problem Statement

Modern outbound sales suffers from:

Poor targeting
Generic outreach
Low reply rates
Lack of intelligent filtering

Goal:

Build an AI-powered lead intelligence system that:
- discovers companies
- ranks them
- recommends similar ones
- generates personalized outreach
- enables direct engagement

2. Data Acquisition Strategy
Initial Approach — Algolia (YC API)

Attempted:

YC Algolia index


Challenges:

Rate limits
Partial data
Missing structured fields
Inconsistent summaries
Final Approach — Mirror Dataset Strategy

Solution:

Build local YC mirror


Pipeline:

Raw → Enriched → Processed

3. Data Pipeline Architecture
Stage 1 — Raw Extraction

Collected:

Company name
Batch
Industry
Location
Website

Stored as:

raw dataset

Stage 2 — Enrichment

Added:

Website summaries
Cleaned industries
Standardized locations

Handled:

missing data
inconsistent formatting

Stage 3 — Processed Dataset

Final structured table:

yc_companies


Fields:

id
name
industries
batch
location
website_summary
lead_score

4. Database Design

Database:

SQLite


Why:

Lightweight
Fast
Easy deployment
No external dependency
5. Feature Engineering
Lead Scoring System

Computed using:

industry relevance
keyword signals
inferred growth potential

Normalized:

0 → 1 scale

Text Processing

Applied:

cleaning
normalization
fallback handling
6. Embedding System

Model:

all-MiniLM-L6-v2


Used for:

semantic search


Process:

text → vector (384 dimensions)

7. Vector Indexing

Tool:

FAISS


Stored:

faiss_index.bin
id_map.json

Search Strategy
cosine similarity (normalized vectors)

8. Ranking Algorithm

Hybrid scoring:

final_score =
    0.75 * similarity_score
  + 0.25 * lead_score

9. Fallback Logic

If filters return nothing:

remove filters
return semantic results
show warning

10. API Architecture

Framework:

FastAPI


Endpoints:

/search
/recommend
/personalization/generate-email
/personalization/send-email
/metadata
/system

11. Filtering System

Implemented via:

Enums


For:

industry
batch
location
12. Recommendation Engine

Logic:

vector similarity between companies


Input:

company_id OR name

13. Personalization Engine

Core logic:

signal detection (fraud, payments, security)
dynamic sentence construction
contextual messaging
Improvements Made
removed robotic tone
added variation
added natural phrasing
contextual hooks
14. Outreach System
Email Generation

Produces:

subject
body
personalized context
Email Sending

Uses:

SMTP


Flow:

generate → infer contact → send

Contact Strategy

Since YC doesn’t provide emails:

Solution:

info@domain.com heuristic

15. Access Control System

Modes:

demo
full

Demo Mode

Limits:

search results
recommendations
personalization preview
Full Mode

Unlocked via:

API key

16. API Security

Header:

x-api-key

17. UI Considerations (Swagger → Product)

Problem:

Swagger too technical


Solution:

React frontend (planned)

18. Deployment Strategy

Containerization:

Docker


Hosting:

Render

19. System Flow
User → API → FAISS → SQLite → Ranking → Response
