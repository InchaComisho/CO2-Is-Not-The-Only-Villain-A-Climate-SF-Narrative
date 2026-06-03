# Blue Pulse Simulation Plots

> **IMPORTANT:** These plots are outputs of a simplified educational toy model.
> They are NOT real climate forecasts. They are illustrative scenario comparisons
> for the fictional Blue Pulse project.

## Generated Plots

| File | Description |
|---|---|
| `unit_count_vs_regional_sst_reduction.png` | Illustrative regional SST reduction vs. unit count |
| `unit_count_vs_heatwave_day_reduction.png` | Illustrative marine heatwave day reduction vs. unit count |
| `unit_count_vs_ecosystem_recovery_index.png` | Ecosystem recovery proxy index vs. unit count |
| `unit_count_vs_risk_index.png` | Ecosystem recovery index vs. intervention risk index |

## Notes

- Scaling is nonlinear: saturation formula `1 - exp(-area / target_area)` is used.
- Risk grows faster than benefit at high unit counts.
- All axes values are illustrative estimates, not real measurements.

## See Also

- [Simulation README](../README.md)
- [Blue Pulse Simulation Model](../../../docs/concepts/blue-pulse-simulation-model.md)
