"""Seed the Chrome profile with our download preferences.

Runs before Chrome is started for the first time: Chrome keeps whatever is
already in Default/Preferences, so there is no need to start it twice just to
patch the file it generated.
"""
import json
import os

PATH = '/userdata/Default/Preferences'

prefs = {}
if os.path.exists(PATH):
    with open(PATH, encoding='utf8') as f:
        prefs = json.load(f)

prefs.setdefault('download', {}).update(dict(
    default_directory='/downloads/',
    prompt_for_download=False
))
# The translate bubble covers the top of the page (and of screenshots); the
# command-line flags no longer suppress it, this pref does.
prefs.setdefault('translate', {}).update(dict(enabled=False))

os.makedirs(os.path.dirname(PATH), exist_ok=True)
with open(PATH, 'w', encoding='utf8') as f:
    json.dump(prefs, f)
