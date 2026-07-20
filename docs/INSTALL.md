# Installation guide

## Prerequisites

- Feral's macOS Napoleon: Total War release.
- World War zerO installed in the application bundle.
- Python 3 available to `/usr/bin/env python3`.
- The game fully quit during installation.

Radious Campaign AI is optional and must be downloaded separately from its
[credited ModDB page](https://www.moddb.com/games/napoleon-total-war/downloads/radious-campaign-ai).

## Complete suite

From a release archive, double-click:

```text
installers/macos/INSTALL_ALL.command
```

This installs faction unlocks, both parity database packs, and the checksummed
WW0 Europe startpos delta. It does not download or enable Radious.

If the verified Radious pack is already in Feral's VFS directory, use:

```text
installers/macos/INSTALL_ALL_WITH_RADIOUS.command
```

The university minister component is an optional gameplay change and is not
part of either complete-suite command. Install it separately with its component
launcher or the `university` command below.

## Individual components

Open Terminal in `installers/macos` and choose one or more names:

```bash
python3 mod_manager.py install --components unlock
python3 mod_manager.py install --components agents
python3 mod_manager.py install --components university
python3 mod_manager.py install --components naval
python3 mod_manager.py install --components startpos
python3 mod_manager.py install --components radious
python3 mod_manager.py install --components agents naval
```

Component names are:

- `unlock`: the 23-faction script block.
- `agents`: Eastern Scholar and Assassin building/research parity.
- `university`: education-tier chances for +1 Management on new minister candidates.
- `naval`: five Ottoman late-game ship permissions.
- `startpos`: new-campaign Ottoman/Crimean base cap correction.
- `radious`: only the managed loader line; requires the verified third-party pack.

## Installed locations

Packs:

```text
~/Library/Containers/com.feralinteractive.napoleontw/Data/Library/Application Support/Feral Interactive/Napoleon Total War/VFS/Local/Napoleon Total War/data/
```

Managed script blocks:

```text
~/Library/Containers/com.feralinteractive.napoleontw/Data/Library/Application Support/Feral Interactive/Napoleon Total War/AppData/scripts/user.script.txt
```

WW0 Europe startpos:

```text
/Applications/Napoleon Total War.app/Contents/Resources/Data/Data/campaigns/ww0_europe/startpos.esf
```

Backups and manifests:

```text
~/Library/Application Support/Napoleon Total War macOS Mods/
```

## Custom locations

Use `--app`, `--support`, and `--state`, or set `NTW_APP_PATH`,
`NTW_SUPPORT_PATH`, and `NTW_MOD_STATE_ROOT`.
