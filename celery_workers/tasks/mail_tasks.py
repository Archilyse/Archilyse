import os
from http import HTTPStatus

from jinja2 import Template
from python_http_client import HTTPError
from sendgrid import MailSettings, SandBoxMode, SendGridAPIClient
from sendgrid.helpers import mail as mail_helpers

from common_utils.constants import PRODUCTION_URL, get_sendgrid_email_default_sender
from common_utils.exceptions import SendGridMailException
from handlers import UserHandler
from handlers.db import UserDBHandler
from tasks.utils.constants import (
    EMAIL_CONTENT_BY_TYPE,
    EMAIL_TEMPLATE_BY_TYPE,
    EmailTypes,
    sendgrid_sandbox_mode,
)
from tasks.utils.utils import celery_retry_task


def get_email_template_by_type(email_type: EmailTypes) -> str:
    with EMAIL_TEMPLATE_BY_TYPE[email_type].open() as f:
        return f.read()


@celery_retry_task
def send_email_task(self, user_id: int, email_type: str):
    mail = get_sendgrid_mail_configured(
        user_id=user_id, email_type=EmailTypes[email_type]
    )
    try:
        response = SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"]).send(mail)
        if response.status_code != HTTPStatus.ACCEPTED:
            raise SendGridMailException(
                f"Email error: {mail}. Status code: {response.status_code}"
            )
    except HTTPError as e:
        raise SendGridMailException(f"Email error: {e.to_dict}")


def get_sendgrid_mail_configured(user_id: int, email_type: EmailTypes):
    user = UserDBHandler.get_by(id=user_id)
    activation_token = UserHandler.generate_confirmation_token(user_id=user["id"])
    redirection_address = (
        f"{PRODUCTION_URL}/dms/password/reset?token={activation_token}"
    )
    template = Template(get_email_template_by_type(email_type=email_type))
    mail = mail_helpers.Mail(
        from_email=mail_helpers.Email(get_sendgrid_email_default_sender()),
        to_emails=mail_helpers.To(user["email"]),
        subject=EMAIL_CONTENT_BY_TYPE[email_type]["subject"],
        html_content=mail_helpers.HtmlContent(
            template.render(
                redirection_address=redirection_address,
                body_content=EMAIL_CONTENT_BY_TYPE[email_type]["body_content"],
                call_to_action=EMAIL_CONTENT_BY_TYPE[email_type]["call_to_action"],
                username=user["login"],
                body_footer=EMAIL_CONTENT_BY_TYPE[email_type]["body_footer"],
            )
        ),
    )
    mail.mail_settings = MailSettings(sandbox_mode=SandBoxMode(sendgrid_sandbox_mode))
    return mail
