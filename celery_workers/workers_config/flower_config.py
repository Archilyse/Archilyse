import os

auto_refresh = True
inspect_timeout = 10000.0
max_tasks = 10000
persistent = False
port = int(os.environ["FLOWER_PORT"])
purge_offline_workers = 600
oauth_keys = ("FLOWER_OAUTH2_KEY", "FLOWER_OAUTH2_REDIRECT_URI", "FLOWER_OAUTH2_SECRET")
if all(os.environ.get(key) for key in oauth_keys):
    auth = ".*@archilyse.com"
else:
    basic_auth = [f'{os.environ["FLOWER_USER"]}:{os.environ["FLOWER_PASSWORD"]}']
