# Napoleon: Total War macOS Mods

Modular, reversible fixes for the Feral macOS release of Napoleon: Total War,
focused on completing playable Ottoman and Crimean behavior in World War zerO.

## Included components

| Component | What it changes | Can be installed alone? |
|---|---|---:|
| [All-factions unlocker](components/all-factions-unlocker/) | Adds 23 optional faction keys to `user.script.txt` | Yes |
| [Ottoman naval parity](components/ottoman-naval-parity/) | Enables five researched late-game Ottoman ships, including Ironclads | Yes |
| [Middle Eastern agent parity](components/middle-eastern-agent-parity/) | Mirrors normal building/research benefits to Eastern Scholars and Assassins | Yes |
| [WW0 agent-cap startpos](components/ww0-agent-cap-startpos/) | Corrects Ottoman and Crimean base cap records for new campaigns | Yes |
| [Radious compatibility](components/radious-compatibility/) | Adds an optional loader line for a separately downloaded Radious pack | Yes |

There is no fog-of-war mod in this release: that issue was investigated but no
validated correction was produced.

## Easy installation

1. Install [World War zerO](https://www.moddb.com/mods/world-war-zero).
2. Quit Napoleon: Total War.
3. Download and unzip the latest `NTW-macOS-complete-suite` release asset.
4. Double-click `installers/macos/INSTALL_ALL.command`.
5. Start a **new WW0 campaign** for the corrected Ottoman/Crimean base agent caps.

If Radious is already installed from its [official ModDB download](https://www.moddb.com/games/napoleon-total-war/downloads/radious-campaign-ai),
use `INSTALL_ALL_WITH_RADIOUS.command` instead.

Run `STATUS.command` for a read-only report. Run `ROLLBACK_LAST.command` to
restore the exact pre-install script, packs, and startpos from checksummed
transaction backups.

See [the installation guide](docs/INSTALL.md), [rollback guide](docs/ROLLBACK.md),
and [compatibility matrix](docs/COMPATIBILITY.md).

## Safety design

- Each feature is a separate component and a separate Git commit.
- Existing `user.script.txt` content and encoding are preserved.
- Packs are installed in Feral's writable VFS directory, not bundled into WW0.
- The startpos correction is a compact delta; no complete WW0/game startpos is published.
- Unknown or later-modified files are rejected instead of overwritten.
- Every install produces a JSON transaction manifest and byte-for-byte backups.
- WW0 and Radious remain external, credited dependencies.

## Scope and limitations

- Fully supported installer: Feral macOS release.
- The startpos delta targets one exact WW0 Europe build; its accepted hashes are documented.
- Existing saves keep their serialized base agent caps. The database packs can
  load with an existing save, but the complete correction requires a new campaign.
- Rocket Troops are not added because no generic or Ottoman rocket-unit variant exists.
- This is an unofficial fan project. See [third-party notices](THIRD_PARTY_NOTICES.md).

## Verification

```bash
python3 -m unittest discover -s tests -v
```

The public tests verify component hashes and row manifests, UTF-16LE merging,
idempotent safety checks, and exact transactional rollback without requiring or
redistributing the game.
