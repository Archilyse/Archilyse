#!/usr/bin/env bash

set -e

pipeline_tests() {
  cd /dep/pipeline/ && \
  ng test --watch=false --source-map=false;ec=$?;
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "fepipeline"
  echo "EXIT WITH ${ec}"
  if [[ ${ec} -eq 2 ]]
  then
    exit 1
  else
    exit 0
  fi
}

editor_tests() {
  cd /dep/react-planner/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "feeditor"
}

potential_view_tests() {
  cd /dep/potential_view/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "fepotential"
}

common_tests() {
  cd /dep/common/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "fecommon"
}

admin_tests() {
  cd /dep/admin/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "feadminui"
}

dms_tests() {
  cd /dep/dms/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "fedms"
}

dashboard_tests() {
  cd /dep/dashboard/ && \
  npm run test
  [[ -n "${CODECOV_TOKEN}" ]] && \
  curl -s https://codecov.io/bash | bash -s - -t "${CODECOV_TOKEN}" -C "${CIRCLE_SHA1}" codecov --token "${CODECOV_TOKEN}" \
  -F "fedashboard"
}


case "$1" in
  --pipeline_tests)
    pipeline_tests
    ;;
  --editor_tests)
    editor_tests
    ;;
  --potential_view_tests)
    potential_view_tests
    ;;
  --common_tests)
    common_tests
    ;;
  --admin_tests)
    admin_tests
    ;;
  --dms_tests)
    dms_tests
    ;;
  --dashboard_tests)
    dashboard_tests
    ;;
esac
