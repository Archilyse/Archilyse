#!/usr/bin/env bash

# GCLOUD_KEY is define as environment variable in circle ci. The value is build doing `cat project_name-xxxxx.json | base64 --wrap=0`
# from the service account credentials of google cloud.
echo "${GCLOUD_SERVICE_KEY}" | base64 --decode > gcloud.json
gcloud auth activate-service-account --key-file gcloud.json
gcloud auth configure-docker
