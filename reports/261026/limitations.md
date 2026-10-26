# Limitations

R_pair_proxy is camera/virtual-LiDAR annotation disagreement, affected by shared labels, asynchrony and calibration interpretation. No independent detector-vs-GT data. Six held-out sites are not broad external validation.

Q_effective targets recorded trajectories from an existing sensing/tracking pipeline, not physical GT. Isotropic Gaussian CV is an assumption; filtering/initial-state/observation/processing effects remain mixed. Innovation-ML boundary solutions do not imply zero physical measurement noise.

Only eligible common1s/3s origins are evaluated. Very short/ending segments and invalid status rows remain in audit tables but lack forecast targets. Dense origins are correlated. Date grouping is conservative; actual identities across dates are unavailable.

Signals/weather/age/violations are not fitted. Complete-crossing/G95 requires independently verified geometry/entry-exit definition and is not computed. SPD and IMPTC are not pooled and SPD R is never forced into IMPTC.

Sample pilot and Set01 were inspected previously; the full extension is exploratory with fixed new-fit holdouts, not an untouched benchmark. No hyperparameters were revised after outer-fold scores.
