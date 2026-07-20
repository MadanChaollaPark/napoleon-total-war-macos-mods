# Troubleshooting

## Unknown WW0 startpos version

The installer intentionally supports only the documented upstream hash. A WW0
update or another startpos mod changes that hash. Do not force the delta onto an
unknown file; install the matching WW0 build or wait for an updated delta.

## Unknown existing parity pack

Another version already occupies the target name. Move it aside manually only
after preserving it, then retry. The installer will never overwrite an unknown
pack.

## Radious is missing or has the wrong checksum

Download and extract the original archive from the credited ModDB page. This
repository does not supply or modify the Radious binary.

## Factions or ships do not appear

- Restart the game after changing loader lines.
- Confirm `STATUS.command` reports the selected packs as installed.
- Meet the normal technology and building requirements; the naval component
  does not grant research or a free steam drydock.
- Start a new WW0 campaign for the corrected base Scholar/Assassin caps.

## The game crashes

Roll back the latest transaction, then add components one at a time. WW0 itself
documents a known Grand Campaign return-to-menu crash. Keep crash diagnosis
separate from this repository's component checks.

