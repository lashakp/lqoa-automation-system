from pipeline.personalization.generate_email import (
    generate_personalized_email
)


def run_email_generation(
    company_id,
    sender_name,
    sender_role,
    sender_company
):

    return generate_personalized_email(

        company_id=company_id,

        sender_name=sender_name,

        sender_role=sender_role,

        sender_company=sender_company
    )
