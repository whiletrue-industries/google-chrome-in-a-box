import os
import random
import socket
import subprocess
import time

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from .chromedriver import chromedriver_for

IMAGE = os.environ.get('CHROME_BOX_IMAGE', 'google-chrome-in-a-box:test')
BUILD = os.environ.get('CHROME_BOX_BUILD', '1') == '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chrome refuses CDP requests whose Host header is neither localhost nor an IP
# address, so tests always talk to the published ports by IP.
HOST = '127.0.0.1'


def _free_port():
    for _ in range(50):
        port = random.randint(20000, 30000)
        with socket.socket() as sock:
            if sock.connect_ex((HOST, port)) != 0 and sock.connect_ex((HOST, port + 1)) != 0:
                return port
    raise RuntimeError('Could not find a free port pair')


@pytest.fixture(scope='session')
def image():
    if BUILD:
        subprocess.run(['docker', 'build', '-t', IMAGE, '.'], cwd=ROOT, check=True)
    return IMAGE


class ChromeBox:
    """A running google-chrome-in-a-box container."""

    def __init__(self, container, port):
        self.container = container
        self.port = port
        self.downloads_port = port + 1
        self.cdp_url = f'http://{HOST}:{port}'
        self.downloads_url = f'http://{HOST}:{port + 1}'
        self.driver = None

    def exec(self, *args):
        return subprocess.run(['docker', 'exec', self.container, *args],
                              check=True, capture_output=True, text=True).stdout

    def write_file(self, path, content):
        subprocess.run(['docker', 'exec', '-i', self.container, 'tee', path],
                       input=content.encode('utf8'), check=True, capture_output=True)

    def logs(self):
        return subprocess.run(['docker', 'logs', self.container],
                              capture_output=True, text=True).stdout


def _wait_for(what, url, timeout=180, accept=(200,), **kwargs):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5, **kwargs)
            if response.status_code in accept:
                return response
            last = f'status {response.status_code}'
        except requests.RequestException as e:
            last = str(e)
        time.sleep(2)
    raise TimeoutError(f'Timed out waiting for {what} at {url}: {last}')


@pytest.fixture(scope='session')
def chrome_box(image):
    port = _free_port()
    container = subprocess.run(
        ['docker', 'run', '-d', '--rm', '--shm-size=1g',
         '-p', f'{HOST}:{port}:{port}', '-p', f'{HOST}:{port + 1}:{port + 1}',
         image, str(port), str(port + 1), 'about:blank'],
        check=True, capture_output=True, text=True).stdout.strip()

    box = ChromeBox(container, port)
    try:
        version = _wait_for('CDP', f'{box.cdp_url}/json/version').json()
        # The file server has no route for `/`, a 404 means it is listening.
        _wait_for('downloads server', f'{box.downloads_url}/', timeout=60, accept=(200, 404))

        driver_path = chromedriver_for(version['Browser'].split('/')[-1])
        options = webdriver.ChromeOptions()
        options.debugger_address = f'{HOST}:{port}'
        box.driver = webdriver.Chrome(service=Service(driver_path), options=options)
        yield box
    finally:
        if box.driver is not None:
            try:
                box.driver.quit()
            except Exception:
                pass
        print(box.logs())
        subprocess.run(['docker', 'stop', '-t', '1', container], capture_output=True)
