#!/bin/bash
set -u

PORT=${1}
DOWNLOADS_PORT=${2}
INITIAL=${3}

# Chrome only ever listens on the loopback interface, so the debugging port is
# published through socat.
INTERNAL_PORT=19222

echo "HI! LISTENING ON" ${PORT} ${DOWNLOADS_PORT}
echo "SCREENSHOT http://localhost:${DOWNLOADS_PORT}/screenshot"
echo "INITIAL PAGE" ${INITIAL}

# Derived from the Chrome actually installed in the image: a pinned version
# string eventually contradicts the sec-ch-ua client hints Chrome sends from its
# real version, which is exactly what bot protection looks for. Override by
# passing USER_AGENT to `docker run -e`.
CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+(\.[0-9]+){3}')
USER_AGENT=${USER_AGENT:-"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${CHROME_VERSION} Safari/537.36 datagov-external-client"}
echo "USER AGENT" "${USER_AGENT}"

wait_for_cdp() {
    for _ in $(seq 1 60); do
        if curl -sf "http://127.0.0.1:${1}/json/version" > /dev/null; then
            return 0
        fi
        sleep 1
    done
    echo "TIMED OUT waiting for CDP on ${1}" >&2
    return 1
}

mkdir -p /downloads /userdata
(cd /downloads && exec python3 /app/server.py ${DOWNLOADS_PORT}) &

python3 /app/fix_profile.py

socat tcp-listen:${PORT},fork,reuseaddr tcp:127.0.0.1:${INTERNAL_PORT} &

# `exec` so that $! is Chrome itself rather than the subshell wrapping it.
(exec google-chrome \
    --start-maximized \
    --remote-debugging-port=${INTERNAL_PORT} \
    --remote-allow-origins='*' \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-networking \
    --disable-sync \
    --disable-features=Translate,TranslateUI \
    --test-type \
    --user-data-dir=/userdata/ \
    --user-agent="$USER_AGENT" \
    "${INITIAL}") &
CHROME_PID=$!

wait_for_cdp ${INTERNAL_PORT}

echo "STAT"
curl -s 127.0.0.1:${INTERNAL_PORT}/json/list
echo "READY"

wait ${CHROME_PID}
