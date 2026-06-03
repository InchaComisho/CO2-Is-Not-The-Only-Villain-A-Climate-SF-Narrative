"""
Trinity Equatorial Belt Conceptual Simulation
==============================================

IMPORTANT DISCLAIMER
--------------------
This is a simplified educational toy model for the fictional Trinity Model in the
narrative "If I Had Believed CO2 Was the Only Villain, Earth Would Have Been Checkmated."

This script is NOT:
  - a real climate forecast
  - an engineering validation
  - a policy recommendation
  - a substitute for peer-reviewed oceanographic or land-surface science

All outputs are illustrative scenario estimates under stated assumptions.
They are designed to support narrative understanding of how a three-pillar
equatorial-belt intervention might compare across deployment scales.

The Trinity Model combines:
  - OBS  (Ocean Breathing System / deep ocean aeration) -- from below
  - UMC  (Ultrasonic Mist Cooling) -- from above, over ocean and land
  - Soil Regeneration -- restoring terrestrial carbon sinks

The equatorial belt grid is a simplified toy mask, not a real geographic model.

Usage
-----
    python trinity_equatorial_belt_simulation.py [--config PATH]

Output
------
    results/sample_results.csv
    results/sample_summary.md
    results/plots/  (if matplotlib is available)
"""

import math
import csv
import os
import argparse
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config", "default_parameters.yml")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
PLOTS_DIR   = os.path.join(RESULTS_DIR, "plots")
CSV_PATH    = os.path.join(RESULTS_DIR, "sample_results.csv")
SUMMARY_PATH = os.path.join(RESULTS_DIR, "sample_summary.md")

# ---------------------------------------------------------------------------
# Built-in default parameters (fallback if YAML unavailable)
# ---------------------------------------------------------------------------

DEFAULT_PARAMS = {
    "equatorial_belt": {
        "latitude_min": -15, "latitude_max": 15,
        "longitude_min": -180, "longitude_max": 180,
        "grid_resolution_degrees": 5,
    },
    "deployment_scenarios": [1, 100, 1000, 10000, 50000, 100000, 250000, 500000],
    "deployment_allocation": {
        "ocean_obs_share": 0.50,
        "ocean_umc_share": 0.20,
        "land_umc_share": 0.15,
        "land_soil_regeneration_share": 0.15,
    },
    "unit_effective_area_km2": {
        "ocean_obs_default": 2500,
        "ocean_umc_default": 2000,
        "land_umc_default": 1500,
        "soil_regeneration_default": 1000,
    },
    "effect_strength": {
        "obs_ocean_heat_reduction_local_c": 0.12,
        "umc_ocean_peak_heat_reduction_local_c": 0.10,
        "umc_land_peak_heat_reduction_local_c": 0.18,
        "soil_carbon_sink_recovery_per_coverage": 0.35,
        "soil_water_retention_recovery_per_coverage": 0.30,
        "ecosystem_recovery_per_coverage": 0.25,
    },
    "synergy": {
        "ocean_obs_umc_synergy_factor": 1.15,
        "land_umc_soil_synergy_factor": 1.25,
        "ocean_land_coupling_factor": 0.20,
        "trinity_system_synergy_factor": 1.10,
    },
    "saturation": {
        "max_ocean_heat_reduction_c": 0.35,
        "max_land_heat_reduction_c": 0.50,
        "max_carbon_sink_recovery_percent": 40,
        "max_compound_risk_reduction_percent": 45,
    },
    "baseline": {
        "baseline_super_el_nino_sst_anomaly_c": 2.0,
        "baseline_marine_heatwave_days": 120,
    },
    "risk": {
        "ocean_intervention_risk_exponent": 1.35,
        "land_intervention_risk_exponent": 1.15,
        "governance_risk_exponent": 1.40,
        "public_trust_risk_exponent": 1.30,
        "max_intervention_risk": 100,
    },
    "land_regions": {
        "south_america": {"lon_min": -82, "lon_max": -35, "lat_min": -15, "lat_max": 15},
        "africa":        {"lon_min": -20, "lon_max":  50, "lat_min": -15, "lat_max": 15},
        "southeast_asia":{"lon_min":  95, "lon_max": 150, "lat_min": -10, "lat_max": 15},
        "north_australia":{"lon_min":120, "lon_max": 150, "lat_min": -15, "lat_max": -5},
    },
}

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path):
    if YAML_AVAILABLE and os.path.isfile(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data
    print("[info] YAML config not found or yaml unavailable. Using built-in defaults.")
    return DEFAULT_PARAMS.copy()

# ---------------------------------------------------------------------------
# Land / ocean mask (simplified toy model)
# ---------------------------------------------------------------------------

REGION_CODES = {
    "south_america": 1,
    "africa": 2,
    "southeast_asia": 3,
    "north_australia": 4,
}


def classify_cell(lat, lon, land_regions):
    """Return region name if land, None if ocean. Uses OR logic (first match wins)."""
    for name, box in land_regions.items():
        if (box["lon_min"] <= lon <= box["lon_max"]
                and box["lat_min"] <= lat <= box["lat_max"]):
            return name
    return None

# ---------------------------------------------------------------------------
# Grid builder
# ---------------------------------------------------------------------------

def build_grid(params):
    """
    Build simplified equatorial belt grid cells.
    Returns cells list, total ocean area km2, total land area km2,
    list of lat centers, list of lon centers.
    """
    belt = params.get("equatorial_belt", DEFAULT_PARAMS["equatorial_belt"])
    land_regions = params.get("land_regions", DEFAULT_PARAMS["land_regions"])
    res = belt["grid_resolution_degrees"]
    lat_min, lat_max = belt["latitude_min"], belt["latitude_max"]
    lon_min, lon_max = belt["longitude_min"], belt["longitude_max"]

    lats, lons = [], []
    lat = lat_min + res / 2.0
    while lat < lat_max - 1e-9:
        lats.append(round(lat, 6))
        lat += res
    lon = lon_min + res / 2.0
    while lon < lon_max - 1e-9:
        lons.append(round(lon, 6))
        lon += res

    cells = []
    for lat_c in lats:
        for lon_c in lons:
            # Approximate cell area using spherical Earth
            lat_rad = math.radians(lat_c)
            area_km2 = (res * 111.32) ** 2 * abs(math.cos(lat_rad))
            region = classify_cell(lat_c, lon_c, land_regions)
            cells.append({
                "lat": lat_c,
                "lon": lon_c,
                "area_km2": area_km2,
                "region": region,
                "is_land": region is not None,
            })

    total_ocean = sum(c["area_km2"] for c in cells if not c["is_land"])
    total_land  = sum(c["area_km2"] for c in cells if c["is_land"])
    return cells, total_ocean, total_land, lats, lons, res

# ---------------------------------------------------------------------------
# Coverage formula
# ---------------------------------------------------------------------------

def sat_coverage(effective_area_km2, target_area_km2):
    """Saturation coverage: 1 - exp(-effective_area / target_area)."""
    if target_area_km2 <= 0:
        return 0.0
    return 1.0 - math.exp(-effective_area_km2 / target_area_km2)

# ---------------------------------------------------------------------------
# Core simulation function
# ---------------------------------------------------------------------------

MAX_SCENARIO = 500000  # used for governance risk normalization


def simulate_scenario(unit_count, params, total_ocean_km2, total_land_km2):
    """
    Compute illustrative conceptual outputs for a given deployment unit count.
    All values are toy-model estimates, not real-world forecasts.
    """
    alloc   = params.get("deployment_allocation", DEFAULT_PARAMS["deployment_allocation"])
    areas   = params.get("unit_effective_area_km2", DEFAULT_PARAMS["unit_effective_area_km2"])
    fx      = params.get("effect_strength", DEFAULT_PARAMS["effect_strength"])
    syn     = params.get("synergy", DEFAULT_PARAMS["synergy"])
    sat     = params.get("saturation", DEFAULT_PARAMS["saturation"])
    base    = params.get("baseline", DEFAULT_PARAMS["baseline"])
    rsk     = params.get("risk", DEFAULT_PARAMS["risk"])

    # -- Unit allocation --
    obs_n   = unit_count * alloc.get("ocean_obs_share", 0.50)
    oumc_n  = unit_count * alloc.get("ocean_umc_share", 0.20)
    lumc_n  = unit_count * alloc.get("land_umc_share", 0.15)
    soil_n  = unit_count * alloc.get("land_soil_regeneration_share", 0.15)

    # -- Coverage per pillar --
    obs_area  = obs_n  * areas.get("ocean_obs_default",       2500)
    oumc_area = oumc_n * areas.get("ocean_umc_default",       2000)
    lumc_area = lumc_n * areas.get("land_umc_default",        1500)
    soil_area = soil_n * areas.get("soil_regeneration_default", 1000)

    obs_cov  = sat_coverage(obs_area,  total_ocean_km2)
    oumc_cov = sat_coverage(oumc_area, total_ocean_km2)
    lumc_cov = sat_coverage(lumc_area, total_land_km2)
    soil_cov = sat_coverage(soil_area, total_land_km2)

    # -- Effect strength values --
    obs_sst  = fx.get("obs_ocean_heat_reduction_local_c", 0.12)
    umc_osst = fx.get("umc_ocean_peak_heat_reduction_local_c", 0.10)
    umc_lsst = fx.get("umc_land_peak_heat_reduction_local_c", 0.18)
    soil_c   = fx.get("soil_carbon_sink_recovery_per_coverage", 0.35)
    soil_w   = fx.get("soil_water_retention_recovery_per_coverage", 0.30)
    eco_rate = fx.get("ecosystem_recovery_per_coverage", 0.25)

    # -- Synergy values --
    o_syn    = syn.get("ocean_obs_umc_synergy_factor", 1.15)
    l_syn    = syn.get("land_umc_soil_synergy_factor", 1.25)
    tri_syn  = syn.get("trinity_system_synergy_factor", 1.10)

    # -- Saturation caps --
    max_o_c  = sat.get("max_ocean_heat_reduction_c", 0.35)
    max_l_c  = sat.get("max_land_heat_reduction_c", 0.50)
    max_c_pct = sat.get("max_carbon_sink_recovery_percent", 40)
    max_cmp  = sat.get("max_compound_risk_reduction_percent", 45)

    # -- Baseline --
    base_sst = base.get("baseline_super_el_nino_sst_anomaly_c", 2.0)

    # ==========================================================
    # OCEAN HEAT STRESS REDUCTION
    # ==========================================================
    ocean_local_raw = (obs_sst * obs_cov + umc_osst * oumc_cov) * o_syn
    ocean_local = min(max_o_c, ocean_local_raw)
    ocean_heat_pct = min(35.0, ocean_local / base_sst * 100.0)

    # ==========================================================
    # LAND HEAT STRESS REDUCTION
    # ==========================================================
    land_heat_raw = umc_lsst * lumc_cov * l_syn
    land_heat = min(max_l_c, land_heat_raw)
    # Reference: 2.5 C as illustrative land heat anomaly under stress
    land_heat_pct = min(35.0, land_heat / 2.5 * 100.0)

    # ==========================================================
    # SOIL / CARBON SINK RECOVERY
    # ==========================================================
    soil_recovery_pct    = min(max_c_pct, soil_cov * soil_c * 100.0)
    water_retention_pct  = min(max_c_pct, soil_cov * soil_w * 100.0)

    eco_raw = (soil_cov * eco_rate + lumc_cov * 0.10 + obs_cov * 0.08) * 100.0
    ecosystem_recovery_pct = min(max_c_pct, eco_raw)

    # Terrestrial carbon sink = soil_recovery
    terrestrial_carbon_pct = soil_recovery_pct

    # ==========================================================
    # OCEAN CARBON SINK PROXY
    # ==========================================================
    ocean_carbon_pct = min(35.0, obs_cov * 25.0 + oumc_cov * 5.0)

    # ==========================================================
    # COMPOUND RISK REDUCTION
    # ==========================================================
    compound_raw = (
        0.25 * ocean_heat_pct
        + 0.15 * land_heat_pct
        + 0.20 * soil_recovery_pct
        + 0.10 * water_retention_pct
        + 0.15 * ocean_carbon_pct
        + 0.15 * ecosystem_recovery_pct
    ) * tri_syn
    compound_risk_reduction = min(max_cmp, compound_raw)

    # ==========================================================
    # INTERVENTION RISK INDEX
    # ==========================================================
    o_exp   = rsk.get("ocean_intervention_risk_exponent", 1.35)
    l_exp   = rsk.get("land_intervention_risk_exponent", 1.15)
    g_exp   = rsk.get("governance_risk_exponent", 1.40)
    t_exp   = rsk.get("public_trust_risk_exponent", 1.30)
    max_r   = rsk.get("max_intervention_risk", 100)

    avg_ocean_cov = (obs_cov + oumc_cov) / 2.0
    avg_land_cov  = (lumc_cov + soil_cov) / 2.0
    avg_all_cov   = (avg_ocean_cov + avg_land_cov) / 2.0

    ocean_risk = 100.0 * (avg_ocean_cov ** o_exp)
    land_risk  = 100.0 * (avg_land_cov  ** l_exp)
    norm_dep   = min(1.0, unit_count / MAX_SCENARIO)
    gov_risk   = 100.0 * (norm_dep ** g_exp)
    trust_risk = 100.0 * (avg_all_cov  ** t_exp)

    total_risk = min(max_r,
        0.30 * ocean_risk
        + 0.20 * land_risk
        + 0.30 * gov_risk
        + 0.20 * trust_risk
    )

    benefit_risk_balance = round(compound_risk_reduction - total_risk, 2)

    # ==========================================================
    # CONFIDENCE + INTERPRETATION
    # ==========================================================
    conf_map = {
        1:      "observation only",
        100:    "very low -- speculative",
        1000:   "low -- illustrative",
        10000:  "low-medium -- optimistic illustrative",
        50000:  "medium -- scenario only",
        100000: "medium -- saturation regime beginning",
        250000: "low-medium -- high uncertainty, stress test",
        500000: "low -- extreme scenario, toy model limit",
    }
    interp_map = {
        1:      "Single conceptual test / observation only. No regional effect in any pillar.",
        100:    "Small pilot array; effects remain mostly local. Indistinguishable from noise at regional scale.",
        1000:   "Regional signals may begin to appear in sensitive equatorial zones under optimistic assumptions.",
        10000:  "Meaningful equatorial-belt scenario in the toy model; emerging signal in ocean zone.",
        50000:  "Large-scale deployment; measurable ocean heat reduction; governance and ecological risk growing.",
        100000: "Saturation beginning; trinity compound effect stronger, but risk and management burden dominate.",
        250000: "Very large planetary-scale conceptual infrastructure; not an operational recommendation.",
        500000: "Extreme scenario for stress-testing the toy model; high uncertainty throughout.",
    }

    return {
        "deployment_units": unit_count,
        "ocean_obs_units":          int(obs_n),
        "ocean_umc_units":          int(oumc_n),
        "land_umc_units":           int(lumc_n),
        "soil_regeneration_units":  int(soil_n),
        "ocean_obs_coverage_percent":          round(obs_cov  * 100, 2),
        "ocean_umc_coverage_percent":          round(oumc_cov * 100, 2),
        "land_umc_coverage_percent":           round(lumc_cov * 100, 2),
        "soil_regeneration_coverage_percent":  round(soil_cov * 100, 2),
        "ocean_heat_stress_reduction_percent": round(ocean_heat_pct, 2),
        "estimated_ocean_sst_reduction_c":     round(ocean_local, 4),
        "land_heat_stress_reduction_percent":  round(land_heat_pct, 2),
        "estimated_land_surface_peak_reduction_c": round(land_heat, 4),
        "soil_recovery_percent":               round(soil_recovery_pct, 2),
        "water_retention_recovery_percent":    round(water_retention_pct, 2),
        "ocean_carbon_sink_recovery_percent":  round(ocean_carbon_pct, 2),
        "terrestrial_carbon_sink_recovery_percent": round(terrestrial_carbon_pct, 2),
        "ecosystem_recovery_percent":          round(ecosystem_recovery_pct, 2),
        "compound_risk_reduction_percent":     round(compound_risk_reduction, 2),
        "intervention_risk_index_0_100":       round(total_risk, 2),
        "benefit_risk_balance":                benefit_risk_balance,
        "confidence_level":   conf_map.get(unit_count, "low -- illustrative"),
        "interpretation":     interp_map.get(unit_count, "Illustrative scenario."),
    }

# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

FIELDS = [
    "deployment_units",
    "ocean_obs_units", "ocean_umc_units", "land_umc_units", "soil_regeneration_units",
    "ocean_obs_coverage_percent", "ocean_umc_coverage_percent",
    "land_umc_coverage_percent", "soil_regeneration_coverage_percent",
    "ocean_heat_stress_reduction_percent", "estimated_ocean_sst_reduction_c",
    "land_heat_stress_reduction_percent", "estimated_land_surface_peak_reduction_c",
    "soil_recovery_percent", "water_retention_recovery_percent",
    "ocean_carbon_sink_recovery_percent", "terrestrial_carbon_sink_recovery_percent",
    "ecosystem_recovery_percent",
    "compound_risk_reduction_percent", "intervention_risk_index_0_100",
    "benefit_risk_balance", "confidence_level", "interpretation",
]


def write_csv(results, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(results)
    print("[output] CSV  ->", path)

# ---------------------------------------------------------------------------
# Markdown summary
# ---------------------------------------------------------------------------

SCALE_LABELS = {
    1:      "Single test unit",
    100:    "Tiny pilot",
    1000:   "Small regional test",
    10000:  "Regional deployment",
    50000:  "Large-scale deployment",
    100000: "Basin-scale infrastructure",
    250000: "Continental-scale infrastructure",
    500000: "Extreme scenario (toy model limit)",
}

MAIN_BENEFIT = {
    1:      "Local observation only",
    100:    "Near-zero signal",
    1000:   "Detectable local effects in ocean zone",
    10000:  "Emerging signal in tropical ocean zone",
    50000:  "Measurable ocean heat reduction in zone",
    100000: "Meaningful compound risk reduction signal",
    250000: "Strong ocean coverage; saturation",
    500000: "Near-total belt coverage (toy model)",
}

MAIN_LIMITATION = {
    1:      "No regional effect",
    100:    "Indistinguishable from noise at regional scale",
    1000:   "Negligible compound-risk reduction",
    10000:  "Governance and ecological attribution unclear",
    50000:  "Risk index growing; governance burden significant",
    100000: "Saturation beginning; risk dominates in governance and ocean",
    250000: "Very high risk; not an operational recommendation",
    500000: "Toy model stress test; real-world feasibility not modeled",
}


def write_summary(results, params, path, total_ocean, total_land):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Trinity Equatorial Belt Simulation -- Sample Summary",
        "",
        "> **IMPORTANT:** These results are outputs of a simplified educational toy model.",
        "> They are NOT real climate forecasts, NOT engineering validation, and NOT policy",
        "> recommendations. All values are illustrative scenario estimates.",
        "",
        f"Generated: {ts}",
        "",
        "---",
        "",
        "## What Is Being Simulated",
        "",
        "- OBS / deep ocean aeration in the tropical ocean belt (50% of deployment units)",
        "- UMC / mist cooling over tropical ocean surface cells (20%)",
        "- UMC / mist cooling over equatorial land surface cells (15%)",
        "- Soil regeneration over equatorial land regions (15%)",
        "- Combined trinity effect with synergy factors",
        "",
        "### Simplified Grid",
        f"- Total belt ocean area (toy model): {total_ocean/1e6:.1f} million km2",
        f"- Total belt land area (toy model):  {total_land/1e6:.1f} million km2",
        f"- Unit effective areas: OBS ocean={params.get('unit_effective_area_km2',{}).get('ocean_obs_default',2500)} km2, "
        f"UMC ocean={params.get('unit_effective_area_km2',{}).get('ocean_umc_default',2000)} km2, "
        f"UMC land={params.get('unit_effective_area_km2',{}).get('land_umc_default',1500)} km2, "
        f"Soil={params.get('unit_effective_area_km2',{}).get('soil_regeneration_default',1000)} km2",
        "",
        "---",
        "",
        "## Coverage Summary",
        "",
        "| Units | OBS Ocean % | UMC Ocean % | UMC Land % | Soil % |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['deployment_units']:,} "
            f"| {r['ocean_obs_coverage_percent']:.1f}% "
            f"| {r['ocean_umc_coverage_percent']:.1f}% "
            f"| {r['land_umc_coverage_percent']:.1f}% "
            f"| {r['soil_regeneration_coverage_percent']:.1f}% |"
        )

    lines += [
        "",
        "---",
        "",
        "## Compound Risk Reduction vs. Intervention Risk",
        "",
        "| Units | Compound Risk Reduction | Intervention Risk | Balance | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['deployment_units']:,} "
            f"| {r['compound_risk_reduction_percent']:.1f}% "
            f"| {r['intervention_risk_index_0_100']:.1f} "
            f"| {r['benefit_risk_balance']:+.1f} "
            f"| {r['confidence_level']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Scale Interpretation Table",
        "",
        "| Units | Expected Scale | Main Benefit | Main Limitation |",
        "|---|---|---|---|",
    ]
    for r in results:
        u = r["deployment_units"]
        lines.append(
            f"| {u:,} "
            f"| {SCALE_LABELS.get(u, '---')} "
            f"| {MAIN_BENEFIT.get(u, '---')} "
            f"| {MAIN_LIMITATION.get(u, '---')} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Main Finding (Conceptual)",
        "",
        "- Small deployments (1-1,000 units) mostly provide observation and proof-of-concept.",
        "- Around 10,000 units, the model begins to show an emerging signal in the ocean zone.",
        "- Around 50,000-100,000 units, compound risk reduction grows but intervention risk grows faster.",
        "- Above 100,000 units, benefits begin to saturate while governance, ecological,",
        "  maintenance, and public-trust risks dominate.",
        "- The Trinity Model shows greater compound-risk improvement than ocean-only Blue Pulse",
        "  because it acts on ocean heat, land heat stress, and soil carbon sinks together.",
        "- However, this improvement remains conceptual and should not be read as an operational proposal.",
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ]

    for r in results:
        lines += [
            f"### {r['deployment_units']:,} Units",
            "",
            f"- OBS ocean coverage: **{r['ocean_obs_coverage_percent']:.1f}%**",
            f"- UMC ocean coverage: **{r['ocean_umc_coverage_percent']:.1f}%**",
            f"- UMC land coverage: **{r['land_umc_coverage_percent']:.1f}%**",
            f"- Soil regen coverage: **{r['soil_regeneration_coverage_percent']:.1f}%**",
            f"- Ocean heat stress reduction: **{r['ocean_heat_stress_reduction_percent']:.2f}%** "
            f"(est. SST delta: {r['estimated_ocean_sst_reduction_c']:.4f} degC)",
            f"- Land heat stress reduction: **{r['land_heat_stress_reduction_percent']:.2f}%** "
            f"(est. surface delta: {r['estimated_land_surface_peak_reduction_c']:.4f} degC)",
            f"- Soil recovery: **{r['soil_recovery_percent']:.2f}%**",
            f"- Water retention recovery: **{r['water_retention_recovery_percent']:.2f}%**",
            f"- Ocean carbon sink proxy: **{r['ocean_carbon_sink_recovery_percent']:.2f}%**",
            f"- Terrestrial carbon sink proxy: **{r['terrestrial_carbon_sink_recovery_percent']:.2f}%**",
            f"- Ecosystem recovery proxy: **{r['ecosystem_recovery_percent']:.2f}%**",
            f"- Compound risk reduction: **{r['compound_risk_reduction_percent']:.2f}%**",
            f"- Intervention risk index: **{r['intervention_risk_index_0_100']:.2f} / 100**",
            f"- Benefit-risk balance: **{r['benefit_risk_balance']:+.2f}**",
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
        "- The belt grid is a simplified toy mask, not a real geographic model.",
        "- Unit effective areas (km2 per cluster) are illustrative and not derived from",
        "  real engineering data.",
        "- Carbon uptake proxies are not in real carbon tonnage.",
        "- Risk index values do not map to any real governance or safety threshold.",
        "- The benefit-risk balance metric is an illustrative construct only.",
        "",
        "---",
        "",
        "## See Also",
        "",
        "- [Trinity Equatorial Belt Simulation docs](../../docs/concepts/trinity-equatorial-belt-simulation.md)",
        "- [Trinity Model concept](../../docs/concepts/trinity-model.md)",
        "- [Blue Pulse Simulation](../blue-pulse/results/sample_summary.md)",
        "- [Intervention Ethics](../../docs/concepts/intervention-ethics.md)",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("[output] MD   ->", path)

# ---------------------------------------------------------------------------
# Simulation README (auto-generated)
# ---------------------------------------------------------------------------

def write_sim_readme(sim_dir):
    path = os.path.join(sim_dir, "README.md")
    content = """\
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
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[output] MD   ->", path)

# ---------------------------------------------------------------------------
# Plots directory README
# ---------------------------------------------------------------------------

def write_plots_readme(plots_dir):
    path = os.path.join(plots_dir, "README.md")
    content = """\
# Trinity Equatorial Belt Simulation -- Plots

> **IMPORTANT:** All plots are outputs of a simplified educational toy model.
> They are NOT real climate forecasts. They are illustrative scenario comparisons.

## Generated Plots

| File | Description |
|---|---|
| `deployment_scale_vs_compound_risk_reduction.png` | Compound risk reduction across all deployment scales |
| `deployment_scale_vs_ocean_heat_stress_reduction.png` | Ocean heat stress reduction estimate |
| `deployment_scale_vs_land_heat_stress_reduction.png` | Land heat stress reduction estimate |
| `deployment_scale_vs_carbon_sink_recovery.png` | Ocean and terrestrial carbon sink proxies |
| `deployment_scale_vs_intervention_risk.png` | Benefit vs. risk comparison |
| `equatorial_belt_concept_map.png` | Simplified conceptual grid map (NOT a real map) |

## Notes

- All y-axis values are illustrative estimates, not real measurements.
- Scaling is nonlinear due to exponential saturation formula.
- Risk grows faster than benefit at large scales.

## See Also

- [Simulation README](../README.md)
- [Trinity Equatorial Belt Simulation docs](../../../docs/concepts/trinity-equatorial-belt-simulation.md)
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[output] MD   ->", path)

# ---------------------------------------------------------------------------
# Plot helpers
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
    "lines.linewidth": 2.2,
    "lines.markersize": 8,
}


def apply_style():
    for k, v in PLOT_STYLE.items():
        try:
            plt.rcParams[k] = v
        except Exception:
            pass


def x_labels(results):
    return [f"{r['deployment_units']:,}" for r in results]


def add_disclaimer(ax, text="Conceptual toy model -- not a climate forecast"):
    ax.text(0.01, 0.98, text, transform=ax.transAxes,
            fontsize=7, color="#8b949e", va="top", ha="left")


def save_fig(fig, name, plots_dir):
    fig.tight_layout()
    path = os.path.join(plots_dir, name)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print("[output] Plot ->", path)

# ---------------------------------------------------------------------------
# Individual plots
# ---------------------------------------------------------------------------

def plot_compound_risk_reduction(results, plots_dir):
    apply_style()
    x = list(range(len(results)))
    xl = x_labels(results)
    vals = [r["compound_risk_reduction_percent"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, vals, color="#58a6ff", marker="o", label="Compound risk reduction (%)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#58a6ff")
    ax.set_xticks(x); ax.set_xticklabels(xl, rotation=30, ha="right", fontsize=9)
    ax.set_title("Trinity Model -- Deployment Scale vs. Compound Risk Reduction\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units (Total)")
    ax.set_ylabel("Illustrative Compound Risk Reduction (%)")
    ax.legend(fontsize=9); ax.grid(True)
    add_disclaimer(ax)
    save_fig(fig, "deployment_scale_vs_compound_risk_reduction.png", plots_dir)


def plot_ocean_heat(results, plots_dir):
    apply_style()
    x = list(range(len(results)))
    xl = x_labels(results)
    vals = [r["ocean_heat_stress_reduction_percent"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, vals, color="#79c0ff", marker="s", label="Ocean heat stress reduction (%)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#79c0ff")
    ax.set_xticks(x); ax.set_xticklabels(xl, rotation=30, ha="right", fontsize=9)
    ax.set_title("Trinity Model -- Deployment Scale vs. Ocean Heat Stress Reduction\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units (Total)")
    ax.set_ylabel("Illustrative Heat Stress Reduction (%)")
    ax.legend(fontsize=9); ax.grid(True)
    add_disclaimer(ax)
    save_fig(fig, "deployment_scale_vs_ocean_heat_stress_reduction.png", plots_dir)


def plot_land_heat(results, plots_dir):
    apply_style()
    x = list(range(len(results)))
    xl = x_labels(results)
    vals = [r["land_heat_stress_reduction_percent"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, vals, color="#56d364", marker="^", label="Land heat stress reduction (%)")
    ax.fill_between(x, 0, vals, alpha=0.18, color="#56d364")
    ax.set_xticks(x); ax.set_xticklabels(xl, rotation=30, ha="right", fontsize=9)
    ax.set_title("Trinity Model -- Deployment Scale vs. Land Heat Stress Reduction\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units (Total)")
    ax.set_ylabel("Illustrative Heat Stress Reduction (%)")
    ax.legend(fontsize=9); ax.grid(True)
    add_disclaimer(ax)
    save_fig(fig, "deployment_scale_vs_land_heat_stress_reduction.png", plots_dir)


def plot_carbon_sink(results, plots_dir):
    apply_style()
    x = list(range(len(results)))
    xl = x_labels(results)
    ocean_c = [r["ocean_carbon_sink_recovery_percent"] for r in results]
    terr_c  = [r["terrestrial_carbon_sink_recovery_percent"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, ocean_c, color="#79c0ff", marker="o", label="Ocean carbon sink proxy (%)")
    ax.plot(x, terr_c,  color="#56d364", marker="s", linestyle="--",
            label="Terrestrial carbon sink proxy (%)")
    ax.set_xticks(x); ax.set_xticklabels(xl, rotation=30, ha="right", fontsize=9)
    ax.set_title("Trinity Model -- Deployment Scale vs. Carbon Sink Recovery Proxies\n(Conceptual simulation -- NOT real carbon tonnage)", fontsize=11)
    ax.set_xlabel("Deployed Units (Total)")
    ax.set_ylabel("Illustrative Recovery Proxy (%)")
    ax.legend(fontsize=9); ax.grid(True)
    add_disclaimer(ax, "Proxy indices only -- not real carbon tonnage")
    save_fig(fig, "deployment_scale_vs_carbon_sink_recovery.png", plots_dir)


def plot_intervention_risk(results, plots_dir):
    apply_style()
    x = list(range(len(results)))
    xl = x_labels(results)
    compound = [r["compound_risk_reduction_percent"] for r in results]
    risk     = [r["intervention_risk_index_0_100"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, compound, color="#58a6ff", marker="o", label="Compound risk reduction (%)")
    ax.plot(x, risk,     color="#da3633", marker="v", linestyle="--",
            label="Intervention risk index (0-100)")
    ax.fill_between(x, compound, risk,
                    where=[r > c for r, c in zip(risk, compound)],
                    alpha=0.12, color="#da3633", label="Risk > Benefit zone")
    ax.set_ylim(0, 110)
    ax.set_xticks(x); ax.set_xticklabels(xl, rotation=30, ha="right", fontsize=9)
    ax.set_title("Trinity Model -- Compound Benefit vs. Intervention Risk\n(Conceptual simulation)", fontsize=11)
    ax.set_xlabel("Deployed Units (Total)")
    ax.set_ylabel("Index / Percentage (illustrative)")
    ax.legend(fontsize=9); ax.grid(True)
    add_disclaimer(ax)
    save_fig(fig, "deployment_scale_vs_intervention_risk.png", plots_dir)

# ---------------------------------------------------------------------------
# Equatorial belt concept map
# ---------------------------------------------------------------------------

# Region code -> (name, color)
REGION_COLORS = {
    None: ("#0e2240", "Open ocean"),          # deep navy
    "south_america": ("#2d6a1a", "South America land"),  # forest green
    "africa":        ("#6b5a0e", "Africa land"),          # ochre
    "southeast_asia":("#0e5a5a", "SE Asia / Indonesia"), # teal
    "north_australia":("#5a3a0e", "N. Australia edge"),  # brown
}


def plot_concept_map(cells, lats, lons, res, plots_dir):
    """Draw simplified equatorial belt concept map (NOT a real geographic model)."""
    apply_style()

    n_lats = len(lats)
    n_lons = len(lons)

    # Build 2D color array
    color_grid = []
    for lat_c in lats:
        row = []
        for lon_c in lons:
            region = None
            for c in cells:
                if abs(c["lat"] - lat_c) < 1e-3 and abs(c["lon"] - lon_c) < 1e-3:
                    region = c["region"]
                    break
            row.append(REGION_COLORS.get(region, (REGION_COLORS[None][0], ""))[0])
        color_grid.append(row)

    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # Draw each cell as a rectangle
    for i, lat_c in enumerate(lats):
        for j, lon_c in enumerate(lons):
            region = None
            for c in cells:
                if abs(c["lat"] - lat_c) < 1e-3 and abs(c["lon"] - lon_c) < 1e-3:
                    region = c["region"]
                    break
            color = REGION_COLORS.get(region, (REGION_COLORS[None][0], ""))[0]
            rect = plt.Rectangle(
                (lon_c - res/2, lat_c - res/2), res, res,
                facecolor=color, edgecolor="#21262d", linewidth=0.3
            )
            ax.add_patch(rect)

    # Equator line
    ax.axhline(0, color="#8b949e", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.text(175, 0.5, "Equator", color="#8b949e", fontsize=7, va="bottom", ha="right")

    # Region labels
    region_labels = [
        (-60, 2, "South America"),
        (15, 5, "Africa"),
        (120, 5, "SE Asia"),
        (135, -13, "Australia"),
    ]
    for lx, ly, lab in region_labels:
        ax.text(lx, ly, lab, color="#e6edf3", fontsize=7, ha="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#21262d", alpha=0.7))

    # Legend patches
    legend_patches = [
        mpatches.Patch(color=v[0], label=v[1])
        for k, v in REGION_COLORS.items()
    ]
    ax.legend(handles=legend_patches, loc="lower left", fontsize=7,
              facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9")

    ax.set_xlim(-180, 180)
    ax.set_ylim(-15, 15)
    ax.set_xlabel("Longitude", color="#c9d1d9", fontsize=9)
    ax.set_ylabel("Latitude", color="#c9d1d9", fontsize=9)
    ax.set_title(
        "Simplified Equatorial Belt Concept Map -- Trinity Model Deployment Zones\n"
        "(TOY MASK -- NOT a real geographic model. Regions are approximate rectangular boxes.)",
        fontsize=10, color="#c9d1d9"
    )
    ax.tick_params(colors="#8b949e", labelsize=8)

    add_disclaimer(ax, "This is a conceptual grid, not a real climate or geographic model.")
    save_fig(fig, "equatorial_belt_concept_map.png", plots_dir)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Trinity Equatorial Belt Conceptual Simulation (toy model)"
    )
    parser.add_argument("--config", default=CONFIG_PATH)
    args = parser.parse_args()

    print("=" * 60)
    print("Trinity Equatorial Belt Conceptual Simulation")
    print("TOY MODEL -- NOT A REAL CLIMATE FORECAST")
    print("=" * 60)
    print("Config:", args.config)
    print()

    params = load_config(args.config)
    scenarios = params.get("deployment_scenarios",
                           DEFAULT_PARAMS["deployment_scenarios"])

    # Build grid
    cells, total_ocean, total_land, lats, lons, res = build_grid(params)
    n_ocean = sum(1 for c in cells if not c["is_land"])
    n_land  = sum(1 for c in cells if c["is_land"])
    print(f"Grid: {len(cells)} cells  |  "
          f"Ocean: {n_ocean} cells ({total_ocean/1e6:.1f}M km2)  |  "
          f"Land: {n_land} cells ({total_land/1e6:.1f}M km2)")
    print()

    # Run scenarios
    results = []
    for n in scenarios:
        r = simulate_scenario(n, params, total_ocean, total_land)
        results.append(r)
        print(
            f"  {n:>8,} units  |  "
            f"OBS cov {r['ocean_obs_coverage_percent']:5.1f}%  |  "
            f"compound {r['compound_risk_reduction_percent']:5.2f}%  |  "
            f"risk {r['intervention_risk_index_0_100']:5.1f}"
        )

    print()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    write_csv(results, CSV_PATH)
    write_summary(results, params, SUMMARY_PATH, total_ocean, total_land)
    write_sim_readme(SCRIPT_DIR)
    write_plots_readme(PLOTS_DIR)

    if MATPLOTLIB_AVAILABLE:
        os.makedirs(PLOTS_DIR, exist_ok=True)
        plot_compound_risk_reduction(results, PLOTS_DIR)
        plot_ocean_heat(results, PLOTS_DIR)
        plot_land_heat(results, PLOTS_DIR)
        plot_carbon_sink(results, PLOTS_DIR)
        plot_intervention_risk(results, PLOTS_DIR)
        plot_concept_map(cells, lats, lons, res, PLOTS_DIR)
    else:
        print("[info] matplotlib not available -- skipping plots")

    print()
    print("Done. All outputs written.")
    print("  CSV:    ", CSV_PATH)
    print("  Summary:", SUMMARY_PATH)
    if MATPLOTLIB_AVAILABLE:
        print("  Plots:  ", PLOTS_DIR)
    print()
    print("REMINDER: These are illustrative toy-model outputs, not climate forecasts.")


if __name__ == "__main__":
    main()
