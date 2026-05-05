# pipeline/personalization/generate_email.py

import logging
from pathlib import Path
import pandas as pd
import random

from pipeline.api.dependencies.database import get_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "pipeline" / "ingestion" / "data" / "yc_database.db"


# ======================
# DEFAULT SENDER VALUES
# ======================

DEFAULT_NAME = "Paul"
DEFAULT_COMPANY = "Lash Tech"
DEFAULT_ROLE = "Founder"


# ======================
# VARIATION COMPONENTS
# ======================

GREETINGS = [
    "Hi team at {company},",
    "Hello {company} team,",
    "Hi {company},"
]

OPENERS = [
    "I came across {company} recently and was impressed by what you're building",
    "I was looking into companies in this space and {company} stood out",
    "I've been following companies working in this area and {company} caught my attention"
]

CTAS = [
    "Would you be open to a quick 10-minute chat next week?",
    "Worth a short conversation to compare notes?",
    "Happy to connect briefly if useful."
]

CLOSINGS = [
    "Best regards,",
    "Thanks,",
    "Appreciate your time,"
]


# ======================
# HELPERS
# ======================

def clean_summary(summary):

    if not summary:

        return None

    summary = summary.strip()

    if summary.lower() in [
        "fetch error",
        "error",
        "none",
        "null",
        ""
    ]:

        return None

    # keep it short and human
    MAX_LENGTH = 200

    if len(summary) > MAX_LENGTH:

        summary = summary[:MAX_LENGTH].rstrip()

        summary += "..."

    return summary


# ======================
# DATABASE ACCESS
# ======================

def get_company(company_id: str = None, name: str = None):

    conn = get_connection()

    if company_id:

        df = pd.read_sql_query(
            "SELECT * FROM yc_companies WHERE id = ?",
            conn,
            params=(company_id,)
        )

    elif name:

        df = pd.read_sql_query(
            "SELECT * FROM yc_companies WHERE name = ?",
            conn,
            params=(name,)
        )

    else:

        conn.close()
        return None

    conn.close()

    if df.empty:

        return None

    return df.iloc[0].to_dict()


# ======================
# SIGNAL PERSONALIZATION
# ======================

def detect_signal(summary, industries):

    text = (summary or "").lower()

    if "fraud" in text or "aml" in text:

        return "especially your focus on automating financial crime compliance workflows."

    if "security" in text:

        return "especially your work in strengthening security and risk detection systems."

    if "payments" in text:

        return "particularly your work in modernizing payment infrastructure."

    return f"especially the work you're doing in {industries}."


# ======================
# EMAIL GENERATOR
# ======================

def generate_personalized_email(
    company_id: str = None,
    name: str = None,
    sender_name: str = None,
    sender_role: str = None,
    sender_company: str = None
):

    logger.info(
        f"Generating email | company_id={company_id} | name={name}"
    )

    # ---------------------
    # Resolve sender identity
    # ---------------------

    sender_name = sender_name or DEFAULT_NAME
    sender_role = sender_role or DEFAULT_ROLE
    sender_company = sender_company or DEFAULT_COMPANY

    # ---------------------
    # Fetch company
    # ---------------------

    company = get_company(company_id, name)

    if not company:

        logger.warning("Company not found")

        return "Company not found."

    company_name = company.get("name")

    summary = clean_summary(
        company.get("website_summary")
    )

    industries = (
        company.get("industries")
        or "your space"
    )

    # ---------------------
    # Personalization signal
    # ---------------------

    signal_line = detect_signal(
        summary,
        industries
    )

    # ---------------------
    # Randomized components
    # ---------------------

    greeting = random.choice(GREETINGS).format(
        company=company_name
    )

    opener = random.choice(OPENERS).format(
        company=company_name
    )

    cta = random.choice(CTAS)

    closing = random.choice(CLOSINGS)

    # ---------------------
    # Build message
    # ---------------------

    email_parts = [

        greeting,

        "",

        f"{opener} — {signal_line}"

    ]

    if summary:

        email_parts.extend([

            "",

            f"I noticed: {summary}"

        ])

    email_parts.extend([

        "",

        f"At {sender_company}, we're helping B2B SaaS teams improve outbound reply rates and booking quality using AI that understands context — not just templates.",

        "",

        "There might be a useful overlap with what you're building.",

        "",

        cta,

        "",

        closing,

        "",

        sender_name,

        sender_role,

        sender_company
    ])

    email_body = "\n".join(email_parts)

    logger.info(
        f"Email generated successfully for {company_name}"
    )

    return email_body


# ======================
# CLI
# ======================

if __name__ == "__main__":

    print("\n=== AI Personalization Engine ===\n")

    choice = input(
        "Search by (1) ID or (2) Name? Enter 1 or 2: "
    ).strip()

    if choice == "1":

        company_id = input(
            "Enter Company ID: "
        ).strip()

        email = generate_personalized_email(
            company_id=company_id
        )

    else:

        name = input(
            "Enter Company Name: "
        ).strip()

        email = generate_personalized_email(
            name=name
        )

    print("\n" + "=" * 80)
    print("PERSONALIZED COLD EMAIL:")
    print("=" * 80)
    print(email)
