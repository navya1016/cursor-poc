import base64
import browser_cookie3
import glob
import json
import os
import pathlib

print('LOCALAPPDATA=', os.getenv('LOCALAPPDATA'))
print('APPDATA=', os.getenv('APPDATA'))
print('USERPROFILE=', os.getenv('USERPROFILE'))
print('browser_cookie3 module=', getattr(browser_cookie3, '__file__', None))
print('browser_cookie3 version=', getattr(browser_cookie3, '__version__', None))

chrome_root = pathlib.Path(os.getenv('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'User Data'
print('Chrome user data root=', chrome_root)
print('exists=', chrome_root.exists())
if chrome_root.exists():
    print('Local State exists=', (chrome_root / 'Local State').exists())
    for candidate in [
        chrome_root / 'Default' / 'Cookies',
        chrome_root / 'Default' / 'Network' / 'Cookies',
    ]:
        print(candidate, 'exists=', candidate.exists())

    for profile in sorted(chrome_root.glob('Profile *')):
        print('profile', profile.name)
        for candidate in [profile / 'Cookies', profile / 'Network' / 'Cookies']:
            print('  ', candidate, 'exists=', candidate.exists())

if (chrome_root / 'Local State').exists():
    try:
        with open(chrome_root / 'Local State', 'r', encoding='utf-8') as f:
            data = json.load(f)
        key = base64.b64decode(data['os_crypt']['encrypted_key'])
        print('encrypted_key startswith DPAPI=', key.startswith(b'DPAPI'))
    except Exception as exc:
        print('Failed to inspect Local State:', exc)

try:
    c = browser_cookie3.Chrome()
    print('browser_cookie3.Chrome() cookie_file=', getattr(c, 'cookie_file', None))
    print('browser_cookie3.Chrome() key_file=', getattr(c, 'key_file', None))
except Exception as exc:
    print('browser_cookie3.Chrome() failed:', exc)
