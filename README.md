# RiftWii mods

The list of Riivolution mods the Rift Store shows on a Wii game's **Mods**
page (**Get more mods...**), built every night from
[GameBanana](https://gamebanana.com) and published at
`https://riftwii.github.io/mods/mods.json`.

**No mod is hosted here.** Each mod is downloaded from GameBanana's own
servers; the list only says which GameBanana file to get, checked and
pinned by its SHA-256, and links to the mod's GameBanana page, where its
author is credited. The small icons in `icons/` are cut from each mod's
first GameBanana picture.

A mod is listed when its download is really a Riivolution pack (it has a
`riivolution/*.xml`), passed GameBanana's virus scan, is public and not
marked as mature, and fits what the Wii can install. How the list is
built and what the Wii checks: RiftWii's
[docs/MODS.md](https://github.com/KakarottoCake/Riftwii/blob/main/docs/MODS.md).

## Leaving a mod out

If you made a mod and don't want it in RiftWii's list, open an issue with
its GameBanana link. Its id goes in `excluded.txt` and the next night's
list leaves it out.

## Files

| File | |
| --- | --- |
| `.github/workflows/publish.yml` | The nightly build and deploy to GitHub Pages. |
| `excluded.txt` | GameBanana mod ids to leave out, one per line. |
| `cache-seed/` | What the first build learned, so a fresh cache doesn't start from nothing. |
| `scripts/build_app_list_check.sh` | Builds the Wii's own list parser, which checks every list before it is published. |
