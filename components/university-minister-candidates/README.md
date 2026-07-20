# University minister candidates

This standalone Mod-type pack gives newly created government candidates a
chance to receive the visible **University Educated** trait, worth **+1
Management** in every cabinet office.

Only the highest education building currently owned by the candidate's faction
applies:

- College: 6%
- University: 12%
- Enlightened University: 20%

The roll runs only on `CharacterCreated`. Existing candidates are not changed,
multiple universities do not stack, and moving or appointing the same
politician cannot trigger another education roll. There is no paid reroll or
appointment-triggered bonus in this component.

The pack includes literal triggers for 64 Napoleon faction keys and supports
both the standard and Peninsular Campaign education chains. Human and AI
factions use the same rules.

## Files

- `WW0_University_Minister_Candidates.pack`
- `user.script.fragment.txt`
- `source/build_pack.py`

`build_pack.py` deterministically generates the PFH0 pack from original table
rows. RPFM decoded all eight internal files successfully, and the deterministic
source builder reproduced the checked-in pack byte-for-byte.

The stock minister-creation exclusions in `BASE_CANDIDATE_CONDITIONS` mirror
Creative Assembly's original conditions. The university predicates,
localization, builder, and additive rows are original project work. No game,
WW0, RPFM code, or RPFM schema is redistributed.

Pack SHA-256:

```text
e40cecb7deeb07ef4c1b5ce14938bfa20e5cf529dad01ee9dc5eccd56b32ad0c
```

The database additions work with vanilla Napoleon and WW0. Use the component
installer; only candidates created after the pack loads can receive the trait.
The historical `WW0_` pack filename is retained for compatibility with the
already-installed build; World War zerO is not required for this component.
