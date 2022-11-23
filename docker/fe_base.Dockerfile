ARG NODE_VERSION

FROM selenium/standalone-chrome:87.0-20201119 as chrome_driver

FROM node:$NODE_VERSION as js_dependencies
# Instal Chrome for angular tests
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo deb http://dl.google.com/linux/chrome/deb/ stable main >> \
    /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update -qqy && apt-get -qqy install --no-install-recommends google-chrome-stable && \
    # And clean up
    apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/* && rm -rf /tmp/* && \
    npm install -g npm@8.5.1 && \
    npm install -g @angular/cli@9.0.4

COPY --from=chrome_driver /usr/bin/chromedriver /usr/bin/chromedriver

RUN npm set progress=false && npm config set depth 0

# Root dependencies
COPY /ui/package* /dep/

# Common files and dependencies
COPY /ui/common/ /dep/common/
COPY /ui/common/package* /dep/common/

# Admin dependencies
COPY /ui/admin/package* /dep/admin/

# DMS dependencies
COPY /ui/dms/package* /dep/dms/

# Dashboard dependencies
COPY /ui/dashboard/package*.json /dep/dashboard/

# Pipeline dependencies
COPY ui/pipeline/package* /dep/pipeline/
COPY ui/pipeline/angular.json ui/pipeline/tsconfig.json /dep/pipeline/

# Editor V2 dependencies
COPY ui/react-planner/package* /dep/react-planner/

# Potential view V2 dependencies
COPY ui/potential-view/package* /dep/potential-view/

# To ensure a clean installation
RUN npm cache clean --force

# Install dependencies in the root
WORKDIR /dep/
RUN npm ci

WORKDIR /dep/common/
RUN npm run build

WORKDIR /dep/pipeline/
RUN npm ci
