# SPDX-FileCopyrightText: 2026 RiftWii contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""hosted.json from hosted-sources.json, the downloads and the checked zips.

usage: make_hosted.py <hosted-sources.json> <downloads dir> <zips dir> <hosted.json>"""
import json
import pathlib
import re
import sys
import urllib.parse
import shutil
import subprocess
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
sources = json.load(open(sys.argv[1], encoding="utf-8"))
downloads = pathlib.Path(sys.argv[2])
zips = pathlib.Path(sys.argv[3])
target = pathlib.Path(sys.argv[4])
MAX = 128 << 20
SEVEN = shutil.which("7z") or shutil.which("7zz") or "C:/Program Files/7-Zip/7z.exe"
GAME = {"SMG1": "Super Mario Galaxy", "SMG2": "Super Mario Galaxy 2"}
PREVIEW = "https://lumasworkshop.com/mods/preview_{}_0.jpg"
# Luma's Workshop's own preview picture names, where they differ from the slug.
PICTURES = {
    "kaizo-mario-galaxy-legacy": "kaizo_mario_galaxy_legacy_edition",
    "kaizo-mario-galaxy-rebalanced": "kaizo_mario_galaxy_rebalanced",
    "kaizo-mario-galaxy-2": "kaizo_mario_galaxy_2",
    "lost-levels-directors-cut": "super_mario_galaxy_the_lost_levels",
    "smg2-master-mode": "super_mario_galaxy_2_master_mode",
    "smg2-cosmic-race-collection": "Cosmic_Race_Collection",
    "smg64-holiday-special": "super_mario_galaxy_64_holiday_special",
    "super-mario-gravity-demo-1": "super_mario_gravity",
    "a-rock-galaxy": "level_a_rock_galaxy",
    "bones-curse": "level_bones_curse",
    "desert-snake": "level_desert_snake",
    "floaty-beach-galaxy": "level_floaty_beach_galaxy",
    "pipeground-galaxy": "level_pipeground_galaxy",
    "rolling-plains-galaxy": "level_rolling_plains_galaxy",
    "sphere-creek-galaxy": "level_sphere_creek_galaxy",
    "super-ikea-galaxy": "level_super_ikea_galaxy",
    "super-roblox-galaxy": "level_super_roblox_galaxy",
    "switchflip-galaxy": "level_switchflip_galaxy",
    "the-arena": "level_the_arena",
    "smg-brazilian-portuguese": "smg_portuguese",
    "smg2-brazilian-portuguese": "smg2_portuguese",
    "smg-chinese": "smg_chinese",
    "smg-chinese-shield": "smg_chinese_nvidia",
    "smg-russian": "smg_russian",
    "smg2-russian": "smg2_russian",
    "lw-competition-1": "competition_1", "lw-competition-2": "competition_2", "lw-competition-3": "competition_3",
    "lw-competition-5": "competition_5", "lw-competition-6": "competition_6", "lw-competition-7": "competition_7",
    "smg-daredevil-mode": "super_mario_galaxy_daredevil_mode",
    "smg2-daredevil-mode": "super_mario_galaxy_2_daredevil_mode",
    "battle-fort": "level_battle_fort",
    "neo-mario-galaxy": "neo_mario_galaxy",
}
# On GameBanana as an installable zip from the maker: that listing is kept.
ON_GAMEBANANA = {"kaizo-mario-galaxy-legacy": 149763, "kaizo-mario-galaxy-2": 439733}
items = []
for s in sources:
    if s["slug"] in ON_GAMEBANANA:
        print("left out:", s["slug"], f"(the maker's own GameBanana zip gb{ON_GAMEBANANA[s['slug']]} is listed)")
        continue
    path = zips / (s["slug"] + ".zip")
    if not path.exists() or path.stat().st_size > MAX:
        print("left out:", s["slug"], "(not checked)" if not path.exists() else "(over 128 MB)")
        continue
    # The date and version from the archive as its makers shared it: the
    # newest file in it, and a "v1.2" in its name.
    original = max((p for p in (downloads / s["slug"]).iterdir() if p.suffix.lower() in (".zip", ".7z", ".rar")),
                   key=lambda p: p.stat().st_size)
    listing = subprocess.run([SEVEN, "l", "-slt", str(original)], capture_output=True).stdout.decode("utf-8", "replace")
    dates = re.findall(r"^Modified = (\d{4}-\d{2}-\d{2})", listing, re.M)
    released = max(dates) if dates else s["released"][:4] + "-01-01"
    name = urllib.parse.unquote(original.name).replace("+", " ")
    m = re.search(r"[vV](\d+(?:\.\d+)*)(?![0-9A-Za-z])", name)
    version = m.group(1) if m else released[:4]
    item = {
        "id": "rw-" + s["slug"],
        "name": s["name"],
        "makers": s["credits"],
        "game": GAME[s["game"]],
        "page": s["page"],
        "released": released,
        "version": version,
        # A zip already on GitHub (the maker's own release or site) is linked
        # as it is; the rest are kept in RiftWii/mods' "files" release.
        "url": s["source"] if re.match(r"https://(github\.com|[\w-]+\.github\.io)/.+\.zip$", s["source"])
        else "https://github.com/RiftWii/mods/releases/download/files/" + s["slug"] + ".zip",
        "source": s["source"],
        "listed_on": "https://lumasworkshop.com/mods/",
    }
    if s["slug"] in PICTURES:
        item["picture"] = PREVIEW.format(PICTURES[s["slug"]])
    if s.get("replaces_gamebanana"):
        item["replaces"] = [s["replaces_gamebanana"]]
    items.append(item)
target.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(items), "mods")
