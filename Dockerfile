FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates wget gnupg unzip xvfb net-tools socat curl \
        python3 python3-venv x11-apps imagemagick fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings && \
    wget -q -O /etc/apt/keyrings/google-chrome.asc https://dl-ssl.google.com/linux/linux_signing_key.pub && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.asc] https://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Ubuntu 24.04 marks the system python as externally managed (PEP 668), so flask
# lives in its own virtualenv.
RUN python3 -m venv /app/venv && /app/venv/bin/pip install --no-cache-dir flask
ENV PATH=/app/venv/bin:$PATH

RUN mkdir -p /userdata/ /downloads/

ENV DBUS_SESSION_BUS_ADDRESS=disabled:
ENV DISPLAY=:99.0

COPY entrypoint.sh .
COPY startup.sh .
COPY fix_profile.py .
COPY server.py .

ENTRYPOINT ["/app/entrypoint.sh"]
