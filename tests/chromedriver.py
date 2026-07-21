"""Fetch a chromedriver matching the Chrome running inside the container.

The host machine may have a different (or no) Chrome installed, so we resolve
the driver from the Chrome-for-Testing feed using the exact version reported by
the container over CDP.
"""
import io
import os
import platform
import re
import stat
import zipfile

import requests

FEED = ('https://googlechromelabs.github.io/chrome-for-testing/'
        'latest-patch-versions-per-build-with-downloads.json')
CACHE_DIR = os.environ.get('CHROMEDRIVER_CACHE', os.path.expanduser('~/.cache/chromedriver'))


def _platform():
    system, machine = platform.system(), platform.machine()
    if system == 'Linux':
        return 'linux64'
    if system == 'Darwin':
        return 'mac-arm64' if machine == 'arm64' else 'mac-x64'
    if system == 'Windows':
        return 'win64'
    raise RuntimeError(f'Unsupported platform: {system}/{machine}')


def _download_url(chrome_version):
    build = '.'.join(chrome_version.split('.')[:3])
    builds = requests.get(FEED, timeout=60).json()['builds']
    if build not in builds:
        raise RuntimeError(f'No chromedriver published for Chrome build {build}')
    downloads = builds[build]['downloads']['chromedriver']
    wanted = _platform()
    for download in downloads:
        if download['platform'] == wanted:
            return builds[build]['version'], download['url']
    raise RuntimeError(f'No chromedriver for platform {wanted}')


def chromedriver_for(chrome_version):
    """Return a path to a chromedriver binary matching `chrome_version`."""
    assert re.match(r'^\d+\.\d+\.\d+\.\d+$', chrome_version), chrome_version
    version, url = _download_url(chrome_version)
    target = os.path.join(CACHE_DIR, version, 'chromedriver')
    if os.path.exists(target):
        return target

    os.makedirs(os.path.dirname(target), exist_ok=True)
    archive = zipfile.ZipFile(io.BytesIO(requests.get(url, timeout=300).content))
    member = next(n for n in archive.namelist() if n.endswith('/chromedriver')
                  or n.endswith('/chromedriver.exe'))
    with archive.open(member) as src, open(target, 'wb') as out:
        out.write(src.read())
    os.chmod(target, os.stat(target).st_mode | stat.S_IEXEC)
    return target
