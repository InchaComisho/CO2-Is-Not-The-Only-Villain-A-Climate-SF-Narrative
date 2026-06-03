"""
Blue Pulse Conceptual Deployment Simulation
============================================

IMPORTANT DISCLAIMER
--------------------
This is a simplified educational toy model for the fictional Blue Pulse project
in the narrative "If I Had Believed CO2 Was the Only Villain, Earth Would Have
Been Checkmated."

This script is NOT:
  - a real climate forecast
  - an engineering validation
  - a policy recommendation
  - a substitute for peer-reviewed oceanographic science

All outputs are illustrative scenario estimates under default assumptions.
They are designed to support narrative understanding of scaling dynamics,
not to predict real-world outcomes.

Usage
-----
    python blue_pulse_simulation.py [--config PATH] [--variant {low,default,high}]

Output
------
    results/sample_results.csv
    results/sample_summary.md
    results/plots/  (if matplotlib is available)
"""

import math
import csv
import os
import sys
import argparse
from datetime import datetime

# Optional YAML config support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Optional plotting support
try:
    import matplotlib
    matplotlib.use("Agg")   # non-interactive backend for script use
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config", "default_parameters.yml")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
CSV_PATH = os.path.join(RESULTS_DIR, "sample_results.csv")
SUMMARY_PATH = os.path.join(RESULTS_DIR, "sample_summary.md")

# ---------------------------------------------------------------------------
# Default parameters (used if YAML is unavailable or config not found)
# ---------------------------------------------------------------------------

DEFAULT_PARAMS = {
    "target_region_area_km2": 100000,
    "unit_effective_area_km2": {"low": 2, "default": 5, "high": 10},
    "obs_local_max_sst_reduction_c": {"low": 0.03, "default": 0.12, "high": 0.25},
    "obs_strength_factor": {"low": 0.5, "default": 1.0, "high": 1.6},
    "umc_local_max_sst_peak_reduction_c": {"low": 0.02, "default": 0.10, "high": 0.20},
    "umc_fog_risk_weight": 0.12,
    "combined_synergy_factor": {"low": 0.8, "default": 1.15, "high": 1.35},
    "local_combined_sst_cap_c": 0.75,
    "regional_coupling_factor": {"low": 0.25, "default": 0.45, "high": 0.65},
    "risk_growth_exponent": {"default": 1.35},
    "risk_weights": {
        "ecological_disturbance": 0.40,
        "umc_fog_visibility": 0.20,
        "governance_public_trust": 0.25,
        "circulation_uncertainty": 0.15,
    },
    "baseline_super_el_nino_sst_anomaly_c": 2.0,
    "baseline_marine_heatwave_days": 120,
    "caps": {
        "marine_heatwave_days_reduced_percent": 35,
        "phytoplankton_proxy_increase_percent": 40,
        "ecosystem_recovery_index": 100,
        "intervention_risk_index": 100,
    },
    "deployment_scenarios": [1, 100, 1000, 10000, 50000, 100000],
}

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path: str, variant: str = "default") -> dict:
    """Load YAML config, falling back to built-in defaults."""
    if YAML_AVAILABLE and os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        params = raw.copy()
        params["_variant"] = variant
        return params
    print(f"[info] Config not loaded via YAML. Using built-in defaults.")
    params = DEFAULT_PARAMS.copy()
    params["_variant"] = variant
    return params


def get_val(param, variant: str = "default"):
    """Extract scalar from a dict with low/default/high, or return scalar."""
    if isinstance(param, dict):
        return param.get(variant, param.get("default"))
    return param

# ---------------------------------------------------------------------------
# Core simulation formulas
# ---------------------------------------------------------------------------

def simulate_scenario(unit_count: int, params: dict, variant: str = "default") -> dict:
    """
    Compute conceptual model outputs for a given unit count.

    All outputs are illustrative estimates under the stated assumptions.
    Not a real climate forecast.
    """
    target_area = params["target_region_area_km2"]
    unit_area = get_val(params["unit_effective_area_km2"], variant)
    obs_sst = get_val(params["obs_local_max_sst_reduction_c"], variant)
    obs_str = get_val(params.get("obs_strength_factor", {"default": 1.0}), variant)
    umc_sst = get_val(params["umc_local_max_sst_peak_reduction_c"], variant)
    synergy = get_val(params["combined_synergy_factor"], variant)
    sst_cap = params.get("local_combined_sst_cap_c", 0.75)
    coupling = get_val(params["regional_coupling_factor"], variant)
    risk_exp = get_val(params.get("risk_growth_exponent", {"default": 1.35}), variant)
    fog_wt = params.get("umc_fog_risk_weight", 0.12)
    risk_wts = params.get("risk_weights", {
        "ecological_disturbance": 0.40,
        "umc_fog_visibility": 0.20,
        "governance_public_trust": 0.25,
        "circulation_uncertainty": 0.15,
    })
    baseline_sst_anomaly = params.get("baseline_super_el_nino_sst_anomaly_c", 2.0)
    baseline_hw_days = params.get("baseline_marine_heatwave_days", 120)
    caps = params.get("caps", {
        "marine_heatwave_days_reduced_percent": 35,
        "phytoplankton_proxy_increase_percent": 40,
        "ecosystem_recovery_index": 100,
        "intervention_risk_index": 100,
    })

    # 1. Effective coverage (saturation formula)
    total_area = unit_count * unit_area
    effective_coverage = 1.0 - math.exp(-total_area / target_area)

    # 2. Local combined SST peak reduction (OBS + UMC synergy, capped)
    local_combined = (obs_sst + umc_sst) * synergy
    local_combined = min(local_combined, sst_cap)

    # 3. Regional mean SST reduction
    regional_sst_reduction = local_combined * effective_coverage * coupling

    # 4. Marine heatwave days reduced (percent)
    hw_reduced_pct = min(
        caps.get("marine_heatwave_days_reduced_percent", 35),
        (regional_sst_reduction / baseline_sst_anomaly) * 100.0
    )

    # 5. Phytoplankton proxy increase (percent)
    phyto_pct = min(
        caps.get("phytoplankton_proxy_increase_percent", 40),
        effective_coverage * 35.0 * obs_str
    )

    # 6. Carbon uptake proxy (percent)  — proxy only, not real tonnage
    carbon_proxy = phyto_pct * 0.45

    # 7. Ecosystem recovery index (0–100)
    # Weighted combination of normalized benefit signals
    sst_norm = min(1.0, regional_sst_reduction / 0.5)       # 0.5 C as reference
    hw_norm = hw_reduced_pct / caps.get("marine_heatwave_days_reduced_percent", 35)
    phyto_norm = phyto_pct / caps.get("phytoplankton_proxy_increase_percent", 40)
    eco_index = min(
        caps.get("ecosystem_recovery_index", 100),
        100.0 * (0.35 * sst_norm + 0.30 * hw_norm + 0.35 * phyto_norm)
    )

    # 8. Intervention risk index (0–100)
    base_risk = effective_coverage ** risk_exp
    fog_risk = fog_wt * effective_coverage
    gov_risk = min(1.0, effective_coverage * 1.2)   # governance concern grows faster
    circ_risk = min(1.0, effective_coverage * 0.9)  # circulation uncertainty

    composite_risk = (
        risk_wts.get("ecological_disturbance", 0.40) * base_risk
        + risk_wts.get("umc_fog_visibility", 0.20) * fog_risk
        + risk_wts.get("governance_public_trust", 0.25) * gov_risk
        + risk_wts.get("circulation_uncertainty", 0.15) * circ_risk
    )
    risk_index = min(
        caps.get("intervention_risk_index", 100),
        100.0 * composite_risk
    )

    # 9. Confidence level string
    if unit_count <= 1:
        confidence = "observation only"
    elif unit_count <= 100:
        confidence = "very low — speculative"
    elif unit_count <= 1000:
        confidence = "low — illustrative"
    elif unit_count <= 10000:
        confidence = "low-medium — optimistic illustrative"
    elif unit_count <= 50000:
        confidence = "medium — scenario only"
    else:
        confidence = "low-medium — saturation regime, high uncertainty"

    # 10. Interpretation
    if unit_count <= 1:
        interp = "Single proof-of-concept unit. Effects are local and negligible at regional scale."
    elif unit_count <= 100:
        interp = "Small field array. Local SST peak reduction may become detectable with careful monitoring."
    elif unit_count <= 1000:
        interp = "Coastal experimental corridor. Possible regional heat-stress reduction begins to appear in model."
    elif unit_count <= 10000:
        interp = "Large upwelling-zone deployment. Meaningful regional improvement possible under optimistic assumptions."
    elif unit_count <= 50000:
        interp = "Basin-scale experimental infrastructure. Strong regional signal possible; risk index growing significantly."
    else:
        interp = "Very large deployment. Saturation begins; marginal benefit declines; ecological, governance, and public-trust risks become dominant."

    return {
        "unit_count": unit_count,
        "effective_coverage_percent": round(effective_coverage * 100, 2),
        "local_combined_sst_reduction_c": round(local_combined, 4),
        "regional_mean_sst_reduction_c": round(regional_sst_reduction, 4),
        "marine_heatwave_days_reduced_percent": round(hw_reduced_pct, 2),
        "phytoplankton_proxy_increase_percent": round(phyto_pct, 2),
        "carbon_uptake_proxy_increase_percent": round(carbon_proxy, 2),
        "ecosystem_recovery_index_0_100": round(eco_index, 2),
        "intervention_risk_index_0_100": round(risk_index, 2),
        "confidence_level": confidence,
        "interpretation": interp,
    }

# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

FIELDS = [
    "unit_count",
    "effective_coverage_percent",
    "local_combined_sst_reduction_c",
    "regional_mean_sst_reduction_c",
    "marine_heatwave_days_reduced_percent",
    "phytoplankton_proxy_increase_percent",
    "carbon_uptake_proxy_increase_percent",
    "ecosystem_recovery_index_0_100",
    "intervention_risk_index_0_100",
    "confidence_level",
    "interpretation",
]


def write_csv(results: list, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(results)
    print(f"[output] CSV  -> {path}")

# ---------------------------------------------------------------------------
# Markdown summary output
# ---------------------------------------------------------------------------

SCALE_LABELS = {
    1: "Single test unit",
    100: "Small field array",
    1000: "Coastal experimental corridor",
    10000: "Large upwelling-zone deployment",
    50000: "Basin-scale experimental infrastructure",
    100000: "Very large deployment",
}

RISK_LABELS = {
    1: "negligible climate effect",
    100: "monitoring and trust issues",
    1000: "ecological attribution uncertainty",
    10000: "governance, ecosystem, fog/visibility, cost",
    50000: "high intervention risk and diminishing returns",
    100000: "major ethical, ecological, geopolitical risk",
}

BENEFIT_LABELS = {
    1: "local observation only",
    100: "local SST peak reduction may become detectable",
    1000: "possible regional heat-stress reduction",
    10000: "meaningful regional improvement under optimistic assumptions",
    50000: "strong regional signal possible in model",
    100000: "saturation begins; not linear",
}


def write_summary(results: list, params: dict, variant: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Blue Pulse Conceptual Simulation — Sample Results",
        "",
        "> **IMPORTANT:** These results are outputs of a simplified educational toy model.",
        "> They are NOT a real climate forecast, NOT an engineering validation, and NOT a",
        "> policy recommendation. All values are illustrative scenario estimates.",
        "",
        f"Generated: {ts}  ",
        f"Parameter variant: **{variant}**  ",
        f"Target region area: {params.get('target_region_area_km2', 100000):,} km²",
        "",
        "---",
        "",
        "## Scenario Results",
        "",
        "| Units | Coverage % | Regional SST Δ (°C) | HW Days Reduced % | Ecosystem Index | Risk Index | Confidence |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        lines.append(
            f"| {r['unit_count']:,} "
            f"| {r['effective_coverage_percent']:.1f}% "
            f"| {r['regional_mean_sst_reduction_c']:.4f} "
            f"| {r['marine_heatwave_days_reduced_percent']:.1f}% "
            f"| {r['ecosystem_recovery_index_0_100']:.1f} "
            f"| {r['intervention_risk_index_0_100']:.1f} "
            f"| {r['confidence_level']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Scale Interpretation Table",
        "",
        "| Units | Expected Scale | Likely Benefit | Main Risk |",
        "|---|---|---|---|",
    ]

    for r in results:
        u = r["unit_count"]
        lines.append(
            f"| {u:,} "
            f"| {SCALE_LABELS.get(u, '—')} "
            f"| {BENEFIT_LABELS.get(u, r['interpretation'])} "
            f"| {RISK_LABELS.get(u, '—')} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Detailed Scenario Notes",
        "",
    ]

    for r in results:
        lines += [
            f"### {r['unit_count']:,} Units",
            "",
            f"- Effective coverage: **{r['effective_coverage_percent']:.1f}%** of target region",
            f"- Local combined SST peak reduction: **{r['local_combined_sst_reduction_c']:.4f} °C**",
            f"- Regional mean SST reduction: **{r['regional_mean_sst_reduction_c']:.4f} °C**",
            f"- Marine heatwave days reduced: **{r['marine_heatwave_days_reduced_percent']:.1f}%**",
            f"- Phytoplankton proxy increase: **{r['phytoplankton_proxy_increase_percent']:.1f}%**",
            f"- Carbon uptake proxy increase: **{r['carbon_uptake_proxy_increase_percent']:.1f}%**",
            f"- Ecosystem recovery index: **{r['ecosystem_recovery_index_0_100']:.1f} / 100**",
            f"- Intervention risk index: **{r['intervention_risk_index_0_100']:.1f} / 100**",
            f"- Confidence: {r['confidence_level']}",
            f"- *{r['interpretation']}*",
            "",
        ]

    lines += [
        "---",
        "",
        "## Cautions",
        "",
        "- These results are conceptual and should not be read as climate forecasts.",
        "- The model uses simple exponential saturation; real ocean systems are far more complex.",
        "- OBS and UMC effects at scale have not been demonstrated in the real world.",
        "- Risk index values do not map to any real governance threshold.",
        "- The ecosystem recovery index is a proxy composite, not a real ecological measurement.",
        "- Carbon uptake proxy is not in real carbon tonnage and cannot be used for carbon accounting.",
        "",
        "---",
        "",
        "## See Also",
        "",
        "- [Blue Pulse concept page](../../docs/concepts/blue-pulse.md)",
        "- [Blue Pulse Simulation Model documentation](../../docs/concepts/blue-pulse-simulation-model.md)",
        "- [Ocean Breathing System](../../docs/concepts/ocean-breathing-system.md)",
        "- [Ultrasonic Mist Cooling](../../docs/concepts/ultrasonic-mist-cooling.md)",
        "- [Intervention Ethics](../../docs/concepts/intervention-ethics.md)",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[output] MD   -> {path}")

# ---------------------------------------------------------------------------
# Plot output
# ---------------------------------------------------------------------------

PLOT_STYLE = {
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "lines.linewidth": 2.0,
    "lines.markersize": 7,
}


def apply_style():
    for k, v in PLOT_STYLE.items():
        try:
            plt.rcParams[k] = v
        except Exception:
            pass


def make_plots(results: list, plots_dir: str) -> None:
    os.makedirs(plots_dir, exist_ok=True)
    apply_style()

    units = [r["unit_count"] for r in results]
    x = list(range(len(units)))
    x_labels = [f"{u:,}" for u in units]

    def base_fig():
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=9)
        ax.grid(True)
        return fig, ax

    def add_disclaimer(ax):
        ax.text(
            0.01, 0.98,
            "Conceptual toy model — not a climate forecast",
            transform=ax.transAxes,
            fontsize=7, color="#8b949e", va="top", ha="left"
        )

    def save(fig, name):
        path = os.path.join(plots_dir, name)
        fig.tight_layout()
        fig.savefig(path, dpi=120)
        plt.close(fig)
        print(f"[output] Plot -> {path}")

    # Plot 1: Regional SST reduction
    fig, ax = base_fig()
    vals = [r["regional_mean_sst_reduction_c"] for r in results]
    ax.plot(x, vals, color="#58a6ff", marker="o", label="Regional mean SST Δ (°C)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#58a6ff")
    ax.set_title("Blue Pulse — Unit Count vs. Regional SST Reduction\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units")
    ax.set_ylabel("Illustrative SST Reduction (°C)")
    ax.legend(fontsize=9)
    add_disclaimer(ax)
    save(fig, "unit_count_vs_regional_sst_reduction.png")

    # Plot 2: Marine heatwave day reduction
    fig, ax = base_fig()
    vals = [r["marine_heatwave_days_reduced_percent"] for r in results]
    ax.plot(x, vals, color="#f78166", marker="s", label="Heatwave days reduced (%)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#f78166")
    ax.set_title("Blue Pulse — Unit Count vs. Marine Heatwave Day Reduction\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units")
    ax.set_ylabel("Illustrative Reduction (%)")
    ax.legend(fontsize=9)
    add_disclaimer(ax)
    save(fig, "unit_count_vs_heatwave_day_reduction.png")

    # Plot 3: Ecosystem recovery index
    fig, ax = base_fig()
    vals = [r["ecosystem_recovery_index_0_100"] for r in results]
    ax.plot(x, vals, color="#3fb950", marker="^", label="Ecosystem recovery index (0–100)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#3fb950")
    ax.set_ylim(0, 110)
    ax.set_title("Blue Pulse — Unit Count vs. Ecosystem Recovery Index\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units")
    ax.set_ylabel("Index (0–100, illustrative)")
    ax.legend(fontsize=9)
    add_disclaimer(ax)
    save(fig, "unit_count_vs_ecosystem_recovery_index.png")

    # Plot 4: Risk index vs ecosystem index (dual)
    fig, ax = base_fig()
    eco = [r["ecosystem_recovery_index_0_100"] for r in results]
    risk = [r["intervention_risk_index_0_100"] for r in results]
    ax.plot(x, eco, color="#3fb950", marker="^", label="Ecosystem recovery index")
    ax.plot(x, risk, color="#da3633", marker="v", linestyle="--", label="Intervention risk index")
    ax.fill_between(x, eco, risk, where=[r > e for r, e in zip(risk, eco)],
                    alpha=0.12, color="#da3633", label="Risk > Benefit zone")
    ax.set_ylim(0, 110)
    ax.set_title("Blue Pulse — Ecosystem Recovery vs. Intervention Risk\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units")
    ax.set_ylabel("Index (0–100, illustrative)")
    ax.legend(fontsize=9)
    add_disclaimer(ax)
    save(fig, "unit_count_vs_risk_index.png")


# ---------------------------------------------------------------------------
# Plots directory README
# ---------------------------------------------------------------------------

def write_plots_readme(plots_dir: str) -> None:
    path = os.path.join(plots_dir, "README.md")
    content = """\
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
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[output] MD   -> {path}")

# ---------------------------------------------------------------------------
# Simulation README
# ---------------------------------------------------------------------------

def write_sim_readme(sim_dir: str) -> None:
    path = os.path.join(sim_dir, "README.md")
    content = """\
# Blue Pulse Conceptual Deployment Simulation

> **IMPORTANT DISCLAIMER**
>
> This is a simplified educational toy model for the fictional Blue Pulse project.
> It is NOT a real climate forecast, NOT an engineering validation, and NOT a policy
> recommendation. All outputs are illustrative scenario estimates under stated assumptions.

## Purpose

This simulation module estimates how the fictional Blue Pulse project might scale
under different deployment sizes, from a single test unit to 100,000+ units.

It models the combined effect of:

- **OBS** (Ocean Breathing System) — deep ocean aeration from below
- **UMC** (Ultrasonic Mist Cooling) — evaporative surface cooling from above

Scaling is nonlinear: coverage saturates exponentially, while intervention risk
grows faster than benefit at large scales.

## Files

| File | Description |
|---|---|
| `blue_pulse_simulation.py` | Main simulation script |
| `config/default_parameters.yml` | All model parameters (fully configurable) |
| `results/sample_results.csv` | Numeric results for all scenarios |
| `results/sample_summary.md` | Human-readable summary with interpretation |
| `results/plots/` | Visualizations (generated if matplotlib is available) |

## Quick Start

```bash
cd simulations/blue-pulse
python blue_pulse_simulation.py
```

To run with different parameter variants:

```bash
python blue_pulse_simulation.py --variant low
python blue_pulse_simulation.py --variant high
```

## Scenarios

| Units | Scale |
|---|---|
| 1 | Single proof-of-concept unit |
| 100 | Small field array |
| 1,000 | Coastal experimental corridor |
| 10,000 | Large upwelling-zone deployment |
| 50,000 | Basin-scale experimental infrastructure |
| 100,000 | Very large deployment (saturation regime) |

## Key Model Behaviors

- **Coverage** saturates as `1 - exp(-total_area / target_area)`
- **Risk** grows as `effective_coverage ** 1.35` plus fog, governance, and
  circulation uncertainty components
- **Benefits** cap at model-defined maximums to prevent unrealistic outputs
- At large scales, risk index grows faster than ecosystem recovery index

## Cautions

- These outputs should not be compared to real oceanographic data.
- The model does not simulate real ocean circulation, real weather feedbacks,
  real carbon-cycle tonnage, or real ecological dynamics.
- OBS and UMC have not been demonstrated at operational scale in the real world.

## Related Documentation

- [Blue Pulse concept page](../../docs/concepts/blue-pulse.md)
- [Blue Pulse Simulation Model](../../docs/concepts/blue-pulse-simulation-model.md)
- [Ocean Breathing System](../../docs/concepts/ocean-breathing-system.md)
- [Ultrasonic Mist Cooling](../../docs/concepts/ultrasonic-mist-cooling.md)
- [Intervention Ethics](../../docs/concepts/intervention-ethics.md)
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[output] MD   -> {path}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Blue Pulse Conceptual Simulation (toy model, not a real forecast)"
    )
    parser.add_argument("--config", default=CONFIG_PATH, help="Path to YAML config file")
    parser.add_argument(
        "--variant", default="default", choices=["low", "default", "high"],
        help="Parameter variant to use"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Blue Pulse Conceptual Simulation")
    print("TOY MODEL -- NOT A REAL CLIMATE FORECAST")
    print("=" * 60)
    print(f"Config:  {args.config}")
    print(f"Variant: {args.variant}")
    print()

    params = load_config(args.config, args.variant)
    variant = args.variant
    scenarios = params.get("deployment_scenarios", [1, 100, 1000, 10000, 50000, 100000])

    results = []
    for n in scenarios:
        r = simulate_scenario(n, params, variant)
        results.append(r)
        print(f"  {n:>8,} units  |  coverage {r['effective_coverage_percent']:5.1f}%  "
              f"|  SST Δ {r['regional_mean_sst_reduction_c']:.4f}°C  "
              f"|  risk {r['intervention_risk_index_0_100']:.1f}")

    print()
    write_csv(results, CSV_PATH)
    write_summary(results, params, variant, SUMMARY_PATH)
    write_sim_readme(SCRIPT_DIR)
    write_plots_readme(PLOTS_DIR)

    if MATPLOTLIB_AVAILABLE:
        make_plots(results, PLOTS_DIR)
    else:
        print("[info] matplotlib not available — skipping plots")

    print()
    print("Done. All outputs written.")
    print(f"  CSV:     {CSV_PATH}")
    print(f"  Summary: {SUMMARY_PATH}")
    if MATPLOTLIB_AVAILABLE:
        print(f"  Plots:   {PLOTS_DIR}")
    print()
    print("REMINDER: These are illustrative toy-model outputs, not climate forecasts.")


if __name__ == "__main__":
    main()
