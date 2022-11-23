#!/usr/bin/env bash

pip install requests

GCR_URL=$(< docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2) && \
GITHUB_PR_ID=$(python -c "import requests, os;token=os.environ['GITHUB_API_TOKEN'];print(requests.get(headers={'Authorization': 'token ' + token},url='https://api.github.com/search/issues?q=repo:Archilyse/slam+is:pr+sort:updated-desc+is:merged').json()['items'][0]['number'])")

echo "export SLAM_VERSION=$GITHUB_PR_ID" >> $BASH_ENV
echo "export SLAM_COMMIT_VERSION=$CIRCLE_SHA1" >> $BASH_ENV

docker pull ${GCR_URL}/infrastructure:latest
docker run -e VAULT_PASSWORD=$VAULT_PASSWORD \
           -e SLAM_VERSION=$GITHUB_PR_ID \
           -e SLAM_COMMIT_VERSION=$CIRCLE_SHA1 \
           -e CIRCLE_USERNAME=$CIRCLE_USERNAME \
           ${GCR_URL}/infrastructure:latest --deployment