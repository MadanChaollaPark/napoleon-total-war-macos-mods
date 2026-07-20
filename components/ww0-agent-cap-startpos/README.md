# WW0 base agent-cap startpos correction

WW0 inherits two vanilla AI-faction cap records that target `gentleman` and
`rake`, even though Ottoman and Crimean Middle Eastern cultures use
`Eastern_Scholar` and `assassin`.

This component changes both cap blocks for both factions. It affects only
campaigns started after patching.

It also restores the normal European base capacity of one `gentleman` and one
`rake` in both cap blocks for three WW0-playable Italian factions whose
AI-only records were empty:

- Kingdom of Italy
- Papal States
- Venetian Republic

The repository does not redistribute WW0's complete 28 MB startpos. Instead it
contains two compact bsdiff deltas: one for a clean verified WW0 startpos and
one for upgrading the earlier Ottoman/Crimean-only correction.

## Install

1. Install the matching version of WW0.
2. Quit Napoleon: Total War.
3. Double-click `INSTALL.command`.

The installer:

- Checks the exact clean or legacy-patched SHA-256 before writing.
- Saves a byte-for-byte backup outside the application bundle.
- Builds and verifies the patched file before copying it into place.
- Detects an already patched installation.

Double-click `ROLLBACK.command` to restore the recorded original. Both scripts
accept an alternate application path through `NTW_APP_PATH`.

## Checksums

```text
upstream startpos:     35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394
legacy patched input: a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30
fully patched output: 1a28aeb95cfa4f342eab3b17ddb7818abbb4e059038638b8f4c0d4fc7d58eb0d
clean-install delta:  faa5903265d5308b2a212a6073bbec8b9fb76d77b04e938d157d35521a484ede
legacy-upgrade delta: 9f7110e56b85cadbf8c794d1a05f3d4d9adb90c44693f104cb14187ae304ab3b
```
