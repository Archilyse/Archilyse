ARG BASE_IMAGE_VERSION
ARG GCP_REGISTRY_PROJECT

FROM $GCP_REGISTRY_PROJECT/slam_base:$BASE_IMAGE_VERSION as base

# NOTE: Don't generate PYC during test
ENV PYTHONDONTWRITEBYTECODE=1

# hadolint ignore=SC2086
RUN CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") && \
    CHROME_DRIVER_VERSION=$(wget --no-verbose -O - \
        https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}) && \
    wget --no-verbose -O /tmp/chromedriver_linux64.zip \
        https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
    rm -rf /opt/selenium/chromedriver && \
    unzip /tmp/chromedriver_linux64.zip -d /opt/selenium && \
    mv /opt/selenium/chromedriver /usr/bin/chromedriver && \
    rm -r /tmp/chromedriver_linux64.zip /opt/selenium

# Install Node to have percy agent
RUN wget https://deb.nodesource.com/setup_14.x && bash setup_14.x && \
    apt-get install --no-install-recommends nodejs -y && \
    npm cache clean --force && npm install -g @percy/cli@v1.6.1 --unsafe-perm=true

COPY setup.cfg /src/setup.cfg

COPY tests/requirements.txt /src/tests/requirements.txt
RUN pip install -r /src/tests/requirements.txt

# Install slam packages
COPY api /src/api
COPY brooks /src/brooks
COPY celery_workers /src/celery_workers
COPY dufresne /src/dufresne
COPY simulations /src/simulations
COPY handlers /src/handlers
COPY surroundings /src/surroundings
COPY ifc_reader /src/ifc_reader
COPY utils /src/utils
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

COPY tests /src/tests
COPY bin /src/bin

WORKDIR /src
COPY docker/entrypoints/test_entrypoint.sh /entrypoint.sh
ENTRYPOINT ["bash", "/entrypoint.sh"]
