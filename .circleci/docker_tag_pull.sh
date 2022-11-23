#!/usr/bin/env bash

pip install requests
GCR_URL=$(< docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)
if [[ -z "${CIRCLE_PULL_REQUEST}" ]]; then
    export PR_NUMBER=$(python -c "import requests, os;token=os.environ['GITHUB_API_TOKEN'];print(requests.get(headers={'Authorization': 'token ' + token},url='https://api.github.com/search/issues?q=repo:Archilyse/slam+is:pr+sort:updated-desc+is:merged').json()['items'][0]['number'])")
else
    export PR_NUMBER=$(echo ${CIRCLE_PULL_REQUEST} | cut -d "/" -f 7)
fi
docker-compose -f .circleci/docker-compose-parallel-ci.yml pull

docker tag ${GCR_URL}/slam_worker:${PR_NUMBER} slam-worker
docker tag ${GCR_URL}/slam_worker:${PR_NUMBER} slam-flower
docker tag ${GCR_URL}/slam_tests:${PR_NUMBER} slam-tests
docker tag ${GCR_URL}/slam_router:${PR_NUMBER}  slam-router
docker tag ${GCR_URL}/slam_api:${PR_NUMBER} slam-api
docker tag ${GCR_URL}/slam_api:${PR_NUMBER} slam-db_migrations
