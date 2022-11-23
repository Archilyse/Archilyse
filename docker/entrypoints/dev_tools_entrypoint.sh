#!/usr/bin/env bash

set -e

CCRED="\e[31m"
CCYELLOW="\e[33m"
CCGREEN="\e[92m"
CCEND="\e[0m"


cli_help() {
  printf "
SLAM development tools
Commands:
  ${CCGREEN}--jupyter${CCEND}        Jupyter Notebook
  ${CCGREEN}help${CCEND}       Print help
"
  exit 1
}

jupyter_notebook(){
  printf "${CCGREEN}RUNNING JUPYTER NOTEBOOK${CCEND}\n"
  jupyter notebook --allow-root --ip='*' --NotebookApp.token='' --NotebookApp.password=''
}

case "$1" in
  --jupyter)
    jupyter_notebook
    ;;
  --bash)
    /bin/bash
    ;;
  *)
    cli_help
    ;;
esac
