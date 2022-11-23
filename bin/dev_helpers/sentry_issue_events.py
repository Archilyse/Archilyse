import requests

# Copy the token from https://sentry.io/settings/account/api/auth-tokens/
token_from_sentry = ""  # noqa: B105
issue_id = 1240657524


list_issues_id = f"https://sentry.io/api/0/issues/{issue_id}/events/?full=True"
issues = requests.get(
    headers={"Authorization": f"Bearer {token_from_sentry}"}, url=list_issues_id
).json()
site_ids = {issue["context"]["celery-job"]["kwargs"]["site_id"] for issue in issues}
