#!make

########################################################################################
# Makefile internals								 								   #
########################################################################################
unameOut=$(shell uname -s)
SHELL := /bin/bash
ifeq ($(unameOut), Darwin)
	SHELL := $(shell echo ${SHELL})
	COMPOSE_DOCKER_CLI_BUILD=0
	DOCKER_BUILDKIT=0
	GCLOUD_INC_FILE=~/google-cloud-sdk/path.zsh.inc
else
	COMPOSE_DOCKER_CLI_BUILD=1
	DOCKER_BUILDKIT=1
	GCLOUD_INC_FILE=~/google-cloud-sdk/path.bash.inc
endif

python_executable := python3.10

CCRED := \e[31m
CCYELLOW := \e[33m
CCGREEN := \e[92m
CCEND := \e[0m

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

########################################################################################
# Docker clean up targets
########################################################################################
docker_cleanup: docker_down # Clean up docker images, containers, etc
	docker system prune -f

docker_full_cleanup: docker_down
	docker system prune -f --all

housekeeping_docker_registry:
	@echo infastructure slam_api slam_base slam_base_fe slam_router slam_tests slam_worker | xargs -n 1 -I %  \
	bin/housekeeping_registry_images.sh \
	 $(shell < docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)/%

########################################################################################
# Docker-compose targets
########################################################################################
#
# Original docker-compose file, same as used in CircleCI
#
DOCKER_CI := COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) DOCKER_BUILDKIT=${DOCKER_BUILDKIT} docker-compose --project-directory docker -f docker/docker-compose.yml
#
# Tweaked docker-compose file, for development only
#
DOCKER_DEV := COMPOSE_DOCKER_CLI_BUILD=$(COMPOSE_DOCKER_CLI_BUILD) DOCKER_BUILDKIT=${DOCKER_BUILDKIT} docker-compose --project-directory docker -f docker/dev-docker-compose.yml
USER_ID := "$(shell id -u):$(shell id -g)"

build: docker_build ## Docker-compose build alias
GCLOUD_AUTH := source $(shell echo ${GCLOUD_INC_FILE}) && CLOUDSDK_CORE_DISABLE_PROMPTS=1 gcloud auth configure-docker
DOCKER_DEV_BUILD_PARALLEL := $(DOCKER_DEV) build --parallel \
		--build-arg $(shell < docker/.env grep BASE_IMAGE_VERSION | xargs) \
		--build-arg $(shell < docker/.env grep BASE_FE_IMAGE_VERSION | xargs) \
		--build-arg $(shell < docker/.env.local grep GCP_REGISTRY_PROJECT | xargs)

DOCKER_TAGS := docker tag slam_api slam_db_migrations && \
               docker tag slam_worker slam_flower
DOCKER_ENV_ARGS := $(shell < docker/.env xargs) $(shell < docker/.env.local xargs)
GCP_PROJECT_ID = $(shell < docker/.env.local grep GCP_PROJECT_ID | cut -d "=" -f 2)
POSTGRES_DB_INSTANCE = $(shell < .env/.stag_args grep POSTGRES_DB_INSTANCE | cut -d "=" -f 2)
GCP_REGISTRY_PROJECT := $(shell < docker/.env.local grep GCP_REGISTRY_PROJECT | cut -d "=" -f 2)
BASE_FE_VERSION := $(shell < docker/.env grep BASE_FE_IMAGE_VERSION | cut -d "=" -f 2)
BASE_BE_VERSION := $(shell < docker/.env grep BASE_IMAGE_VERSION | cut -d "=" -f 2)
BASE_FE_IMAGE := ${GCP_REGISTRY_PROJECT}/slam_base_fe:${BASE_FE_VERSION}
BASE_PYTHON_IMAGE := ${GCP_REGISTRY_PROJECT}/slam_base:${BASE_BE_VERSION}
NODE_VERSION := 14.20.0
PYTHON_VERSION := 3.10.5

POSTGRES_STAG_PASSWORD := $(shell < .env/.stag_args grep POSTGRES_PASSWORD | sed -e "s/POSTGRES_PASSWORD=//g")

DOCKER_STAG_ARGS := $(shell < .env/.stag_args xargs -0 | sed 's/^/-e /') -e PGBOUNCER_HOST="postgres_stag" -e CELERY_EAGER="True"
STAG_ARGS := $(shell < .env/.stag_args xargs -0)
LOCAL_ARGS := $(shell < .env/.local_args xargs -0)

API_STAGING := $(DOCKER_DEV) run --rm $(DOCKER_STAG_ARGS) --workdir=/src/api/slam_api -e FLASK_DEBUG=1 -e CELERY_EAGER=True --entrypoint flask api
API_LOCAL := $(DOCKER_DEV) run --rm --service-ports --workdir=/src/api/slam_api -e FLASK_DEBUG=1 -e CELERY_EAGER=True --entrypoint flask api
API_LOCAL_DEFAULT_ENTRY := $(DOCKER_DEV) run --rm --service-ports --workdir=/src/api/slam_api -e FLASK_DEBUG=1 -e CELERY_EAGER=True  api
API_STAG_DEFAULT_ENTRY := $(DOCKER_DEV) run --rm $(DOCKER_STAG_ARGS) --service-ports --workdir=/src/api/slam_api -e FLASK_DEBUG=1 -e CELERY_EAGER=True  api
DEV_TOOLS_STAGING := $(DOCKER_DEV) run --rm --service-ports $(DOCKER_STAG_ARGS) --workdir=/src/ -e FLASK_DEBUG=1 -e CELERY_EAGER=True dev_tools
DEV_TOOLS_LOCAL := $(DOCKER_DEV) run --rm --service-ports --workdir=/src/ -e FLASK_DEBUG=1 -e CELERY_EAGER=True dev_tools

build_base_image:  ## Build the base image
	DOCKER_BUILDKIT=${DOCKER_BUILDKIT} docker build --build-arg PYTHON_VERSION=${PYTHON_VERSION} -f docker/slam_base.Dockerfile  -t \
	${BASE_PYTHON_IMAGE} .

build_base_fe_image:  ## Build the base image for FE dependencies
	DOCKER_BUILDKIT=${DOCKER_BUILDKIT} docker build --build-arg NODE_VERSION=${NODE_VERSION} -f docker/fe_base.Dockerfile -t \
	${BASE_FE_IMAGE} .

docker_build: ## Docker compose build with CI settings
	$(GCLOUD_AUTH) && \
	$(DOCKER_DEV_BUILD_PARALLEL) fe_unittest worker api tests router
	$(DOCKER_TAGS)

docker_build_no_cache: ## Docker compose build with CI settings
	$(GCLOUD_AUTH) && \
	$(DOCKER_DEV_BUILD_PARALLEL) --no-cache fe_unittest worker api tests router && \
	$(DOCKER_TAGS)

docker_restart_router: ## Docker compose build with CI settings
	$(DOCKER_DEV) kill router

up: docker_build docker_up  ## Docker-compose up alias

docker_up:  ## Docker compose up all services with CI settings
	$(DOCKER_DEV) up --remove-orphans router api worker

docker_up_daemonize:  ## Docker compose up all services with CI settings
	$(DOCKER_DEV) up -d --remove-orphans router api worker

docker_down:
	$(DOCKER_DEV) down -v --remove-orphans

docker_logs_full:
	$(DOCKER_CI) logs api worker router db_migrations

docker_tail_logs:
	$(DOCKER_CI) logs -f --tail 20

docker_nginx_logs:
	docker exec -it slam_router_1 tail -f /var/log/nginx/nginx_access.log

docker_api_bash: ## Run and execute into the API container
	$(DOCKER_DEV) run --rm --service-ports --entrypoint bash api

docker_api_stag_bash: db_stag_proxy_up ## Run and execute into the SLAM with stag DB settings
	$(DOCKER_DEV) run --rm \
	$(DOCKER_STAG_ARGS) \
	--service-ports --entrypoint bash api

docker_test_bash: ## Run and execute into the test container
	$(DOCKER_DEV) run --service-ports --entrypoint bash tests

docker_worker_bash: ## Run and execute into the test container
	$(DOCKER_DEV) run --service-ports --entrypoint bash worker

########################################################################################
# Migration targets
########################################################################################
alembic_upgrade_local: db_up
	$(API_LOCAL) create-database-and-upgrade

alembic_upgrade_staging:
	$(API_STAGING) create-database-and-upgrade

alembic_downgrade_local: db_up
	$(API_LOCAL) alembic-downgrade-version "base"

alembic_downgrade_staging:
	$(API_STAGING) alembic-downgrade-version "base"

alembic_checks_local: alembic_upgrade_local
	$(API_LOCAL) alembic-checks

alembic_checks_staging: alembic_upgrade_staging
	$(API_STAGING) alembic-checks

alembic_new_migration_file_local: alembic_upgrade_local
	$(API_LOCAL) alembic-autogenerate-revision
	# --user=$(USER_ID) doesn't work yet as we need root inside of the container as of now

alembic_new_migration_file_staging: alembic_upgrade_staging
	$(API_STAGING) alembic-autogenerate-revision
	# --user=$(USER_ID) doesn't work yet as we need root inside of the container as of now

########################################################################################
# Local testing targets
########################################################################################
fe_test_locally: test_common_ui test_admin_ui test_dms_ui test_dashboard_ui test_react_planner_ui test_potential_view_ui test_pipeline_ui

# To see snapshots in percy.io, set PERCY_TOKEN (found in percy.io project settings) in .env.local to work
percy_locally:  docker_restart_router docker_build docker_up_daemonize
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	percy exec pytest tests/percy_tests/ -s --pdb --lf || true

python_e2e_locally:  docker_build docker_up_daemonize
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	pytest tests/e2e_python/ -m "not quavis" -s --pdb --maxfail=3 --durations=0 || true

e2e_locally:  docker_restart_router docker_build docker_up_daemonize
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	pytest tests/e2e_browser/ -m "not quavis" -s --pdb --maxfail=3 --durations=0 || true

integrationtest: db_up redis_up
	$(DOCKER_DEV) run --no-deps --entrypoint pytest tests tests/integration/ -m "not slow" --maxfail=30 -n auto -s --lf || true

integrationtest_locally: db_up redis_up
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	COVERAGE_FILE=.coverage_integrationtests \
	pytest tests/integration/ -m "not slow and not vtk" --maxfail=30 -s --lf -n auto || true

integrationtest_locally_with_quavis: db_up redis_up
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	pytest --maxfail=3 -s tests/integration/ --lf --quavis -m quavis_test || true

unittest:
	$(DOCKER_DEV) run --no-deps --entrypoint pytest tests tests/unittests/ --maxfail=3 -n auto --lf || true

unittest_locally:
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	COVERAGE_FILE=.coverage_unittests \
	pytest tests/unittests/ -m "not slow and not vtk" --maxfail=60 -s --lf -n auto || true

remove_after_tests:
	rm .coverage -f && rm coverage.xml -f && \
	rm tests/test_stats.xml -f

########################################################################################
# Coverage Targets
########################################################################################

python_coverage_locally:
	rm -r .pytest_cache || true
	make unittest_locally
	make integrationtest_locally
	coverage combine .coverage_unittests .coverage_integrationtests
	coverage report
	rm .coverage* coverage.xml

fe_coverage_locally: test_common_ui test_admin_ui test_dms_ui test_dashboard_ui test_react_planner_ui test_pipeline_ui
	cd ui && \
		npx istanbul-merge ./*/coverage/coverage-final.json --out coverage.json && \
		npx istanbul report --include coverage.json text-summary && \
		rm -r ./*/coverage coverage.json

########################################################################################
# CI test targets
########################################################################################
build_fe_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_DEV_BUILD_PARALLEL) fe_unittest

ci_fe_all_unittests: build_fe_unittests
	$(MAKE) ci_fe_admin_unittests
	$(MAKE) ci_fe_dms_unittests
	$(MAKE) ci_fe_dashboard_unittests
	$(MAKE) ci_fe_pipeline_unittests
	$(MAKE) ci_fe_editor_unittests
	$(MAKE) ci_fe_common_unittests

ci_fe_dms_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --dms_tests

ci_fe_admin_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --admin_tests

ci_fe_dashboard_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --dashboard_tests

ci_fe_pipeline_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --pipeline_tests

ci_fe_editor_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --editor_tests

ci_fe_common_unittests:
	$(GCLOUD_AUTH) && \
	$(DOCKER_CI) run --no-deps --rm fe_unittest --common_tests

ci_unittests: ## Run CI Python unit tests
	$(DOCKER_CI) run --rm --no-deps tests --unittests

ci_integrationtests: ## Run CI integration tests
	$(DOCKER_CI) run --rm tests --integrationtests

ci_e2e_browser_tests: docker_restart_router ## Run CI E2E browser tests
	$(DOCKER_CI) run --rm tests --e2e_browser_tests

ci_e2e_python_tests: docker_restart_router ## Run CI E2E python tests
	$(DOCKER_CI) run --rm tests --e2e_python_tests

ci_percytests: ## Run CI E2E tests
	$(DOCKER_CI) run --rm tests --percytests

ci_migration_tests: ## Run CI Migration tests
	$(DOCKER_CI) up --exit-code-from db_migrations db_migrations

ci_all_tests:  ## Run all CI tests
	$(MAKE) ci_migration_tests
	$(MAKE) ci_unittests
	$(MAKE) ci_integrationtests
	$(MAKE) ci_e2e_browser_tests
	$(MAKE) ci_e2e_python_tests
	$(MAKE) ci_fe_unittests

########################################################################################
# development environments NOTE: this will create a container `dev_tools` that can be
# used to attach Visual Studio Code using the Remote Development Extension (use the 
# `Attach Running Container` action)
########################################################################################
dev_env_jupyter_stag:
	$(DEV_TOOLS_STAGING) --jupyter

dev_env_bash_local:
	$(DEV_TOOLS_LOCAL) --bash

########################################################################################
# static code analysis
########################################################################################
lint_fe:
	cd ui && npm run lint:ci || exit 1 ; \
	cd pipeline && npm run lint || exit 1 ; \

format_fe:  ## Format FE code
	cd ui && npm run prettier:all:write && npm run lint:all:fix

## Check FE code linting & format
static_analysis_fe: lint_fe
	cd ui && npm run prettier:all:check

format:  ## Format BE code by using Black
	black . --exclude='.venv/|node_modules|ifc_reader/ifc_reader/ifcopenshell/'

format_be: format  ## Alias to 'format'

isort:  ## Format BE imports by using isort
	isort api bin brooks celery_workers dufresne handlers surroundings ifc_reader simulations tests utils

static_analysis:  ## Check BE code with flake8
	flake8 && mypy

check_static: isort format static_analysis

docker_lint: ./docker/*Dockerfile  ## Run Dockerfiles linter
	@for file in $^ ; do \
		printf "$(CCBLUE)Testing $${file}${CCEND}"; \
	    docker run -i hadolint/hadolint:v1.19.0-alpine hadolint \
	    	--ignore DL4006 --ignore DL3008 --ignore DL3018 - \
	    	 <  $${file} ||  exit 1; \
	    printf "$(CCGREEN) OK$(CCEND)\n";\
	done

########################################################################################
# Frontend commands
########################################################################################
fixtures_pipeline: db_up flower_up redis_up
	$(DOCKER_ENV_ARGS) \
	$(DOCKER_DEV) run --no-deps -e LOGGER_LEVEL=DEBUG --entrypoint pytest tests -m "local_ui_tests" tests/e2e_browser/utils_admin.py::test_local_pipeline_ui

fixtures_dms_dashboard: db_up flower_up redis_up
	$(DOCKER_ENV_ARGS) \
	$(DOCKER_DEV) run --no-deps -e LOGGER_LEVEL=DEBUG --entrypoint pytest tests -m "local_ui_tests" tests/e2e_browser/utils_admin.py::test_local_dashboard_dms_ui

fixtures_dxf: db_up flower_up redis_up
	$(DOCKER_ENV_ARGS) \
	$(DOCKER_DEV) run --no-deps -e LOGGER_LEVEL=INFO --entrypoint pytest tests -m "local_ui_tests" tests/e2e_browser/utils_admin.py::test_import_dxf

upgrade_npm:
	npm install -g npm@8.5.1

install_clean_fe_dependencies:
	cd ui && npm run clean && cd ..
	$(MAKE) install_fe_dependencies

install_fe_dependencies:
	cd ui && npm install

build_common:
	npm run build --prefix ui/common

test_common_ui:
	npm run test --prefix ui/common

test_admin_ui:
	npm run test --prefix ui/admin

test_dms_ui:
	npm run test --prefix ui/dms

test_dashboard_ui:
	npm run test --prefix ui/dashboard

test_react_planner_ui:
	DEBUG_PRINT_LIMIT=2000000 npm run test --prefix ui/react-planner

test_potential_view_ui:
	npm run test --prefix ui/potential-view

test_pipeline_ui:
	cd ui/pipeline && ng test --watch=false

snapshots_dashboard_update: build_common
	npm run test --prefix ui/dashboard -- -u

locust_local: fixtures_dms_dashboard docker_up_daemonize
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	locust --config=tests/load_testing/locust.conf

########################################################################################
# bin commands
########################################################################################
generate_db_png: alembic_upgrade_local
	$(DOCKER_DEV) run --rm -v $(shell pwd)/documentation:/src/documentation/ --entrypoint bash api bin/generate_db_png.sh

install:
    # Example of how to install python interpreter and libraries
	GCP_REGISTRY_PROJECT=${GCP_REGISTRY_PROJECT} PYTHON_VERSION=${PYTHON_VERSION}  NODE_VERSION=${NODE_VERSION} bash bin/install_ubuntu.sh --python

digitization_partner_import:  ## Creates a folder by site with only the output vectors. Change STAG variables
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	TEST_ENVIRONMENT="False" \
	GOOGLE_GEOCODE_API_KEY="AIzaSyCQxfcx5gZAWyLl3sE04vcUcJOuHJPmpR8" \
	$(python_executable) bin/digitization_partner_importer/digitization_partner_site_building_import_from_qa.py

digitization_partner_import_dxfs:  ## Generate annotations for all the dxf/dwg files contained in the folder. Change STAG variables
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	TEST_ENVIRONMENT="False" \
	LOGGER_LEVEL=INFO \
	$(python_executable) bin/digitization_partner_importer/import_files_from_folder.py

annotations_migration:
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	LOGGER_LEVEL=DEBUG \
	$(python_executable) bin/annotations/migrate_python_fixtures.py && \
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	LOGGER_LEVEL=DEBUG \
	$(python_executable) bin/annotations/migrate_js_fixtures.py

generate_3d_surroundings: db_stag_proxy_up
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	LOGGER_LEVEL=DEBUG \
	$(python_executable) -W ignore bin/surroundings_utils/generate_3d_surroundings.py

sl_sia_areas:
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	LOGGER_LEVEL=DEBUG \
	$(python_executable) -W ignore bin/portfolio_client/sia_areas.py

noise_heatmap:  ## Noise heatmap per unit
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	LOGGER_LEVEL=DEBUG \
	$(python_executable) -W ignore bin/noise_utils/generate_unit_noise_heatmap.py

train_classifiers_stag: db_stag_proxy_up
	$(DOCKER_DEV) \
	run --rm -v $(shell pwd)/brooks/brooks/data/classifiers:/usr/classifiers/ \
	$(DOCKER_STAG_ARGS) \
	--entrypoint python \
	api bin/dev_helpers/train_area_classifiers.py

query_report: db_stag_proxy_up
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	$(python_executable) bin/reports/gross_m2_by_site.py --investors

investors_key_points_report:
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	$(python_executable) bin/reports/investors_monthly_report_summary.py --repo "deep-learning"

era_report: db_stag_proxy_up
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	$(python_executable) handlers/handlers/energy_reference_area/main_report.py

run_potential_ch:
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	CELERY_EAGER="False" \
	$(python_executable) bin/potential/run_all_potential_switzerland.py

ph2022_api_request: db_stag_proxy_up
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	$(python_executable) bin/ph2022_api_request.py

profiling:
	$(DOCKER_ENV_ARGS) \
	WORKING_DIR=$(shell echo ${HOME}/slam_data/) \
	$(STAG_ARGS) \
	$(python_executable) -m cProfile -o prof/myLog.profile bin/profiling/code_to_profile.py \
	&& gprof2dot -f pstats prof/myLog.profile -o prof/callingGraph.dot \
	&& dot -Tsvg prof/callingGraph.dot > prof/profile.svg \
	&& xdg-open prof/profile.svg

########################################################################################
# Local targets
########################################################################################
run_common_ui_library: build_common
	npm run dev --prefix ./ui/common

run_admin_ui_locally: build_common
	npm run dev --prefix ui/admin

run_dms_ui_locally: build_common
	npm run dev --prefix ui/dms

run_dashboard_ui_locally: build_common
	npm run dev --prefix ui/dashboard

run_react_planner_ui_locally: build_common
	npm run dev --prefix ui/react-planner

run_potential_view_ui_locally: build_common
	npm run dev --prefix ui/potential-view

run_pipeline_ui_locally:
	cd ui/pipeline && npm i --no-save && npm run dev-8000

run_api_autoload: alembic_upgrade_local
	$(API_LOCAL_DEFAULT_ENTRY) --dev || (printf \
		"$(CCYELLOW)Have you run $(CCYELLOW) docker kill slam_api_1 $(CCYELLOW)first? $(CCEND)"\
		; exit 1)

run_api_stag_autoload: db_stag_proxy_up
	$(API_STAG_DEFAULT_ENTRY) --dev || (printf \
		"$(CCYELLOW)Have you run $(CCYELLOW) docker kill slam_api_1 $(CCYELLOW)? $(CCEND)"\
		; exit 1)

run_flask_locally: alembic_upgrade_local
	$(DOCKER_ENV_ARGS) \
	$(LOCAL_ARGS) \
	CELERY_EAGER=True \
	FLASK_DEBUG=1 \
	FLASK_APP=api/slam_api/app.py \
	flask run -h 0.0.0.0 -p 8000

ipython_local:
	$(DOCKER_ENV_ARGS) $(LOCAL_ARGS) CELERY_EAGER="false" ipython

ipython_stag: db_stag_proxy_up
	$(DOCKER_DEV) run --rm \
	$(DOCKER_STAG_ARGS) \
	--entrypoint ipython api

ipython_stag_local: db_stag_proxy_up
	$(DOCKER_ENV_ARGS) $(STAG_ARGS) CELERY_EAGER="false" ipython

########################################################################################
# Database
########################################################################################
db_download_site_info:  ## Download SITE info and apply to local env
	$(DOCKER_DEV) run --rm \
    $(DOCKER_STAG_ARGS) \
    -e GCLOUD_BUCKET="test_$(USER)" \
    -e GCLOUD_CLIENT_BUCKET_PREFIX="test_client_$(USER)" \
    --entrypoint python api bin/dev_helpers/download_site_info.py || (printf \
    	"$(CCYELLOW)Have you run make $(CCYELLOW)db_clean $(CCYELLOW)first? $(CCEND)"\
		; exit 1)

db_up:  ## Start up Postgres and PGBouncer
	$(DOCKER_DEV) up --remove-orphans -d pgbouncer

db_stag_proxy_up:
	GCP_PROJECT_ID=$(GCP_PROJECT_ID) POSTGRES_DB_INSTANCE=$(POSTGRES_DB_INSTANCE) $(DOCKER_DEV) up -d postgres_stag

db_stag_proxy_down:
	$(DOCKER_DEV) down postgres_stag

redis_up:  ## Start up redis
	$(DOCKER_DEV) up --remove-orphans -d redis

flower_up:  ## Start up flower as it is required for the test recipes
	$(DOCKER_DEV) up --remove-orphans -d flower

db_clean:  ## Delete DB and apply migrations
	$(DOCKER_DEV) rm -f -s postgres
	$(MAKE) alembic_upgrade_local

db_console:  ## Connect to docker Postgres
	$(DOCKER_DEV) run --rm postgres psql --dbname=postgresql://postgres:changeme@postgres:5432/slam

db_console_stag: db_stag_proxy_up ## Connect to local docker proxy for stag
	$(DOCKER_DEV) run postgres psql --dbname=postgresql://postgres:$(POSTGRES_STAG_PASSWORD)@postgres_stag:2345/slam


########
#  Dev commands
########
ESLINT_PACKAGES := react@16.13.1 eslint@7.10.0 eslint-config-prettier@6.12.0 eslint-plugin-prettier@3.1.4 eslint-plugin-react@7.21.4 eslint-plugin-react-hooks@4.1.2 typescript@4.0.3 @typescript-eslint/parser@4.4.0 @typescript-eslint/eslint-plugin@4.4.0

install_lint_requirements:
	cd ui && npm ci lerna@3.22.1 prettier@2.2.1 $(ESLINT_PACKAGES) --no-package-lock ; \
	cd pipeline && npm ci @angular/cli@9.0.4 ; \

python_dependencies_check:
	pip-compile dev_requirements.txt --generate-hashes --dry-run

######
#  OSX commands
######
install_osx:
	export GCP_REGISTRY_PROJECT=${GCP_REGISTRY_PROJECT} ; \
	bash bin/install_osx.sh ;
