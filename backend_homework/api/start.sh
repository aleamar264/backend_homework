#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --reload