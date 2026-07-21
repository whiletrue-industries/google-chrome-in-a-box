# google-chrome-in-a-box

A headful Google Chrome running under Xvfb inside a container, with its devtools
protocol port and its download directory published over the network — so a
remote Selenium client can drive it and collect whatever it downloaded.

Image: `ghcr.io/akariv/google-chrome-in-a-box`

## Running

```bash
docker run -p 9223:9223 -p 9224:9224 -d \
    ghcr.io/akariv/google-chrome-in-a-box 9223 9224 https://data.gov.il
```

Arguments are `<devtools-port> <downloads-port> <initial-url>`, and the two
ports must also be published, as Chrome advertises itself on them.

- `http://<host>:9223/json/list` — the devtools endpoint Selenium attaches to.
- `http://<host>:9224/<filename>` — `GET` a downloaded file, `DELETE` to remove it.
- `http://<host>:9224/screenshot` — a PNG of the current X display.

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
