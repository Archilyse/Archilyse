#!/usr/bin/env bash
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_PYTHON_SITEPACKAGES=1

if [[ ! -d ${HOME}/google-cloud-sdk/ ]]; then
     curl https://sdk.cloud.google.com | bash;
else
    source $HOME/google-cloud-sdk/path.bash.inc
    gcloud components update
fi
