# Trinity Equatorial Belt Conceptual Simulation

> **IMPORTANT DISCLAIMER**
>
> This is a simplified educational toy model for the fictional Trinity Model.
> It is NOT a real climate forecast, NOT engineering validation, and NOT a policy
> recommendation. All outputs are illustrative scenario estimates.

## Purpose

This module estimates how the fictional Trinity Model might scale when deployed
across a simplified equatorial belt, combining:

- **OBS** -- Ocean Breathing System / deep ocean aeration (from below)
- **UMC** -- Ultrasonic Mist Cooling over ocean and land (from above)
- **Soil Regeneration** -- restoring terrestrial carbon sinks

Unlike the Blue Pulse-only model, this simulation addresses ocean heat, land
heat stress, soil carbon sinks, and water retention simultaneously.

## Files

| File | Description |
|---|---|
| `trinity_equatorial_belt_simulation.py` | Main simulation script |
| `config/default_parameters.yml` | All model parameters (configurable) |
| `results/sample_results.csv` | Numeric results for all scenarios |
| `results/sample_summary.md` | Human-readable summary with interpretation |
| `results/plots/` | Visualizations (if matplotlib is available) |

## Quick Start

```bash
cd simulations/trinity-equatorial-belt
python trinity_equatorial_belt_simulation.py
```

## Deployment Scenarios

| Units | Scale |
|---|---|
| 1 | Single proof-of-concept unit |
| 100 | Tiny pilot |
| 1,000 | Small regional test |
| 10,000 | Regional deployment |
| 50,000 | Large-scale deployment |
| 100,000 | Basin-scale infrastructure |
| 250,000 | Continental-scale (stress test) |
| 500,000 | Extreme scenario (toy model limit) |

## Key Model Behaviors

- Coverage saturates as `1 - exp(-effective_area / target_area)`
- Ocean and land are modeled separately with different target areas
- Trinity synergy factor amplifies combined effects (1.10x)
- Risk grows faster than benefit at large scales
- Governance risk normalized to maximum scenario (500,000 units)

## Grid Note

The equatorial belt grid is a simplified toy mask (5-degree cells, lat -15 to 15).
Land regions are approximate rectangular boxes. This is not a real geographic model.

## Related Documentation

- [Trinity Equatorial Belt Simulation docs](../../docs/concepts/trinity-equatorial-belt-simulation.md)
- [Trinity Model concept page](../../docs/concepts/trinity-model.md)
- [Blue Pulse Simulation](../blue-pulse/)
