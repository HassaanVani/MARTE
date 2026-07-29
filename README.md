# MARTE

## Project description

Relativistic mission-planning simulator that combines orbital mechanics, optimization, and an interactive visualization dashboard.

## Architecture

`marte/` is the scientific-model core; `server/` exposes computation; `frontend/` renders orbital, timeline, diagnostics, and tradeoff views; deployment files containerize the system.

## Technology

Python • React • TypeScript • Vite • Docker

## Run locally

See `VISION.md`; run frontend and Python server separately.

## Repository guide

The implementation is organized so that entry points remain thin and domain-specific logic stays in the modules named above. Configuration, assets, and deployment files are kept separate from application code. Review the source tree before changing behavior, and keep secrets in local environment files rather than committing them.
