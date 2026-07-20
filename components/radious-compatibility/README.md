# Optional Radious Campaign AI compatibility

Radious Campaign AI is a third-party mod and is not redistributed here.

Download it from the [official ModDB page](https://www.moddb.com/games/napoleon-total-war/downloads/radious-campaign-ai).
The ModDB listing credits Radious / Sir Thoragoros and describes a more
aggressive campaign AI with stronger attack planning and more troops.

## Verified upstream file

```text
archive: Radious_CampaignAI.rar
MD5:     3b8089db6b9fa91270e5f7ef49fe38cf
```

After extracting the archive, the tested `Radious_CampaignAI.pack` has:

```text
SHA-256: 55a98db54f04d47c05953a335b69706481a31290c171ba4e8de8776743eeded7
```

Copy that pack to Feral's writable VFS directory:

```text
~/Library/Containers/com.feralinteractive.napoleontw/Data/Library/Application Support/Feral Interactive/Napoleon Total War/VFS/Local/Napoleon Total War/data/
```

Then merge `user.script.fragment.txt` into Feral's `user.script.txt`. The suite
installer can manage the loader line but deliberately never downloads or copies
the third-party binary.

Radious does not override the database tables used by the Ottoman naval and
Middle Eastern agent parity packs. Load it before those component lines.

