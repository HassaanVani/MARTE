"""Shared fixtures for MARTE test suite."""

import pytest


@pytest.fixture
def standard_betas() -> list[float]:
    """Common beta values used across test modules."""
    return [0.0, 0.1, 0.3, 0.6, 0.866, 0.9, 0.99, 0.999]


@pytest.fixture
def reference_mass() -> float:
    """Reference spacecraft mass (kg) — 1000 kg."""
    return 1000.0


@pytest.fixture
def rel_tolerance() -> float:
    """Default relative tolerance for floating-point comparisons."""
    return 1e-9


@pytest.fixture
def abs_tolerance() -> float:
    """Default absolute tolerance for floating-point comparisons (meters)."""
    return 1.0
