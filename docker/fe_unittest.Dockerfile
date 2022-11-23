ARG BASE_FE_IMAGE_VERSION
ARG GCP_REGISTRY_PROJECT

FROM $GCP_REGISTRY_PROJECT/slam_base_fe:$BASE_FE_IMAGE_VERSION as base_fe

# Copy the code to where the dependencies are
COPY ui/admin /dep/admin
COPY ui/dms /dep/dms
COPY ui/dashboard /dep/dashboard
COPY ui/react-planner /dep/react-planner
COPY ui/potential-view /dep/potential-view
COPY ui/pipeline /dep/pipeline
COPY ui/common /dep/common

COPY docker/entrypoints/fe_test_entrypoint.sh /entrypoint.sh
ENTRYPOINT ["bash", "/entrypoint.sh"]
