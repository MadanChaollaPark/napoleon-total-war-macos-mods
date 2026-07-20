# Source row manifest

The pack contains four faction-keyed unit rows, plus the normal three-building
recruitment chain for each unit:

| Table | Rows |
|---|---:|
| `building_units_allowed` | 12 |
| `cdir_unit_qualities` | 4 |
| `uniform_to_faction_colours` | 4 |
| `uniforms` | 4 |
| `unit_stats_land` | 4 |
| `units` | 4 |
| `units_to_exclusive_faction_permissions` | 4 |
| localized unit names | 4 |

All four uniform names are new `WW0_*` keys. Their filenames and colours are
copied from an existing artillery uniform belonging to the same faction.
Spain and Crimea reference existing Howitzer cards at runtime. Portugal and
Switzerland reference their closest national artillery cards because Napoleon
does not ship national Howitzer cards for them. No UI image is included in the
pack.
