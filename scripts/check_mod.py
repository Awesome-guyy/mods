# SPDX-FileCopyrightText: 2026 RiftWii contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""For each downloaded mod: check it as the Wii will install it, and make the
zip RiftWii/mods will host. A zip that passes is kept byte for byte; a 7z or
rar (or a zip the Wii can't take as it is, e.g. a pack inside a zip) is
unpacked with 7-Zip and packed again as a plain zip. Nothing is run.

usage: lw_check.py <sources.json> <files dir> <out dir> <riftwii tools dir>"""
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
sources = json.load(open(sys.argv[1], encoding="utf-8"))
files = pathlib.Path(sys.argv[2])
out = pathlib.Path(sys.argv[3])
sys.path.insert(0, sys.argv[4])
import mod_list  # noqa: E402

SEVEN = mod_list.seven_zip()
out.mkdir(parents=True, exist_ok=True)
ARCHIVES = (".zip", ".7z", ".rar")


def unpack(archive, into):
    r = subprocess.run([SEVEN, "x", "-y", f"-o{into}", str(archive)], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("7-Zip could not unpack it: " + r.stderr.decode(errors="replace")[-200:])


def find_pack_root(folder):
    """The folder that holds riivolution/, unpacking archives found inside
    (a pack zipped inside the download) up to two levels deep."""
    for depth in range(3):
        hits = [p for p in folder.rglob("*") if p.is_dir() and p.name.lower() == "riivolution"
                and any(x.suffix.lower() == ".xml" for x in p.iterdir())]
        if hits:
            return hits[0].parent
        inner = [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in ARCHIVES]
        if not inner or depth == 2:
            return None
        for archive in inner:
            unpack(archive, archive.parent / (archive.stem + "_unpacked"))
            archive.unlink()
    return None


def rezip(root, target):
    """root's contents (riivolution/ and the pack's folders; readmes and
    other loose files at the top kept too) as a plain zip."""
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root).as_posix()
            if any(part.lower() in ("__macosx", ".ds_store", "desktop.ini", "thumbs.db") for part in rel.split("/")):
                continue
            if path.is_file():
                z.write(path, rel)


results = []
for s in sources:
    folder = files / s["slug"]
    archives = sorted(p for p in folder.glob("*") if p.suffix.lower() in ARCHIVES) if folder.exists() else []
    if not archives:
        results.append((s["slug"], "NOT DOWNLOADED", ""))
        continue
    archive = max(archives, key=lambda p: p.stat().st_size) if len(archives) > 1 else archives[0]
    data = archive.read_bytes()
    target = out / (s["slug"] + ".zip")
    how = ""
    try:
        if archive.suffix.lower() == ".zip":
            try:
                v = mod_list.zip_layout(data)
                shutil.copyfile(archive, target)
                how = "kept as it is"
            except (mod_list.Skip, zipfile.BadZipFile) as why:
                how = f"repacked ({why})"
                v = None
        else:
            v = None
            how = f"repacked from .{archive.suffix[1:]}"
        if v is None:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = pathlib.Path(tmp)
                unpack(archive, tmp / "x")
                root = find_pack_root(tmp / "x")
                if root is None:
                    raise mod_list.Skip("no riivolution/*.xml inside")
                rezip(root, target)
            v = mod_list.zip_layout(target.read_bytes())
        size = target.stat().st_size
        note = "" if size <= mod_list.MAX_DOWNLOAD else "  TOO BIG FOR THE WII"
        results.append((s["slug"], "OK", f"{how}; {size >> 20} MB, {v['files']} files, games {v['games']}, "
                                            f"folders {v['folders']}, program {v['program']}{note}"))
    except Exception as why:  # noqa: BLE001 (report every mod, whatever went wrong)
        target.unlink(missing_ok=True)
        results.append((s["slug"], "SKIP", f"{archive.name}: {why}"))

for slug, state, info in results:
    print(f"{state:15} {slug:34} {info}")
