#!/usr/bin/env bash

set -e

CCRED="\e[31m"
CCYELLOW="\e[33m"
CCGREEN="\e[92m"
CCEND="\e[0m"


cli_help() {
  printf "
SLAM API
Commands:
  ${CCGREEN}--migrations${CCEND} Run Alembic migrations
  ${CCGREEN}--downgrade${CCEND}  Downgrade migration
  ${CCGREEN}--api${CCEND}        Run API
  ${CCGREEN}--dev${CCEND}        Run flask DEV (autorestarts on code change)
  ${CCGREEN}help${CCEND}         Print help
"
  exit 1
}

migrations(){
    printf "${CCGREEN}RUNNING MIGRATIONS${CCEND}\n"
    cd /src/api/slam_api
    flask create-database-and-upgrade
    flask alembic-checks
    printf "${CCGREEN}FINISHED MIGRATIONS${CCEND}\n"
}

post_deployment_tasks(){
    printf "${CCGREEN}RUNNING POST DEPLOYMENT TASKS${CCEND}\n"
    cd /src/api/slam_api
    flask post-deployment-tasks
    printf "${CCGREEN}FINISHED POST DEPLOYMENT TASKS${CCEND}\n"
}

downgrade(){
    printf "${CCGREEN}RUNNING DOWNGRADE${CCEND}\n"

    [[ -n "${DOWNGRADE_VERSION}" ]] || \
        printf "${CCRED}Need to set DOWNGRADE_VERSION${CCEND}\n" && exit 1

    cd /src/api/slam_api
    flask alembic-downgrade-version "${DOWNGRADE_VERSION}"

    printf "${CCGREEN}FINISHED DOWNGRADE${CCEND}\n"
}

api(){
    uwsgi --socket 0.0.0.0:8000 --yaml /src/api/uwsgi.yaml
}

dev(){
    FLASK_APP=/src/api/slam_api/app.py FLASK_DEBUG=1 flask run -h 0.0.0.0 -p 8000 
}

[[ -z "${PGBOUNCER_HOST}" ]] && printf "${CCRED}Need to set PGBOUNCER_HOST${CCEND}\n" && exit 1
[[ -z "${PGBOUNCER_PORT}" ]] && printf "${CCRED}Need to set PGBOUNCER_PORT${CCEND}\n" && exit 1


bash wait-for-it.sh --timeout=10 "${PGBOUNCER_HOST}":"${PGBOUNCER_PORT}"

mkdir -p "${LOGS_DESTINATION_FOLDER}""${LOGGER_SERVICE_NAME}"/
mkdir -p /root/pysal_data


case "$1" in
  --migrations)
    migrations
    ;;
  --post_deployment_tasks)
    post_deployment_tasks
    ;;
  --downgrade)
    downgrade
    ;;
  --api)
    api
    ;;
  --dev)
    dev
    ;;
  *)
    cli_help
    ;;
esac