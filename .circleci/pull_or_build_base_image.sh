#!/usr/bin/env bash

# shellcheck disable=SC2046
docker pull $(< docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)/slam_base:$(< docker/.env grep BASE_IMAGE_VERSION | cut -d "=" -f 2)
if [[ $? -ne 0 ]]; then
    make build_base_image
    docker push $(< docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)/slam_base:$(< docker/.env grep BASE_IMAGE_VERSION | cut -d "=" -f 2)
fi
