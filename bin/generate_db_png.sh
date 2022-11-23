#!/usr/bin/env bash

apt-get update -y -q
apt install graphviz -y -q

pip install sqlalchemy_schemadisplay

python bin/generate_db_png.py
echo 'DB .png generated'