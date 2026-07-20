# All-factions unlocker

An optional `user.script.txt` fragment containing the 23 faction keys used by
the tested Feral installation.

## Manual installation

1. Quit Napoleon: Total War.
2. Open Feral's script file:

   ```text
   ~/Library/Containers/com.feralinteractive.napoleontw/Data/Library/Application Support/Feral Interactive/Napoleon Total War/AppData/scripts/user.script.txt
   ```

3. Preserve its existing encoding. The tested Feral file is UTF-16LE without a
   byte-order mark.
4. Add the contents of `user.script.fragment.txt` once.
5. Start the game and reopen the campaign menu.

The suite installer performs an encoding-preserving merge and creates a backup,
so manual editing is not necessary for the normal installation path.

WW0 already exposes its own playable-faction campaign entries. This component
is retained separately for vanilla/other campaign menus and can be omitted by
players who do not need it.

