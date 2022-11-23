#!/usr/bin/env bash

if [[ -z "${CIRCLE_PULL_REQUEST}" ]]
then
    echo "\CIRCLE_PULL_REQUEST is empty. Skipping docker tag and push as we are on develop"
else
    GCR_URL=$(< docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)
    PR_NUMBER=$(echo ${CIRCLE_PULL_REQUEST} | cut -d "/" -f 7)
    
    docker tag slam_worker ${GCR_URL}/slam_worker:${PR_NUMBER} &&
    docker tag slam_worker ${GCR_URL}/slam_worker:${CIRCLE_SHA1} &&
    docker push ${GCR_URL}/slam_worker:${PR_NUMBER} &&
    docker push ${GCR_URL}/slam_worker:${CIRCLE_SHA1}
    
    docker tag slam_tests ${GCR_URL}/slam_tests:${PR_NUMBER} &&
    docker tag slam_tests ${GCR_URL}/slam_tests:${CIRCLE_SHA1} &&
    docker push ${GCR_URL}/slam_tests:${PR_NUMBER} &&
    docker push ${GCR_URL}/slam_tests:${CIRCLE_SHA1}
    
    docker tag slam_router ${GCR_URL}/slam_router:${PR_NUMBER} &&
    docker tag slam_router ${GCR_URL}/slam_router:${CIRCLE_SHA1} &&
    docker push ${GCR_URL}/slam_router:${PR_NUMBER} &&
    docker push ${GCR_URL}/slam_router:${CIRCLE_SHA1}
    
    docker tag slam_api ${GCR_URL}/slam_api:${PR_NUMBER} &&
    docker tag slam_api ${GCR_URL}/slam_api:${CIRCLE_SHA1} &&
    docker push ${GCR_URL}/slam_api:${PR_NUMBER} &&
    docker push ${GCR_URL}/slam_api:${CIRCLE_SHA1}
fi
