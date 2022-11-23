ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim as geos_compiler
# To be removed with the pygeos integration in shapely 2.0
WORKDIR /
RUN apt-get update --no-install-recommends && \
    apt-get install -y --no-install-recommends wget cmake g++ build-essential bzip2 && \
    wget http://download.osgeo.org/geos/geos-3.10.3.tar.bz2 && \
    tar xvfj geos-3.10.3.tar.bz2 && \
    mkdir -p geos-3.10.3/build

WORKDIR /geos-3.10.3/build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local/geos && \
    make && \
    make install

FROM python:${PYTHON_VERSION}-slim as base

# Some environment vars modifiers for Python
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=1

# Add Tini
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

# Due to problems with the signature of the repos for ttf-msconrefonts we have to update twice
# and add the signature of the servers
RUN apt-get update --fix-missing --no-install-recommends && \
    apt-get install -y --no-install-recommends \
    # fonts for matplotlib
    fontconfig fonts-liberation \
    # system level tools
    wget curl unzip gnupg gnupg-agent \
    # dependencies for compiling python libraries
    build-essential \
    libcairo2-dev \
    libjpeg-dev \
    libgif-dev \
    python-dev \
    libspatialindex-dev \
    tk \
    libeigen3-dev \
    libgmp-dev \
    libgmpxx4ldbl \
    libmpfr-dev \
    libboost-dev \
    libboost-thread-dev \
    libtbb-dev \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    graphviz \
    # required for fiona and other gdal python libraries
    gdal-bin \
    libgdal-dev \
    # Needed for percy
    libgl1-mesa-dev \
    # pdf conversion dependency
    libmagickwand-dev \
    ghostscript && \
    fc-cache -f -v && \
    pip install -U --no-cache-dir ipython==8.3.0 && \
    # Install Chrome
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo deb http://dl.google.com/linux/chrome/deb/ stable main >> \
        /etc/apt/sources.list.d/google-chrome.list && \
    # wait for it tool for docker containers boot up
    wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    -P /usr/bin/ && chmod +x /usr/bin/wait-for-it.sh && \
    apt-get update -qqy && apt-get -qqy install --no-install-recommends google-chrome-stable && \
    # And clean up
    apt-get autoremove -yqq --purge && \
    apt-get clean &&  \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/* && \
    rm -rf /tmp/* && \
    # Install Ifcopenshell
    export IFC_VERSION=python-31-v0.7.0-1b1fd1e && \
    export IFC_HOME=/src/ifc_reader && \
    mkdir -p ${IFC_HOME} && \
    wget -P ${IFC_HOME} https://s3.amazonaws.com/ifcopenshell-builds/ifcopenshell-${IFC_VERSION}-linux64.zip && \
    unzip -d ${IFC_HOME} ${IFC_HOME}/ifcopenshell-${IFC_VERSION}-linux64.zip && \
    rm ${IFC_HOME}/ifcopenshell-${IFC_VERSION}-linux64.zip


WORKDIR /src

# Install python
COPY api/requirements.txt /src/api/requirements.txt
COPY brooks/requirements.txt /src/brooks/requirements.txt
COPY celery_workers/requirements.txt /src/celery_workers/requirements.txt
COPY dufresne/requirements.txt /src/dufresne/requirements.txt
COPY simulations/requirements.txt /src/simulations/requirements.txt
COPY surroundings/requirements.txt /src/surroundings/requirements.txt
COPY handlers/requirements.txt /src/handlers/requirements.txt
COPY utils/requirements.txt /src/utils/requirements.txt

# Before installing the python libraries then we copy the geos package so that ir compiles in parallel
COPY --from=geos_compiler /usr/local/geos/bin /usr/bin
COPY --from=geos_compiler /usr/local/geos/lib /usr/lib/x86_64-linux-gnu/
COPY --from=geos_compiler /usr/local/geos/include /usr/include/

## Geos is installed at system library and then shapely and pygeos are not installed with binaries
## so they can share the same GEOS version and convert quicker object among them

RUN pip install --no-cache-dir \
                -r /src/api/requirements.txt \
                -r /src/brooks/requirements.txt \
                -r /src/celery_workers/requirements.txt \
                -r /src/dufresne/requirements.txt \
                -r /src/simulations/requirements.txt \
                -r /src/handlers/requirements.txt \
                -r /src/surroundings/requirements.txt \
                -r /src/utils/requirements.txt \
                --no-binary shapely,pygeos

COPY docker/configs/image-magick-policy.xml /etc/ImageMagick-6/policy.xml
