# Compatibility

## Verified environment

- Napoleon: Total War, Feral Mac App Store release
- Feral application bundle at `/Applications/Napoleon Total War.app`
- World War zerO Europe campaign
- Optional Radious Campaign AI loaded before this repository's packs
- macOS on Apple silicon through Rosetta

## Component compatibility

| Component | Vanilla | WW0 | Radious | New campaign required |
|---|---:|---:|---:|---:|
| All-factions unlocker | Yes | Optional | Yes | Menu reload recommended |
| Ottoman naval parity | No | Yes | Yes | No; reload the save/game |
| Middle Eastern agent parity | No | Yes | Yes | Base-cap portion does |
| WW0 agent-cap startpos delta | No | Exact WW0 build only | Yes | Yes |
| Minor naval parity | No | Yes | Yes | No; reload the save/game |
| Basic Howitzer parity | No | Yes | Yes | No; reload the save/game |
| Experimental Howitzer parity | No | Yes | Yes | No; reload the save/game |
| Rocket Corps parity | No | Yes | Yes | No; reload the save/game |

The startpos delta accepts only this upstream input:

```text
size:    28,325,845 bytes
sha256:  35e29a3a220eb6fede7f15bcd52af0c6338fc902ae247af803bf30ca56402394
```

The clean-install patch and legacy-upgrade patch both produce:

```text
size:    28,326,441 bytes
sha256:  1a28aeb95cfa4f342eab3b17ddb7818abbb4e059038638b8f4c0d4fc7d58eb0d
```

The installer also accepts the earlier Ottoman/Crimean-only patched input:

```text
size:    28,325,925 bytes
sha256:  a52843a83bdbb00710ac74ac3cdf87d76f2209bae81818fdd7016395d80fdf30
```

Unknown or updated WW0 startpos versions are rejected instead of overwritten.

## Not included

There is no fog-of-war component. The reported initial-visibility issue was
investigated, but no validated correction was created and no fog asset was
modified.
