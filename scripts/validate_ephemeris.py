#!/usr/bin/env python3
"""Cross-validate internal MARTE orbital approximations against JPL Horizons."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from marte.constants import YEAR, AU
from marte.ephemeris import _get_client
from marte.orbital import earth_position
from marte.targets import target_position

ARTIFACTS_DIR = Path("/Users/hassaanvani/.gemini/antigravity/brain/92e566b7-5ff4-44c0-8ccd-883f60f76285/artifacts")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def run_validation():
    print("Fetching JPL Horizons ephemeris data...")
    client = _get_client()
    
    t_start = 0.0
    t_end = 5.0 * YEAR
    n_days = 365 * 5
    times = np.linspace(t_start, t_end, n_days)
    
    # Earth (399), Mars (499)
    earth_horizons = client.fetch_body_ephemeris("399", t_start, t_end, step_days=1)
    mars_horizons = client.fetch_body_ephemeris("499", t_start, t_end, step_days=1)
    
    earth_circ_errs = []
    earth_ellip_errs = []
    mars_circ_errs = []
    
    print("Computing deviations...")
    for t in times:
        e_horiz = earth_horizons.position(t)
        e_circ = earth_position(t, elliptical=False)
        e_ellip = earth_position(t, elliptical=True)
        
        m_horiz = mars_horizons.position(t)
        m_circ = target_position("mars", t)
        
        earth_circ_errs.append(np.linalg.norm(e_horiz - e_circ) / AU)
        earth_ellip_errs.append(np.linalg.norm(e_horiz - e_ellip) / AU)
        mars_circ_errs.append(np.linalg.norm(m_horiz - m_circ) / AU)
        
    t_years = times / YEAR
    
    print("\n--- Error Summary ---")
    print(f"Earth (Circular) Max Error: {np.max(earth_circ_errs):.5f} AU")
    print(f"Earth (Circular) Mean Error: {np.mean(earth_circ_errs):.5f} AU")
    print(f"Earth (Elliptical) Max Error: {np.max(earth_ellip_errs):.5f} AU")
    print(f"Earth (Elliptical) Mean Error: {np.mean(earth_ellip_errs):.5f} AU")
    print(f"Mars (Circular) Max Error: {np.max(mars_circ_errs):.5f} AU")
    print(f"Mars (Circular) Mean Error: {np.mean(mars_circ_errs):.5f} AU")

    plt.figure(figsize=(10, 6))
    plt.plot(t_years, earth_circ_errs, label="Earth (Circular)", color="blue")
    plt.plot(t_years, earth_ellip_errs, label="Earth (Elliptical)", color="cyan", linestyle="--")
    plt.plot(t_years, mars_circ_errs, label="Mars (Circular)", color="red")
    
    plt.title("Orbital Model Divergence from JPL Horizons")
    plt.xlabel("Time (Years)")
    plt.ylabel("Positional Error (AU)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    plot_path = ARTIFACTS_DIR / "ephemeris_divergence.png"
    plt.savefig(plot_path, dpi=150)
    print(f"\nPlot saved to {plot_path}")
    
    # Save a markdown report fragment so we can include it in our main report
    report_content = f"""
## Validation Results

| Target / Model | Max Deviation (AU) | Mean Deviation (AU) |
| --- | --- | --- |
| **Earth** (Circular) | {np.max(earth_circ_errs):.5f} | {np.mean(earth_circ_errs):.5f} |
| **Earth** (Elliptical) | {np.max(earth_ellip_errs):.5f} | {np.mean(earth_ellip_errs):.5f} |
| **Mars** (Circular) | {np.max(mars_circ_errs):.5f} | {np.mean(mars_circ_errs):.5f} |
"""
    with open(ARTIFACTS_DIR / "ephemeris_report_data.md", "w") as f:
        f.write(report_content)

if __name__ == "__main__":
    run_validation()
