# WW0 Ottoman and Crimean agent-cap startpos correction

WW0 inherits two vanilla AI-faction cap records that target `gentleman` and
`rake`, even though Ottoman and Crimean Middle Eastern cultures use
`Eastern_Scholar` and `assassin`.

This component changes both cap blocks for both factions. It affects only
campaigns started after patching.

The repository does not redistribute WW0's complete 28 MB startpos. Instead it
contains a 156 KB bsdiff delta that accepts only the verified upstream file.

## Install

1. Install the matching version of WW0.
2. Quit Napoleon: Total War.
3. Double-click `INSTALL.command`.

The installer:

- Checks the exact upstream SHA-256 before writing.
- Saves a byte-for-byte backup outside the application bundle.
- Builds and verifies the patched file before copying it into place.
- Detects an already patched installation.

Double-click `ROLLBACK.command` to restore the recorded original. Both scripts
accept an alternate application path through `NTW_APP_PATH`.

## Checksums

```text
upstream startpos: 35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394
patched startpos:  a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30
bsdiff delta:      1f9bb7cee4708983f282405e5ebff448b5a9f9359be3a2aa587382865f4cd358
```

