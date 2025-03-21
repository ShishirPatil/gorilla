#!/bin/bash

cd goex

echo "Installing mkcert"
mkcert -install

echo "Creating certificate for localhost"
mkcert localhost

echo "Allowing goex direnv"
direnv allow

echo "Creating virtual environment"
python3 -m venv goex-env
. ./goex-env/bin/activate

echo "Installing requirements"
pip install -e .
