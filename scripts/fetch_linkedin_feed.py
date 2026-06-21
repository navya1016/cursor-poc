#!/usr/bin/env python3
"""Fetch LinkedIn feed using local Chrome cookies and save posts to research/linkedin-posts.

Requires: requests, beautifulsoup4

Usage:
  python scripts/fetch_linkedin_feed.py

Note: This script reads cookies from your active Chrome profile on the machine
and attempts to fetch https://www.linkedin.com/feed/ as your logged-in user.
"""
import argparse
import base64
import ctypes
import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

try:
    import browser_cookie3
except Exception:
    browser_cookie3 = None

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, "research", "linkedin-posts")
os.makedirs(OUT_DIR, exist_ok=True)

CHROME_USER_DATA = os.path.join(
    os.getenv('LOCALAPPDATA', ''),
    'Google',
    'Chrome',
    'User Data'
)
CHROME_LOCAL_STATE = os.path.join(CHROME_USER_DATA, 'Local State')


def _find_chrome_cookie_db() -> str:
    default_cookies = os.path.join(CHROME_USER_DATA, 'Default', 'Cookies')
    network_cookies = os.path.join(CHROME_USER_DATA, 'Default', 'Network', 'Cookies')
    if os.path.exists(default_cookies):
        return default_cookies
    if os.path.exists(network_cookies):
        return network_cookies

    if os.path.isdir(CHROME_USER_DATA):
        for profile in sorted(Path(CHROME_USER_DATA).glob('Profile *')):
            profile_cookies = profile / 'Cookies'
            profile_network_cookies = profile / 'Network' / 'Cookies'
            if profile_cookies.exists():
                return str(profile_cookies)
            if profile_network_cookies.exists():
                return str(profile_network_cookies)

    raise FileNotFoundError('Could not locate Chrome Cookies DB in User Data')


def _dpapi_decrypt(cipher_text: bytes) -> bytes:
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ('cbData', ctypes.wintypes.DWORD),
            ('pbData', ctypes.POINTER(ctypes.c_char))
        ]

    blob_in = DATA_BLOB(len(cipher_text), ctypes.create_string_buffer(cipher_text, len(cipher_text)))
    blob_out = DATA_BLOB()

    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise RuntimeError('DPAPI decryption failed')

    result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    return result


def _load_encryption_key(local_state_path: str = None) -> bytes:
    local_state_path = local_state_path or CHROME_LOCAL_STATE
    if not os.path.exists(local_state_path):
        raise FileNotFoundError(f'Chrome Local State not found: {local_state_path}')

    with open(local_state_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    encrypted_key = base64.b64decode(data['os_crypt']['encrypted_key'])
    if encrypted_key.startswith(b'DPAPI'):
        encrypted_key = encrypted_key[5:]
    return _dpapi_decrypt(encrypted_key)


def _decrypt_encrypted_value(encrypted_value: bytes, key: bytes) -> str:
    if not encrypted_value:
        return ''
    if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
        encrypted_value = encrypted_value[3:]
        nonce, ciphertext, tag = encrypted_value[:12], encrypted_value[12:-16], encrypted_value[-16:]
        from Cryptodome.Cipher import AES
        aes = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = aes.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8', errors='replace')
    try:
        return _dpapi_decrypt(encrypted_value).decode('utf-8', errors='replace')
    except Exception:
        return ''


def _copy_db(src_path: str) -> str:
    if not os.path.exists(src_path):
        raise FileNotFoundError(f'Chrome cookies DB not found: {src_path}')
    fd, temp_path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    shutil.copy2(src_path, temp_path)
    return temp_path


def get_chrome_cookies(domain_name: str = 'linkedin.com') -> requests.cookies.RequestsCookieJar:
    if os.name != 'nt':
        raise RuntimeError('Windows is required for Chrome DPAPI cookie decryption')

    key = _load_encryption_key()
    cookie_db_path = _find_chrome_cookie_db()
    cookie_db_copy = _copy_db(cookie_db_path)

    jar = requests.cookies.RequestsCookieJar()
    try:
        conn = sqlite3.connect(cookie_db_copy)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT host_key, path, is_secure, expires_utc, name, value, encrypted_value, is_httponly '
            'FROM cookies WHERE host_key LIKE ?;',
            (f'%{domain_name}%',)
        )

        for host_key, path, is_secure, expires_utc, name, value, encrypted_value, is_httponly in cursor.fetchall():
            if value:
                cookie_value = value
            else:
                cookie_value = _decrypt_encrypted_value(encrypted_value, key)

            jar.set_cookie(
                requests.cookies.create_cookie(
                    domain=host_key,
                    name=name,
                    value=cookie_value,
                    path=path,
                    secure=bool(is_secure),
                    rest={'HttpOnly': bool(is_httponly)},
                )
            )
    finally:
        conn.close()
        try:
            os.unlink(cookie_db_copy)
        except OSError:
            pass

    if len(jar) == 0:
        raise RuntimeError('No LinkedIn cookies were loaded from Chrome')

    return jar


def get_cookies(debug: bool = False):
    if os.name == 'nt':
        try:
            if debug:
                print('DEBUG: Loading Chrome cookies from Chrome user data root:', CHROME_USER_DATA)
                print('DEBUG: Local State path:', CHROME_LOCAL_STATE)
            cj = get_chrome_cookies(domain_name='linkedin.com')
            if debug:
                print('DEBUG: Loaded cookies count:', len(list(cj)))
            return cj
        except Exception as exc:
            if debug:
                import traceback
                traceback.print_exc()
            if browser_cookie3 is not None:
                try:
                    if debug:
                        print('DEBUG: Falling back to browser_cookie3.chrome()')
                    return browser_cookie3.chrome(domain_name='linkedin.com')
                except Exception as exc2:
                    if debug:
                        print('DEBUG: browser_cookie3.chrome() failed:', exc2)
            raise RuntimeError(
                'Failed to load Chrome cookies. Ensure Chrome is installed, you are logged in to LinkedIn, '
                'and your current Windows user can decrypt Chrome credentials. Original error: ' + str(exc)
            )

    if browser_cookie3 is None:
        raise RuntimeError('browser_cookie3 is required on non-Windows platforms')

    return browser_cookie3.chrome(domain_name='linkedin.com')


def slug(s):
    return re.sub(r"[^0-9a-zA-Z_-]", "-", s).strip("-")[:80]


def fetch_feed(debug: bool = False):
    cj = get_cookies(debug=debug)
    csrf = None
    for c in cj:
        if c.name == 'JSESSIONID':
            csrf = c.value.strip('"')
            break

    if debug:
        print('DEBUG: CSRF token', bool(csrf))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://www.linkedin.com/feed/',
    }
    if csrf:
        headers['Csrf-Token'] = f'ajax:{csrf}'

    url = 'https://www.linkedin.com/feed/'
    if debug:
        print('DEBUG: Requesting', url)
    r = requests.get(url, cookies=cj, headers=headers, timeout=30)
    if debug:
        print('DEBUG: Response status', r.status_code)
    if r.status_code != 200:
        raise RuntimeError(f'LinkedIn fetch failed: {r.status_code} for {url}')
    return r.text


def parse_and_save(html):
    soup = BeautifulSoup(html, 'html.parser')
    posts = []
    candidates = soup.find_all(lambda tag: tag.name == 'div' and tag.get('data-urn') and 'activity' in tag.get('data-urn'))
    if not candidates:
        candidates = soup.find_all(class_=re.compile(r'feed-shared-update-v2|feed-shared-text'))

    for node in candidates:
        try:
            author_node = node.find(class_=re.compile(r'feed-shared-actor__name'))
            author = author_node.get_text(strip=True) if author_node else 'unknown'
            text_node = node.find(class_=re.compile(r'feed-shared-update-v2__description|feed-shared-text|feed-shared-update-v2__commentary'))
            text = text_node.get_text(separator='\n', strip=True) if text_node else node.get_text(separator='\n', strip=True)
            urn = node.get('data-urn') or ''
            posts.append({'author': author, 'text': text, 'urn': urn})
        except Exception:
            continue

    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out_path = os.path.join(OUT_DIR, f'linkedin-feed-scrape-{ts}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    for p in posts:
        name = p['author'] or 'unknown'
        fname = slug(name) + '.md'
        path = os.path.join(OUT_DIR, fname)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"- fetched_at: {ts}\n")
            f.write(f"- urn: {p.get('urn','')}\n")
            f.write('\n')
            f.write(p.get('text','') + '\n\n')

    return out_path, len(posts)


def parse_args():
    parser = argparse.ArgumentParser(description='Fetch LinkedIn feed using Chrome cookies')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    return parser.parse_args()


def main():
    args = parse_args()
    html = fetch_feed(debug=args.debug)
    out_path, count = parse_and_save(html)
    print(f'Saved {count} posts to {out_path}')


if __name__ == '__main__':
    main()
