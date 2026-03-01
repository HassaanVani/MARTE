"""JPL Horizons ephemeris integration for real astronomical body positions.

Uses urllib.request (stdlib) — no new dependencies. Fetches vector tables
from the JPL Horizons API and caches them as .npz files.

MARTE epoch convention: t=0 corresponds to J2000.0 (Julian Date 2451545.0).
"""

import hashlib
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from marte.constants import AU, J2000_JD

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
CACHE_DIR = Path.home() / ".marte" / "ephemeris"

# Seconds per day
_SECONDS_PER_DAY = 86400.0


def marte_time_to_jd(t_s: float) -> float:
    """Convert MARTE time (seconds since J2000.0) to Julian Date."""
    return J2000_JD + t_s / _SECONDS_PER_DAY


def jd_to_marte_time(jd: float) -> float:
    """Convert Julian Date to MARTE time (seconds since J2000.0)."""
    return (jd - J2000_JD) * _SECONDS_PER_DAY


def marte_time_to_calendar(t_s: float) -> str:
    """Convert MARTE time to ISO calendar date string for Horizons queries.

    Returns format like '2000-01-01' suitable for Horizons START_TIME/STOP_TIME.
    """
    jd = marte_time_to_jd(t_s)
    # Julian Date to calendar date conversion
    # Algorithm from Meeus, "Astronomical Algorithms" (1991)
    jd_plus = jd + 0.5
    z = int(jd_plus)
    f = jd_plus - z
    if z < 2299161:
        a = z
    else:
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    # Add fractional day as time
    hours = int(f * 24)
    return f"{year:04d}-{month:02d}-{day:02d} {hours:02d}:00"


def _cache_key(body_id: str, start_jd: float, end_jd: float, step_days: int) -> str:
    """Generate a cache filename from query parameters."""
    key_str = f"{body_id}_{start_jd:.6f}_{end_jd:.6f}_{step_days}"
    h = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return f"horizons_{body_id}_{h}.npz"


@dataclass
class EphemerisData:
    """Interpolatable ephemeris data for a solar system body.

    All quantities in MARTE frame (meters, m/s, seconds since J2000.0).
    """

    times_s: NDArray[np.float64]       # shape (N,)
    positions_m: NDArray[np.float64]   # shape (N, 3)
    velocities_m_s: NDArray[np.float64]  # shape (N, 3)

    def position(self, t_s: float) -> NDArray[np.float64]:
        """Interpolate position at MARTE time t_s (seconds since J2000.0).

        Uses cubic spline interpolation per component.
        """
        from scipy.interpolate import CubicSpline
        result = np.zeros(3)
        for i in range(3):
            cs = CubicSpline(self.times_s, self.positions_m[:, i])
            result[i] = float(cs(t_s))
        return result

    def velocity(self, t_s: float) -> NDArray[np.float64]:
        """Interpolate velocity at MARTE time t_s (seconds since J2000.0)."""
        from scipy.interpolate import CubicSpline
        result = np.zeros(3)
        for i in range(3):
            cs = CubicSpline(self.times_s, self.velocities_m_s[:, i])
            result[i] = float(cs(t_s))
        return result


def _parse_horizons_vectors(text: str) -> tuple[list[float], list[list[float]], list[list[float]]]:
    """Parse a JPL Horizons vector table response.

    Expects TABLE_TYPE='VECTORS' format with:
    JDTDB, Calendar Date, X, Y, Z, VX, VY, VZ, ...

    Returns:
        (jd_list, positions_km, velocities_km_s)
    """
    # Find data between $$SOE and $$EOE markers
    soe = text.find("$$SOE")
    eoe = text.find("$$EOE")
    if soe == -1 or eoe == -1:
        raise ValueError("Could not find $$SOE/$$EOE markers in Horizons response")

    data_block = text[soe + 5:eoe].strip()
    lines = [line.strip() for line in data_block.split("\n") if line.strip()]

    jd_list = []
    positions_km = []
    velocities_km_s = []

    # Horizons vector output: every 2 lines form a record
    # Line 1: JDTDB = val, Calendar Date (TDB), ...
    # Line 2: X = val Y = val Z = val
    # Line 3: VX= val VY= val VZ= val
    # (Sometimes all on 2 lines with different formatting)

    # Try to detect format by looking for 'X =' pattern
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for JD line
        jd_match = re.match(r"^\s*([\d.]+)\s*=?\s*", line)
        if jd_match:
            jd = float(jd_match.group(1))
            jd_list.append(jd)

            # Next line(s) should have X, Y, Z and VX, VY, VZ
            if i + 2 < len(lines):
                pos_line = lines[i + 1]
                vel_line = lines[i + 2]

                # Parse X = val Y = val Z = val
                pos_vals = re.findall(r"[-+]?\d+\.\d+[Ee][+-]?\d+", pos_line)
                vel_vals = re.findall(r"[-+]?\d+\.\d+[Ee][+-]?\d+", vel_line)

                if len(pos_vals) >= 3 and len(vel_vals) >= 3:
                    positions_km.append([float(v) for v in pos_vals[:3]])
                    velocities_km_s.append([float(v) for v in vel_vals[:3]])
                    i += 3
                    continue

        i += 1

    return jd_list, positions_km, velocities_km_s


class HorizonsClient:
    """Client for the JPL Horizons API with local caching."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_body_ephemeris(
        self,
        body_id: str,
        t_start_s: float,
        t_end_s: float,
        step_days: int = 1,
    ) -> EphemerisData:
        """Fetch ephemeris for a body from JPL Horizons.

        Args:
            body_id: Horizons body ID (e.g., "399" for Earth, "599" for Jupiter).
            t_start_s: Start time in MARTE seconds since J2000.0.
            t_end_s: End time in MARTE seconds since J2000.0.
            step_days: Time step in days.

        Returns:
            EphemerisData with positions/velocities in meters and m/s.
        """
        start_jd = marte_time_to_jd(t_start_s)
        end_jd = marte_time_to_jd(t_end_s)

        # Check cache
        cache_file = self.cache_dir / _cache_key(body_id, start_jd, end_jd, step_days)
        if cache_file.exists():
            data = np.load(str(cache_file))
            return EphemerisData(
                times_s=data["times_s"],
                positions_m=data["positions_m"],
                velocities_m_s=data["velocities_m_s"],
            )

        # Build Horizons query
        start_cal = marte_time_to_calendar(t_start_s)
        end_cal = marte_time_to_calendar(t_end_s)

        params = {
            "format": "text",
            "COMMAND": f"'{body_id}'",
            "EPHEM_TYPE": "VECTORS",
            "CENTER": "'500@0'",  # Solar System Barycenter
            "START_TIME": f"'{start_cal}'",
            "STOP_TIME": f"'{end_cal}'",
            "STEP_SIZE": f"'{step_days}d'",
            "REF_PLANE": "'ECLIPTIC'",
            "REF_SYSTEM": "'J2000'",
            "OUT_UNITS": "'KM-S'",
            "VEC_TABLE": "'2'",  # position + velocity
            "VEC_CORR": "'NONE'",
            "CSV_FORMAT": "'NO'",
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{HORIZONS_URL}?{query}"

        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                text = resp.read().decode("utf-8")
        except Exception as e:
            raise ConnectionError(f"Failed to fetch from JPL Horizons: {e}") from e

        jd_list, positions_km, velocities_km_s = _parse_horizons_vectors(text)

        if len(jd_list) == 0:
            raise ValueError("No data points parsed from Horizons response")

        # Convert to MARTE units: km → m, km/s → m/s
        times_s = np.array([jd_to_marte_time(jd) for jd in jd_list])
        positions_m = np.array(positions_km) * 1000.0  # km → m
        velocities_m_s = np.array(velocities_km_s) * 1000.0  # km/s → m/s

        # Cache
        np.savez(
            str(cache_file),
            times_s=times_s,
            positions_m=positions_m,
            velocities_m_s=velocities_m_s,
        )

        return EphemerisData(
            times_s=times_s,
            positions_m=positions_m,
            velocities_m_s=velocities_m_s,
        )


# Module-level singleton client
_client: HorizonsClient | None = None


def _get_client() -> HorizonsClient:
    global _client
    if _client is None:
        _client = HorizonsClient()
    return _client


def fetch_earth_ephemeris(
    t_start_s: float,
    t_end_s: float,
    step_days: int = 1,
) -> EphemerisData:
    """Convenience function to fetch Earth ephemeris.

    Args:
        t_start_s: Start time in MARTE seconds since J2000.0.
        t_end_s: End time in MARTE seconds since J2000.0.
        step_days: Time step in days.

    Returns:
        EphemerisData for Earth.
    """
    return _get_client().fetch_body_ephemeris("399", t_start_s, t_end_s, step_days)
