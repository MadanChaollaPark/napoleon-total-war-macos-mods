# Changelog

## 1.1.1 - 2026-07-20

- Added an optional fair auto-resolve component that neutralizes only the two
  hidden Very Hard AI strength bonuses used by automatic land and naval battle
  resolution.
- Replaced placeholder Experimental Howitzer and Rocket Troop cards with
  explicit references to installed, type-correct Prussian and Russian cards.
- Rebuilt the basic Howitzer component as four faction-keyed units so Spain
  and Crimea resolve Howitzer cards, while Portugal and Switzerland resolve
  their closest available national artillery cards.
- Added deterministic basic-Howitzer generation, exact building/technology/
  faction tests, icon-reference tests, and a live installed-asset verifier.
- Added transaction-safe upgrades from the three original v1.1.0 artillery
  pack hashes.

## 1.1.0 - 2026-07-20

- Added university-tier chances for newly generated minister candidates to gain
  a visible +1 Management trait.
- Repaired Spain's national steam-drydock recruitment and technology chain.
- Added researched late-ship permissions for special-roster playable factions.
- Added ordinary Howitzers for Spain, Portugal, Switzerland and Crimea.
- Added European and Eastern Experimental Howitzers for 36 non-major factions.
- Added European and Eastern Rocket Troops for 36 non-major factions.
- Restored base Gentleman and Rake caps for Italy, Papal States and Venice.
- Added clean-install and legacy-upgrade startpos deltas.
- Extended transactional install, verification and rollback to every component.

## 1.0.0 - 2026-07-20

- Added a 23-faction optional unlock block.
- Added five Ottoman late-game naval permissions.
- Added Middle Eastern Scholar/Assassin spawn, factionwide-cap, and research parity.
- Added a compact, hash-gated WW0 Ottoman/Crimean startpos delta.
- Added optional Radious loader compatibility without redistributing Radious.
- Added transactional Feral macOS install, status, and rollback commands.
- Added public artifact, row-count, encoding, refusal, and rollback tests.
