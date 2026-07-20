# Rollback

Quit Napoleon: Total War, then double-click:

```text
installers/macos/ROLLBACK_LAST.command
```

Rollback uses the latest successful transaction manifest. Before restoring, it
checks that each current file still matches either the installer output or the
recorded original. If another tool or user changed a file later, rollback stops
instead of overwriting that work.

For files that existed before installation, it restores the byte-for-byte
backup and verifies its SHA-256. Newly added packs are moved into the transaction
folder rather than permanently erased.

To roll back a particular older transaction:

```bash
python3 installers/macos/mod_manager.py rollback --transaction TRANSACTION_ID
```

Transaction IDs and manifests are stored under:

```text
~/Library/Application Support/Napoleon Total War macOS Mods/transactions/
```

Rollback does not touch campaign saves.

