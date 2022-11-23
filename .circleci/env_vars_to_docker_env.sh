#!/usr/bin/env bash

# this script is intended for CI use only

# export string vars
declare -a arr=(
	"CIRCLECI"
	"CIRCLE_SHA1"
	"CIRCLE_WORKING_DIRECTORY"
	"CIRCLE_BRANCH"
	"CODECOV_TOKEN"
	"PERCY_TOKEN"
	"PERCY_PARALLEL_TOTAL"
	"PERCY_PARALLEL_NONCE"
	"GCLOUD_BUCKET"
	"GCLOUD_CLIENT_BUCKET_PREFIX"
	"GCLOUD_STORAGE_PROJECT_ID"
	"GCLOUD_STORAGE_CLIENT_ID"
	"GCLOUD_STORAGE_CLIENT_SECRET"
	"GCLOUD_STORAGE_REFRESH_TOKEN"
	"GCLOUD_IMAGE_BUCKET"
	"GCP_REGISTRY_PROJECT"
	"GCP_PROJECT_ID"
	"MAPBOX_TILES_TOKEN"
	"LOCATION_IQ_TOKEN"
	"SENTRY_DSN"
)

for var in "${arr[@]}"
do
	printf "%s=%s\n" "${var}" $(printenv ${var}) >> docker/.env.local
done
# show .env.local
cat docker/.env.local
