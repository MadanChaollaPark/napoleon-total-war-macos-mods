# Fair Very Hard auto-resolve

This optional component removes the two hidden AI strength bonuses applied by
Napoleon: Total War when a human campaign and its battles are set to Very Hard:

- `autoresolve_very_hard_campaign_AI_percent_increase`: `0.35` to `0`
- `autoresolve_very_hard_difficulty_AI_advantage`: `0.20` to `0`

It does not change ship or land-unit statistics, manual battle difficulty,
campaign economy, recruitment, diplomacy, public order, or campaign AI. It
changes only the calculation used when a battle is resolved automatically.
Because the vanilla difficulty variables are shared, the correction applies to
both land and naval auto-resolve.

The pack contains one additive `campaign_variables` table with the two original
keys and neutral replacement values. It is compatible with vanilla Napoleon,
World War zerO and the supported Radious Campaign AI pack.

## Install

Quit Napoleon: Total War, then double-click `INSTALL.command`. The transactional
installer backs up the existing UTF-16LE load script and any pack at the target
path before changing them.

Use `ROLLBACK_LAST.command` to restore the exact pre-install state.

## Reproducibility

`source/build_pack.py` deterministically rebuilds the checked-in PFH0 pack. The
source manifest records the only two database rows included.
