# SPDX-FileCopyrightText: 2026 RiftWii contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Download each mod in sources.json into <out>/<slug>/<file name>.

MediaFire: the download button's link on the file page. MEGA: the public
file API, decrypted with the key in the link (AES-CTR). Google Drive: the
usercontent download with confirm. Anything else: a plain GET.
Nothing downloaded is opened or run here."""
import base64
import hashlib
import json
import pathlib
import re
import struct
import sys
import urllib.parse
import urllib.request

from Crypto.Cipher import AES
from Crypto.Util import Counter

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
LIMIT = 600 << 20


def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=120)


def save_stream(resp, path, decrypt=None):
    total = 0
    with open(path, "wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > LIMIT:
                raise RuntimeError("over the size limit")
            out.write(decrypt(chunk) if decrypt else chunk)
    return total


def b64(s):
    s = s.replace("-", "+").replace("_", "/").replace(",", "")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def mega(url, folder):
    m = re.search(r"mega\.nz/file/([\w-]+)#([\w-]+)", url)
    handle, key = m.group(1), b64(m.group(2))
    words = struct.unpack(">8I", key)
    k = struct.pack(">4I", *(words[i] ^ words[i + 4] for i in range(4)))
    iv = struct.pack(">2I", words[4], words[5])
    body = json.dumps([{"a": "g", "g": 1, "p": handle}]).encode()
    info = json.loads(get("https://g.api.mega.co.nz/cs?id=1", body, {"Content-Type": "application/json"}).read())[0]
    if isinstance(info, int):
        raise RuntimeError(f"MEGA error {info}")
    attrs = AES.new(k, AES.MODE_CBC, b"\0" * 16).decrypt(b64(info["at"])).rstrip(b"\0")
    name = json.loads(attrs[4:].decode("utf-8", "replace"))["n"]
    cipher = AES.new(k, AES.MODE_CTR, counter=Counter.new(64, prefix=iv, initial_value=0))
    path = folder / safe(name)
    save_stream(get(info["g"]), path, cipher.decrypt)
    return path


def mega_folder(url, folder):
    """Every file of a public MEGA folder under 200 MB (texture packs skipped)."""
    m = re.search(r"mega\.nz/folder/([\w-]+)#([\w-]+)", url)
    root, folder_key = m.group(1), b64(m.group(2))
    api = f"https://g.api.mega.co.nz/cs?id=1&n={root}"
    nodes = json.loads(get(api, json.dumps([{"a": "f", "c": 1, "r": 1, "ca": 1}]).encode(),
                           {"Content-Type": "application/json"}).read())[0]["f"]
    ecb = AES.new(folder_key, AES.MODE_ECB)
    saved = None
    for node in nodes:
        if node["t"] != 0:
            continue
        key = ecb.decrypt(b64(node["k"].split(":", 1)[1]))
        words = struct.unpack(">8I", key)
        k = struct.pack(">4I", *(words[i] ^ words[i + 4] for i in range(4)))
        iv = struct.pack(">2I", words[4], words[5])
        attrs = AES.new(k, AES.MODE_CBC, b"\0" * 16).decrypt(b64(node["a"])).rstrip(b"\0")
        name = json.loads(attrs[4:].decode("utf-8", "replace"))["n"]
        print(f"     folder file: {name} ({node['s']} bytes)", flush=True)
        if node["s"] > (200 << 20):
            continue
        info = json.loads(get(api, json.dumps([{"a": "g", "g": 1, "n": node["h"]}]).encode(),
                              {"Content-Type": "application/json"}).read())[0]
        cipher = AES.new(k, AES.MODE_CTR, counter=Counter.new(64, prefix=iv, initial_value=0))
        path = folder / safe(name)
        save_stream(get(info["g"]), path, cipher.decrypt)
        saved = saved or path
    return saved


def mediafire(url, folder):
    page = get(url.replace("http://", "https://")).read().decode("utf-8", "replace")
    m = re.search(r'href="(https://download\d*\.mediafire\.com/[^"]+)"', page)
    if not m:
        raise RuntimeError("no download link on the MediaFire page")
    link = m.group(1)
    path = folder / safe(urllib.parse.unquote(link.rsplit("/", 1)[1]))
    save_stream(get(link), path)
    return path


def gdrive(url, folder):
    file_id = re.search(r"/d/([\w-]+)", url).group(1)
    resp = get(f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t")
    disp = resp.headers.get("Content-Disposition", "")
    m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", disp)
    if not m or "text/html" in resp.headers.get("Content-Type", ""):
        raise RuntimeError("Drive did not send a file")
    path = folder / safe(urllib.parse.unquote(m.group(1)))
    save_stream(resp, path)
    return path


def direct(url, folder):
    path = folder / safe(urllib.parse.unquote(url.rsplit("/", 1)[1]))
    save_stream(get(url), path)
    return path


def safe(name):
    name = re.sub(r"[^\w.+\- ()\[\]]", "_", name).strip(". ")
    return name or "download.bin"


def fetch(url, folder):
    if "mega.nz/folder" in url:
        return mega_folder(url, folder)
    if "mega.nz" in url:
        return mega(url, folder)
    if "mediafire.com" in url:
        return mediafire(url, folder)
    if "drive.google.com" in url:
        return gdrive(url, folder)
    return direct(url, folder)


def main():
    sources = json.load(open(sys.argv[1], encoding="utf-8"))
    out = pathlib.Path(sys.argv[2])
    only = set(sys.argv[3:])
    for s in sources:
        if only and s["slug"] not in only:
            continue
        folder = out / s["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        for url in [s["source"], *s.get("also", [])]:
            try:
                path = fetch(url, folder)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                print(f"OK   {s['slug']} | {path.name} | {path.stat().st_size} | {digest}", flush=True)
            except Exception as error:
                print(f"FAIL {s['slug']} | {url} | {error}", flush=True)


main()
