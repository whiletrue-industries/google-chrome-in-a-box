# google-chrome-in-a-box

[![test & publish](https://github.com/whiletrue-industries/google-chrome-in-a-box/actions/workflows/ci.yml/badge.svg)](https://github.com/whiletrue-industries/google-chrome-in-a-box/actions/workflows/ci.yml)

A headful Google Chrome running under Xvfb inside a container, with its devtools
protocol port and its download directory published over the network — so a
remote Selenium client can drive it and collect whatever it downloaded.

Image: `ghcr.io/whiletrue-industries/google-chrome-in-a-box`

## Running

```bash
docker run -p 9223:9223 -p 9224:9224 -d \
    ghcr.io/whiletrue-industries/google-chrome-in-a-box 9223 9224 https://data.gov.il
```

Arguments are `<devtools-port> <downloads-port> <initial-url>`, and the two
ports must also be published, as Chrome advertises itself on them.

- `http://<host>:9223/json/list` — the devtools endpoint Selenium attaches to.
- `http://<host>:9224/<filename>` — `GET` a downloaded file, `DELETE` to remove it.
- `http://<host>:9224/screenshot` — a PNG of the current X display (the whole
  screen, browser chrome included — not just the page viewport).

## User agent

By default Chrome announces itself with its real version plus a
`datagov-external-client` marker. It is derived from the Chrome in the image
rather than pinned: a stale version string contradicts the `sec-ch-ua` client
hints Chrome sends from its actual version, and bot protection treats that
mismatch as a signal — www.gov.il answers such requests with a 403 and renders
nothing. Override with `docker run -e USER_AGENT='...'` if a site needs
something specific.

## Driving it

```python
from selenium import webdriver

options = webdriver.ChromeOptions()
options.debugger_address = f'{host_ip}:9223'
driver = webdriver.Chrome(options=options)
driver.get('https://data.gov.il/api/action/package_search')
```

Connect by **IP address**, not hostname: Chrome rejects devtools requests whose
`Host` header is neither `localhost` nor an IP.

Navigate with `driver.get()` rather than relying on whatever the initial-url
argument loaded. That first load races Chrome's own startup, and can fail with
`ERR_CERT_VERIFIER_CHANGED` when the cert verifier re-initializes mid-flight —
leaving a half-loaded page that a screenshot will happily capture.

## Tests

The suite starts a real container, attaches Selenium to it and exercises page
loading, the user-agent override, the screenshot endpoint and the downloads
server. It needs Docker and network access; chromedriver is fetched
automatically to match the Chrome inside the image.

```bash
pip install -r requirements-test.txt
pytest tests -v
```

Set `CHROME_BOX_BUILD=0` to test an already-built image, and `CHROME_BOX_IMAGE`
to choose which one.
