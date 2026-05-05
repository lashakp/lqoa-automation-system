from fastapi import APIRouter, Query, HTTPException, Depends
import time
import logging
from urllib.parse import urlparse

from pipeline.api.models.response_models import EmailResponse
from pipeline.personalization.generate_email import (
    generate_personalized_email,
    get_company
)

from pipeline.api.dependencies.database import get_connection
from pipeline.api.security.access_control import get_access_mode
from pipeline.email.send_email import send_email

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/personalization",
    tags=["Personalization"]
)

# =========================================
# CONTACT EMAIL GENERATOR
# =========================================

def generate_contact_email(website):

    if not website:

        return None

    parsed = urlparse(website)

    domain = parsed.netloc.replace(
        "www.",
        ""
    )

    if not domain:

        return None

    return f"info@{domain}"


# =========================================
# GENERATE EMAIL
# =========================================

@router.get(
    "/generate-email",
    response_model=EmailResponse,
    summary="Generate a personalized outreach email",
    description="""
Generate a customized outreach email tailored to a specific company.

Demo Mode:
- Email generation allowed
- Output slightly limited

Full Mode:
- Full personalization enabled
"""
)
def generate_email(

    access_mode: str = Depends(get_access_mode),

    company_id: str = Query(
        ...,
        description="Unique identifier of the company",
        example="cfe6c73b4b9de5aeb1a820e29ae92eb4"
    ),

    sender_name: str = Query(
        ...,
        description="Full name of the sender",
        example="John Doe"
    ),

    sender_role: str = Query(
        ...,
        description="Professional role of the sender",
        example="Sales Manager"
    ),

    sender_company: str = Query(
        ...,
        description="Company sending the outreach",
        example="Acme Solutions"
    )
):

    start_time = time.time()

    logger.info(
        f"Generating email for company_id: {company_id}"
    )

    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT name
                FROM yc_companies
                WHERE id = ?
                """,
                (company_id,)
            )

            row = cursor.fetchone()

        if not row:

            raise HTTPException(
                status_code=404,
                detail="Company not found"
            )

        company_name = row[0]

        # -----------------------------
        # Generate email
        # -----------------------------

        email_body = generate_personalized_email(
            company_id=company_id,
            sender_name=sender_name,
            sender_role=sender_role,
            sender_company=sender_company
        )

        # -----------------------------
        # Demo Mode Limitation
        # -----------------------------

        if access_mode == "demo":

            email_body += """

-------------------------------------

Demo Mode Preview:
Upgrade to Full Mode to unlock:

- Full-length personalization
- Unlimited email generation
- Email sending capability
"""

        subject = f"Quick question about {company_name}"

        execution_time = round(
            time.time() - start_time,
            3
        )

        logger.info(
            f"Email generated for {company_name}"
        )

        return {
            "company_id": company_id,
            "company_name": company_name,
            "subject": subject,
            "body": email_body,
            "execution_time_seconds": execution_time
        }

    except HTTPException:

        raise

    except Exception as e:

        logger.error(
            f"Email generation failed: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate email"
        )


# =========================================
# SEND EMAIL (FULL MODE ONLY)
# =========================================

@router.post(
    "/send-email",
    summary="Send outreach email",
    description="""
Send a personalized outreach email.

Available in Full Mode only.
"""
)
def send_outreach_email(
    access_mode: str = Depends(get_access_mode),
    company_id: str = Query(
        ...,
        description="Target company ID"
    ),
    sender_name: str = Query(
        ...,
        description="Sender name"
    ),
    sender_role: str = Query(
        ...,
        description="Sender role"
    ),
    sender_company: str = Query(
        ...,
        description="Sender company"
    )
):
    # -----------------------------
    # Restrict sending
    # -----------------------------
    if access_mode == "demo":
        raise HTTPException(
            status_code=403,
            detail="Email sending is available in full mode only"
        )

    start_time = time.time()

    try:
        company = get_company(
            company_id=company_id
        )

        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found"
            )

        website = company.get("website")
        recipient_email = generate_contact_email(website)

        if not recipient_email:
            raise HTTPException(
                status_code=400,
                detail="No recipient email available"
            )

        # -----------------------------
        # Generate email
        # -----------------------------
        email_body = generate_personalized_email(
            company_id=company_id,
            sender_name=sender_name,
            sender_role=sender_role,
            sender_company=sender_company
        )

        subject = f"Quick question about {company['name']}"
        success = send_email(
            recipient_email,
            subject,
            email_body
        )

        execution_time = round(time.time() - start_time, 3)

        if success:
            logger.info(
                f"Email successfully sent to {recipient_email}"
            )
        else:
            logger.warning(
                f"Email delivery failed to {recipient_email}"
            )

        return {
            "recipient_email": recipient_email,
            "status": "sent" if success else "failed",
            "execution_time_seconds": execution_time
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Send email failed: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to send email"
        )
