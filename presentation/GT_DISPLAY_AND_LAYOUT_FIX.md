# GT Display and Presentation Layout Fix

The default o0008/public-imptc-01 origin is +8s. Actual operational Exit first passage is at +10.063445091s recording time, i.e. +2.063445091s after the forecast origin. The observed frame bracket is +2.040009022–+2.080018044s after origin. H1/H2 outcome is 0; H3/H4 is 1. These are verified stored outcomes, not predictions.

Added an explicit Ground Truth card with the residual time, selected-horizon binary answer and all four horizon labels. Normal comparison shows it before probability bars. Presentation hides it before the GT reveal and shows the same saved values afterwards. The expert expansion explains operational XY/semantic-boundary GT rather than independent foot-level annotation.

Confirmed a presentation layout issue: the iframe position was measured before reveal controls were rendered, allowing it to overlap controls; the expanded case area could extend under the fixed footer. Position is now recalculated after reveal rendering, fonts, resize and scroll using a persistent iframe. Desktop comparison layout is more compact. No model/GT/source artifacts were changed.

Executed browser checks: all seven scenes at 1440×900, actual frame/slot rectangle equality, no overlap with reveal controls, GT card above footer, visible GT before predictions, H1–H4 stored labels and 390px mobile overflow. Static source/deployment and protected-artifact verification passed. Detailed local evidence: /Users/gwondohyeon/view2risk_gt_clarity_20261123/.
