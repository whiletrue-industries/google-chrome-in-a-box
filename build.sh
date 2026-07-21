#!/bin/bash
# Manual build & push; CI (.github/workflows/ci.yml) does this on every push to master.
set -eu
IMAGE=${IMAGE:-ghcr.io/whiletrue-industries/google-chrome-in-a-box}
docker build . -t "${IMAGE}" --cache-from "${IMAGE}"
docker push "${IMAGE}"
