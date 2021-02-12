#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Setup fixtures
export OPENIDC_KEY='YOUR_EXAMPLE_CLIENT_ID'
export OPENIDC_SECRET='YOUR_EXAMPLE_CLIENT_SECRET'
