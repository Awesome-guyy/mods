# RiftWii mods

The list of Riivolution mods the Rift Store shows on a Wii game's **Mods**
page (**Get more mods...**), built every night from
[GameBanana](https://gamebanana.com) and published at
`https://riftwii.github.io/mods/mods.json`.

**GameBanana's mods are not hosted here.** Each one is downloaded from
GameBanana's own servers; the list only says which GameBanana file to get,
checked and pinned by its SHA-256, and links to the mod's GameBanana page,
where its author is credited. The small icons in `icons/` are cut from each
mod's first picture.

## Mods kept here

Some Super Mario Galaxy and Super Mario Galaxy 2 mods are shared only on
MEGA, Google Drive or MediaFire (often from a YouTube description), which a
Wii can't download from. With the makers' agreement through
[Luma's Workshop](https://lumasworkshop.com/mods/), RiftWii keeps a copy of
each as a file of this repository's
[`files` release](https://github.com/RiftWii/mods/releases/tag/files) and
lists it from `hosted.json`: its name, every maker as Luma's Workshop
credits them, and a link to its original page or trailer. A zip is kept
byte for byte; a 7z or rar is unpacked and packed again as a zip (the Wii
unpacks only zips), with nothing added or taken out. A mod its maker also
put on GameBanana as a zip is listed from there instead, and the Wii's
128 MB download limit leaves out the biggest ones.

To add one: put it in `scripts/hosted-sources.json` (name, makers, game,
page, download link), then

```
python3 scripts/fetch_mod.py scripts/hosted-sources.json downloads <slug>
python3 scripts/check_mod.py scripts/hosted-sources.json downloads zips <RiftWii>/tools
python3 scripts/make_hosted.py scripts/hosted-sources.json downloads zips hosted.json
gh release upload files zips/<slug>.zip
```

`fetch_mod.py` takes MEGA, MediaFire and Google Drive links; `check_mod.py`
reads each pack the way the Wii installs it.

A mod is listed when its download is really a Riivolution pack (it has a
`riivolution/*.xml`), passed GameBanana's virus scan, is public and not
marked as mature, and fits what the Wii can install. How the list is
built and what the Wii checks: RiftWii's
[docs/MODS.md](https://github.com/KakarottoCake/Riftwii/blob/main/docs/MODS.md).

## Leaving a mod out

If you made a mod and don't want it in RiftWii's list, open an issue with
its link:

- a GameBanana mod: its id goes in `excluded.txt`, and the next night's
  list leaves it out;
- a mod kept here: its entry leaves `hosted.json` and its file is deleted
  from the release.

If your credit is wrong or missing, open an issue too and it is fixed.

## Files

| File | |
| --- | --- |
| `.github/workflows/publish.yml` | The nightly build and deploy to GitHub Pages. |
| `excluded.txt` | GameBanana mod ids to leave out, one per line. |
| `hosted.json` | The mods kept in the `files` release, with their makers and original pages. |
| `scripts/hosted-sources.json` | Where each of those came from, as Luma's Workshop lists it. |
| `scripts/fetch_mod.py`, `check_mod.py`, `make_hosted.py` | Download, check and list a mod kept here. |
| `cache-seed/` | What the first build learned, so a fresh cache doesn't start from nothing. |
| `scripts/build_app_list_check.sh` | Builds the Wii's own list parser, which checks every list before it is published. |
