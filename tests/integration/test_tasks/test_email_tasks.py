import pytest

from common_utils.constants import get_sendgrid_email_default_sender
from common_utils.exceptions import SendGridMailException
from tasks import mail_tasks
from tasks.mail_tasks import get_sendgrid_mail_configured
from tasks.utils.constants import EMAIL_CONTENT_BY_TYPE, EmailTypes
from tests.constants import USERS
from tests.utils import create_user_context


@pytest.mark.parametrize(
    "email_type", [EmailTypes.ACTIVATION_EMAIL, EmailTypes.PASSWORD_RESET]
)
def test_email_activation_fails(celery_eager, email_type):
    context = create_user_context(USERS["ARCHILYSE_ONE_ADMIN"])
    with pytest.raises(SendGridMailException) as e:
        mail_tasks.send_email_task.delay(
            user_id=context["user"]["id"], email_type=email_type.name
        )

    # 200 is returned when sandbox is True, validates the email and returns without consuming quota.
    assert "The provided authorization grant is invalid" in str(e)


@pytest.mark.parametrize(
    "email_type", [EmailTypes.ACTIVATION_EMAIL, EmailTypes.PASSWORD_RESET]
)
def test_get_email_configured(email_type):
    context = create_user_context(USERS["ARCHILYSE_ONE_ADMIN"])
    mail = get_sendgrid_mail_configured(
        user_id=context["user"]["id"], email_type=email_type
    ).get()

    assert mail["from"]["email"] == get_sendgrid_email_default_sender()
    assert mail["personalizations"][0]["to"][0]["email"] == context["user"]["email"]
    assert (
        EMAIL_CONTENT_BY_TYPE[email_type]["body_content"] in mail["content"][0]["value"]
    )
