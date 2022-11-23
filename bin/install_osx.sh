#!/usr/bin/env bash

case $SHELL in
*/zsh)
  rc=~/.zshrc # assume Zsh
  gcloud_inc_file=~/google-cloud-sdk/path.zsh.inc
  ;;
*)
  rc=~/.bashrc # assume Bash
  gcloud_inc_file=~/google-cloud-sdk/path.bash.inc
  ;;
esac


system_dependencies() {
  if ! XCODE_VERSION=$(xcode-select --version); then
    echo "You must install Xcode in order to run this script."  
    exit 1
  else
    echo $XCODE_VERSION
  fi
  
  # Check if brew is installed
  if ! BREW_VERSION=$(brew --version); then
    echo "Installing Homebrew.."
    # Install Homebrew
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  else
    echo "Homebrew already installed."
    echo $BREW_VERSION
    brew update
  fi
  
  echo "Installing Homebrew dependencies.."
  brew install --force openssl \
  zlib \
  bzip2 \
  readline \
  sqlite \
  wget \
  curl \
  llvm \
  ncurses \
  xz \
  tcl-tk \
  nss \
  git \
  python \
  spatialindex \
  eigen \
  gmp \
  mpfr \
  boost \
  tbb \
  libffi \
  libpq \
  graphviz \
  imagemagick \
  unzip

  if ! GCLOUD_VERSION=$(gcloud --version); then
    echo "Installing Google Cloud SDK.."
    bash bin/install_gcloud.sh
    grep -qxF "source ${gcloud_inc_file}" ${rc} || echo "source ${gcloud_inc_file}" >> ${rc}
    gcloud config set project "${GCP_REGISTRY_PROJECT}"
  else
    echo "Google Cloud SDK already installed."
    echo $GCLOUD_VERSION
  fi

  if ! DOCKER_VERSION=$(docker --version); then
    echo "Installing Docker.."
    brew install --cask docker
    open /Applications/Docker.app
  else
    echo "Docker already installed."
    echo $DOCKER_VERSION
  fi
}

frontend() {

  NODE_VERSION=$(node -v)
  NPM_VERSION=$(npm -v)

  if [ -z $NODE_VERSION ] || [ -z $NPM_VERSION ]; then
    echo "Installing NodeJS and NPM.."
    brew install node
  else
    echo "NodeJS version: $NODE_VERSION"
    echo "NPM version: $NPM_VERSION"
  fi


  npm install -g typescript@4.0.3 && \
  npm install -g prettier@2.2.1 && \
  npm install -g @angular/cli@9.0.4 && \
  npm install -g @percy/cli@v1.6.1
}

case "$1" in
  --frontend)
    frontend
    ;;
  --system_dependencies)
    system_dependencies
    ;;
  *)

    system_dependencies
    frontend
esac