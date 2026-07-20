# Feral macOS installer

Quit Napoleon: Total War before using these commands.

## One-click choices

- `INSTALL_ALL.command`: faction unlocks, both parity packs, and the WW0 startpos correction.
- `INSTALL_ALL_WITH_RADIOUS.command`: the same suite plus a managed Radious loader line. The separately downloaded Radious pack must already be installed.
- `STATUS.command`: read-only status and encoding report.
- `ROLLBACK_LAST.command`: restores the exact pre-install state from the latest transaction.

Each installation stores checksummed backups and a JSON manifest under:

```text
~/Library/Application Support/Napoleon Total War macOS Mods/
```

The installer preserves unrelated `user.script.txt` content and its encoding,
uses individually marked blocks, refuses unknown existing packs/startpos files,
and moves newly added files into the transaction folder during rollback.

## Individual components

Run from this directory:

```bash
python3 mod_manager.py install --components unlock
python3 mod_manager.py install --components agents
python3 mod_manager.py install --components naval
python3 mod_manager.py install --components startpos
python3 mod_manager.py install --components radious
```

Override detected paths with `--app`, `--support`, and `--state`, or the
`NTW_APP_PATH`, `NTW_SUPPORT_PATH`, and `NTW_MOD_STATE_ROOT` environment variables.

