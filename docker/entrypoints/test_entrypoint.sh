#!/usr/bin/env bash

set -e


CCRED="\e[31m"
CCYELLOW="\e[33m"
CCGREEN="\e[92m"
CCEND="\e[0m"


cli_help() {
  printf "
SLAM tests
Commands:
  ${CCGREEN}--unittests${CCEND}        BE unit tests
  ${CCGREEN}--integrationtests${CCEND} BE integration tests
  ${CCGREEN}--e2e_browser_tests${CCEND}  Browser e2e tests
  ${CCGREEN}--e2e_python_tests${CCEND}   BE e2e tests
  ${CCGREEN}--percytests${CCEND}       percy tests
  ${CCGREEN}help${CCEND}       Print help
"
  exit 1
}

unittests(){
  printf "${CCGREEN}RUNNING BE UNITTESTS${CCEND}\n"

  if [[ -f "$TEST_SPLITTING_FILE" ]]
  then
    # shellcheck disable=SC2002
    cat "$TEST_SPLITTING_FILE" | xargs pytest -p no:sugar -n auto
  else
    pytest -p no:sugar tests/unittests/ -n auto
  fi
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "pythonunittests"
}

integrationtests(){
  printf "${CCGREEN}RUNNING INTEGRATION TESTS${CCEND}\n"

  bash wait-for-it.sh --timeout=10 "${PGBOUNCER_HOST}":"${PGBOUNCER_PORT}"

  if [[ -f "$TEST_SPLITTING_FILE" ]]; then
    # shellcheck disable=SC2002
    cat "$TEST_SPLITTING_FILE" | xargs pytest -p no:sugar -m "not vtk" -n auto
  else
    pytest -p no:sugar -m "not vtk" tests/integration/ -n auto
  fi
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "pythonintegration"
}

e2e_browser_tests(){
  printf "${CCGREEN}RUNNING E2E BROWSER TESTS${CCEND}\n"

  bash wait-for-it.sh --timeout=10 "${PGBOUNCER_HOST}":"${PGBOUNCER_PORT}"
  bash wait-for-it.sh --timeout=80 "${FLOWER_HOST}":"${FLOWER_PORT}"

  if [[ -f "$TEST_SPLITTING_FILE" ]]; then
    # shellcheck disable=SC2002
    pytest -p no:sugar $(cat $TEST_SPLITTING_FILE);ec=$?;

    echo "EXIT WITH ${ec}"
    if [[ ${ec} -eq 5 ]]
    then
      exit 0
    else
      exit ${ec}
    fi

  else
    pytest -p no:sugar tests/e2e_browser/ --maxfail=10
  fi
}

e2e_python_tests(){
  printf "${CCGREEN}RUNNING E2E PYTHON TESTS${CCEND}\n"

  bash wait-for-it.sh --timeout=10 "${PGBOUNCER_HOST}":"${PGBOUNCER_PORT}"
  bash wait-for-it.sh --timeout=80 "${FLOWER_HOST}":"${FLOWER_PORT}"

  if [[ -f "$TEST_SPLITTING_FILE" ]]; then
    # shellcheck disable=SC2002
    pytest -p no:sugar $(cat $TEST_SPLITTING_FILE);ec=$?;

    echo "EXIT WITH ${ec}"
    if [[ ${ec} -eq 5 ]]
    then
      exit 0
    else
      exit ${ec}
    fi

  else
    pytest -p no:sugar tests/e2e_python/ --maxfail=10
  fi
}

percytests(){
  printf "${CCGREEN}RUNNING percy TESTS${CCEND}\n"
  bash wait-for-it.sh --timeout=10 "${PGBOUNCER_HOST}":"${PGBOUNCER_PORT}"

  # shellcheck disable=SC2002
  export PERCY_BRANCH=$CIRCLE_BRANCH

  if [[ -f "$TEST_SPLITTING_FILE" ]]; then
    # shellcheck disable=SC2002
    percy exec pytest -p no:sugar $(cat $TEST_SPLITTING_FILE);ec=$?;

    echo "EXIT WITH ${ec}"
    if [[ ${ec} -eq 5 ]]
    then
      exit 0
    else
      exit ${ec}
    fi

  else
    percy exec pytest -p no:sugar tests/percy_tests/
  fi
}


case "$1" in
  --unittests)
    unittests
    ;;
  --integrationtests)
    integrationtests
    ;;
  --e2e_browser_tests)
    e2e_browser_tests
    ;;
  --e2e_python_tests)
    e2e_python_tests
    ;;
  --percytests)
    percytests
    ;;
  *)
    cli_help
    ;;
esac
