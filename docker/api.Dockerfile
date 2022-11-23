ARG BASE_IMAGE_VERSION
ARG GCP_REGISTRY_PROJECT
FROM $GCP_REGISTRY_PROJECT/slam_base:$BASE_IMAGE_VERSION as base

COPY api /src/api
COPY brooks /src/brooks
COPY celery_workers /src/celery_workers
COPY dufresne /src/dufresne
COPY simulations /src/simulations
COPY handlers /src/handlers
COPY surroundings /src/surroundings
COPY ifc_reader /src/ifc_reader
COPY utils /src/utils

# Install slam packages
RUN pip install --no-cache-dir \
                -e /src/api \
                -e /src/brooks \
                -e /src/celery_workers \
                -e /src/dufresne \
                -e /src/simulations \
                -e /src/handlers \
                -e /src/surroundings \
                -e /src/ifc_reader \
                -e /src/utils

COPY docker/entrypoints/api_entrypoint.sh /entrypoint.sh
WORKDIR /src

EXPOSE 8000

ENTRYPOINT ["/tini", "--", "/bin/bash", "/entrypoint.sh"]
