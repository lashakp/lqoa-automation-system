LQOA — YC Startup Intelligence API
Overview

LQOA is an AI-powered lead intelligence system designed to help users discover, analyze, and engage high-potential startups using semantic search and automated personalization.

Features
Semantic company search
Intelligent filtering
Lead scoring
Company recommendations
Personalized email generation
Email sending
Demo and full access modes
Tech Stack
FastAPI
SQLite
FAISS
Sentence Transformers
Docker
Installation
git clone <repo>
cd project
pip install -r requirements.txt
uvicorn pipeline.api.app:app --reload

API Docs
http://localhost:8000/docs

Environment Variables
SMTP_SERVER
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
FROM_EMAIL
API_KEY

Docker
docker build -t lqoa-api .
docker run -p 8000:8000 lqoa-api

Deployment

Deployed via Render using Docker.

Future Improvements
React frontend
CRM integrations
Real contact enrichment
Campaign automation

Author
Lash
