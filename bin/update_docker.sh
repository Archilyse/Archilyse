#!/usr/bin/env bash

sudo apt-get -qq update
sudo apt-get -y -o Dpkg::Options::="--force-confnew" install docker-ce="${docker_version}" --allow-downgrades
