"""End-to-end tests against a running google-chrome-in-a-box container.

Chrome is driven exactly like the real client does it: selenium attaches to the
container's published devtools port via `debugger_address`.
"""
import json

import requests
from selenium.webdriver.common.by import By

PAGE = '<html><head><title>chrome-in-a-box</title></head><body><h1 id="hi">Hello</h1></body></html>'


def _serve(box, name, content):
    """Publish a file from the container's /downloads directory."""
    box.write_file(f'/downloads/{name}', content)
    return f'http://127.0.0.1:{box.downloads_port}/{name}'


def test_cdp_is_reachable(chrome_box):
    version = requests.get(f'{chrome_box.cdp_url}/json/version', timeout=10).json()
    assert version['Browser'].startswith('Chrome/')
    assert len(requests.get(f'{chrome_box.cdp_url}/json/list', timeout=10).json()) >= 1


def test_selenium_loads_a_page(chrome_box):
    url = _serve(chrome_box, 'page.html', PAGE)
    chrome_box.driver.get(url)
    assert chrome_box.driver.title == 'chrome-in-a-box'
    assert chrome_box.driver.find_element(By.ID, 'hi').text == 'Hello'


def test_selenium_executes_javascript(chrome_box):
    chrome_box.driver.get(_serve(chrome_box, 'page.html', PAGE))
    html = chrome_box.driver.execute_script('return document.documentElement.outerHTML;')
    assert 'chrome-in-a-box' in html


def test_user_agent_is_overridden(chrome_box):
    chrome_box.driver.get(_serve(chrome_box, 'page.html', PAGE))
    agent = chrome_box.driver.execute_script('return navigator.userAgent;')
    assert 'datagov-external-client' in agent


def test_json_endpoint_like_the_client_does(chrome_box):
    payload = {'success': True, 'result': [1, 2, 3]}
    url = _serve(chrome_box, 'data.json', json.dumps(payload))
    chrome_box.driver.get(url)
    assert json.loads(chrome_box.driver.find_element(By.CSS_SELECTOR, 'body > pre').text) == payload


def test_screenshot_endpoint(chrome_box):
    response = requests.get(f'{chrome_box.downloads_url}/screenshot', timeout=60)
    assert response.status_code == 200
    assert response.content[:8] == b'\x89PNG\r\n\x1a\n'


def test_downloads_server_serves_and_deletes(chrome_box):
    url = _serve(chrome_box, 'artifact.txt', 'downloaded contents')
    assert requests.get(url, timeout=10).text == 'downloaded contents'
    assert requests.delete(url, timeout=10).status_code == 200
    assert requests.get(url, timeout=10).status_code == 404


def test_downloads_are_written_to_the_downloads_directory(chrome_box):
    prefs = json.loads(chrome_box.exec('cat', '/userdata/Default/Preferences'))
    assert prefs['download']['default_directory'] == '/downloads/'
    assert prefs['download']['prompt_for_download'] is False
    assert prefs['translate']['enabled'] is False
