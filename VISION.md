# MARTE — Multi-frame Astrodynamic Relativistic Trajectory Engine

> *"If my calculations are correct, when this baby hits 88 miles per hour... you're gonna see some serious shit."*

---

## 1. What MARTE Is

MARTE is a **relativistic trajectory solver and spacetime visualization platform**.

It computes physically correct spacecraft trajectories under special relativity, resolving the constrained problem of departing from Earth, traveling at relativistic speeds, and arriving back at Earth's future orbital position — all while honoring the traveler's desired proper time.

If a relativistic spacecraft existed, MARTE is the navigation system it would run.

### What MARTE is not

- Not a game.
- Not a cinematic space simulator.
- Not a sci-fi aesthetic exercise.
- Not a toy orbit viewer.
- Not a proof of concept.

MARTE is a **physics-first engineering tool** that happens to produce compelling visualizations as a consequence of modeling real spacetime geometry.

---

## 2. The Ambition

The defining ambition of MARTE is not to demonstrate that relativistic navigation is theoretically possible. That has been known for a century.

The ambition is to **build the software now** — with the same rigor, correctness, and operational fidelity that would be required if the hardware existed today — so that when relativistic propulsion becomes an engineering reality (not a physics question, but an engineering timeline), the navigation system is already done.

**The software is ahead of its time. We are waiting for the hardware.**

This is not a metaphor. It is a design constraint. Every architectural decision, every physics module, every interface contract in MARTE is evaluated against this question:

> *If an engineer at a propulsion lab handed us a spacecraft capable of 0.6c sustained thrust, could MARTE compute its mission trajectory tomorrow?*

The answer must be yes.

### What this means in practice

- **The physics engine must be flight-grade.** Not "good enough for a demo." Not "illustrative." Correct to the tolerance required for actual trajectory planning. If MARTE says the ship arrives at $(x, y, z)$ at time $t_f$, it arrives there.

- **The solver must handle real constraints.** Not toy problems with hand-picked parameters. Arbitrary departure times, arbitrary arrival windows, arbitrary proper time targets. If the problem is physically feasible, MARTE solves it. If it is infeasible, MARTE proves it and explains why.

- **The architecture must be operationally extensible.** When better orbital models, real ephemeris data, GR corrections, or thrust profile constraints are added, the solver adapts without redesign. The system was built expecting these upgrades from the start.

- **The validation must be rigorous enough to earn trust.** Not "it looks right." Not "the numbers seem reasonable." Every output is verifiable against analytical solutions, conservation laws, and limiting cases. A skeptical physicist can audit any result.

MARTE is not ahead of its time because it looks futuristic. It is ahead of its time because it **works** — for a machine that doesn't exist yet.

---

## 3. The Problem

### Inputs

| Symbol | Meaning |
|--------|---------|
| $t_0$ | Departure coordinate time (Solar System Barycentric Frame) |
| $t_f$ | Desired Earth arrival coordinate time |
| $\tau$ | Desired traveler proper time (experienced duration) |

### Outputs

| Output | Description |
|--------|-------------|
| $v$ | Required velocity magnitude (as fraction of $c$) |
| $\hat{d}_{out}$ | Outbound direction unit vector |
| $t_{turn}$ | Turnaround coordinate time |
| $\hat{d}_{in}$ | Inbound direction unit vector |
| $\mathbf{r}_{ship}(t)$ | Full ship worldline |
| $E_{req}$ | Minimum energy requirement |

### Constraints

1. **Spatial intersection**: The ship worldline must intersect Earth's worldline at $t_f$.

$$\mathbf{r}_{ship}(t_f) = \mathbf{r}_{Earth}(t_f)$$

2. **Proper time match**: The integrated proper time along the ship worldline must equal $\tau$.

$$\tau = \int_{t_0}^{t_f} \sqrt{1 - \frac{v(t)^2}{c^2}} \, dt$$

3. **Subluminal bound**: $|v| < c$ at all times.

This is a **nonlinear constrained root-finding problem** coupling orbital mechanics with special relativity.

---

## 4. Physics Model

### 4.1 Reference Frame

All calculations occur in the **Solar System Barycentric Inertial Frame (SSBIF)**.

- One consistent inertial reference frame.
- No frame-switching during computation.
- Visualization layers may transform into other frames for display purposes, but the physics core never leaves SSBIF.

### 4.2 Earth Orbital Model

**Version 1** — Circular orbit approximation:

$$\mathbf{r}_E(t) = \begin{pmatrix} R \cos(\omega t) \\ R \sin(\omega t) \\ 0 \end{pmatrix}$$

where $R = 1 \text{ AU}$, $\omega = 2\pi / T_{year}$.

**Upgrade path:**

| Version | Model |
|---------|-------|
| v1 | Circular orbit |
| v2 | Keplerian elliptical orbit (eccentricity, inclination, argument of perihelion) |
| v3 | JPL Horizons ephemeris integration (SPICE kernels or Horizons API) |
| v4 | Full N-body perturbation from major Solar System bodies |

Each upgrade is a drop-in replacement of the `earth_position(t)` function. The trajectory solver is agnostic to the orbital model — it only asks "where is Earth at time $t$?"

### 4.3 Ship Trajectory Model

**Version 1** — Piecewise constant velocity:

```
Phase 1: Instantaneous acceleration at t_0 to velocity v_out
Phase 2: Constant relativistic cruise (outbound)
Phase 3: Instantaneous turnaround at t_turn
Phase 4: Constant relativistic cruise (inbound)
Phase 5: Instantaneous deceleration at t_f
```

This is the simplest trajectory model that captures the essential relativistic time-dilation structure. It is analytically tractable and makes the root-finding problem low-dimensional.

**Upgrade path:**

| Version | Model |
|---------|-------|
| v1 | Instantaneous acceleration / constant velocity |
| v2 | Constant proper acceleration (relativistic rocket equation) |
| v3 | Arbitrary thrust profiles with fuel mass constraints |
| v4 | Optimal control trajectories (minimize fuel, minimize proper time, etc.) |

### 4.4 Relativity Module

The relativity module provides the mathematical primitives:

| Function | Definition |
|----------|------------|
| Lorentz factor | $\gamma(v) = (1 - v^2/c^2)^{-1/2}$ |
| Proper time integral | $\tau = \int \gamma^{-1} \, dt$ |
| Minkowski interval | $ds^2 = -c^2 dt^2 + dx^2 + dy^2 + dz^2$ |
| Rapidity | $\phi = \text{arctanh}(v/c)$ |
| Relativistic kinetic energy | $E_k = (\gamma - 1)mc^2$ |
| Relativistic momentum | $p = \gamma m v$ |

These are pure functions. No state. No side effects. Fully unit-testable against known analytical results.

### 4.5 Trajectory Solver

The solver is the mathematical core. It takes the constrained problem and finds the unknowns via numerical root-finding.

**Unknowns** (Version 1):
- Velocity magnitude $|v|$
- Outbound direction $\hat{d}_{out}$ (2 angular DOF)
- Turnaround time $t_{turn}$

**Equations** (Version 1):
- $\mathbf{r}_{ship}(t_f) = \mathbf{r}_{Earth}(t_f)$ — 3 scalar equations
- $\tau_{computed} = \tau_{desired}$ — 1 scalar equation

4 unknowns, 4 equations. The system is well-posed (though potentially multi-valued — multiple valid trajectories may exist for a given set of inputs).

**Solver strategy:**
- SciPy `fsolve` or `root` for the nonlinear system
- Bracketing methods where monotonicity can be established
- Multi-start initialization to find all solution branches
- Convergence validation and residual checking

---

## 5. Architecture

MARTE is structured as a **layered, modular system** with strict separation between physics computation and visual presentation.

```
┌──────────────────────────────────────────────────┐
│                 Visualization Layer               │
│         (Three.js / Matplotlib / Unity)           │
├──────────────────────────────────────────────────┤
│                    API Layer                      │
│            (FastAPI / WebSocket bridge)            │
├──────────────────────────────────────────────────┤
│                  Physics Engine                   │
│                    (Python)                        │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Relativity │ │  Orbital   │ │  Trajectory  │  │
│  │   Module    │ │  Mechanics │ │    Solver    │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Spacetime  │ │  Units &   │ │  Validation  │  │
│  │  Geometry   │ │  Constants │ │    Suite     │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
└──────────────────────────────────────────────────┘
```

### 5.1 Physics Engine (Python)

The physics engine is the heart of MARTE. It is a pure Python library with no rendering dependencies.

**Responsibilities:**
- Compute Earth position at any coordinate time
- Compute ship worldlines from trajectory parameters
- Integrate proper time along worldlines
- Solve the constrained trajectory problem
- Compute energy requirements
- Validate physical consistency (subluminal, causal, energy-bounded)

**Dependencies:** NumPy, SciPy. Optionally SymPy for symbolic cross-verification.

**Non-responsibilities:** Rendering, UI, user interaction, file I/O for display.

### 5.2 API Layer

A thin bridge exposing the physics engine to external consumers.

- **REST endpoints** for one-shot trajectory computation
- **WebSocket** for live parameter sweeps and streaming simulation state
- **Serialization** of worldlines, proper time curves, and diagnostic data into JSON

Framework: FastAPI (lightweight, async, auto-documented).

### 5.3 Visualization Layer

The visualization layer reads computed physics data and renders it. It never computes physics.

**Phase 1:** Matplotlib / Plotly — static and interactive 2D/3D plots for development and validation.

**Phase 2:** Three.js web frontend — interactive 3D spacetime visualization with control panels.

**Phase 3 (optional):** Unity — immersive, high-fidelity navigation console experience.

Each visualization layer is a **consumer** of the physics engine output. Swapping one for another requires zero changes to the physics code.

### 5.4 The SpacetimeState Object

The physics engine does not return a list of coordinates. It returns a **`SpacetimeState`** — a self-contained snapshot of the complete physical state at a single instant. This object is the commodity that every visualization layer consumes.

```json
{
  "coordinate_time": 1740528000.0,
  "proper_time_elapsed": 31536000.0,
  "position_ssbif": [1.49e11, 0, 0],
  "velocity_beta": 0.866,
  "lorentz_factor": 2.0,
  "proper_acceleration": 9.81,
  "aberration_matrix": [["..."]],
  "doppler_factor_forward": 3.732,
  "doppler_factor_aft": 0.268,
  "energy_k_joules": 1.2e20,
  "earth_position_ssbif": [1.48e11, 2.1e10, 0],
  "earth_light_delay_seconds": 498.0,
  "earth_apparent_position": [1.47e11, 1.9e10, 0]
}
```

This object can drive a scientific Matplotlib plot, a Three.js Minkowski diagram, a WebGL cockpit HUD, or a Unity VR bridge — and the physics is identical in every case. The `SpacetimeState` is the contract between the engine and all downstream consumers.

---

## 6. The Dual-Interface Architecture

MARTE has two faces. They share the same physics engine and the same `SpacetimeState` stream. They show radically different things.

### 6.1 The Observer Interface — "Mission Control"

This is the scientific ground truth. It treats the traveler as a point-particle worldline viewed from outside spacetime. It is the interface for **planning, analysis, and verification**.

**Design aesthetic:**
- High-density vector graphics, dark mode
- Amber or NASA-blue accents
- Monospace fonts (Fira Code / JetBrains Mono)
- No decoration that doesn't encode data
- Inspired by mission control telemetry, not consumer dashboards

**Key elements:**

#### The Spacetime Loom

A dynamic Minkowski diagram where the user can drag **Event Pins**. Drag the arrival event further into the future and watch the ship's worldline slope change in real-time. Drag the proper time constraint and watch the solver find a new velocity. The diagram is not a static plot — it is a **direct manipulation interface** for the trajectory solver.

#### The Residual Monitor

A small terminal window showing the SciPy solver's convergence in real-time: iteration count, residual norm, Jacobian condition number. This is not debug output — it is a deliberate design choice. Users see the software **solving** the relativistic constraints. It reinforces that MARTE is computing something hard, not animating something prerecorded.

#### The Energy Tax

A prominent readout showing $E_k = (\gamma - 1)mc^2$. As $\beta \to 1$, the numbers turn red and begin scaling against real-world references:

| $\beta$ | $\gamma$ | Energy | Scale |
|---------|----------|--------|-------|
| 0.1 | 1.005 | $4.5 \times 10^{17}$ J | ~10 Tsar Bomba |
| 0.5 | 1.155 | $1.4 \times 10^{19}$ J | ~1% global annual energy |
| 0.866 | 2.0 | $9.0 \times 10^{19}$ J | ~15% global annual energy |
| 0.99 | 7.089 | $5.5 \times 10^{20}$ J | ~100% global annual energy |
| 0.999 | 22.37 | $1.9 \times 10^{21}$ J | ~300% global annual energy |

The Energy Tax is not a warning. It is a **fact**. The user must understand what relativistic travel costs.

#### Spatial View (3D Orbital Plane)

- Earth's orbit rendered as a closed curve (or helical if showing time axis)
- Ship trajectory rendered as a piecewise path from departure to arrival
- Earth position highlighted at $t_0$, $t_{turn}$, and $t_f$
- Ship position animated along its worldline
- Turnaround point marked
- Arrival intersection verified visually

#### Proper Time vs. Coordinate Time

- Side-by-side clocks showing traveler time and Earth-frame time
- Accumulation curves: $\tau(t)$ plotted against $t$
- Differential time dilation rate: $d\tau/dt = \gamma^{-1}$

---

### 6.2 The Kinetic Interface — "The Pilot"

This moves the camera **onto the ship**. It uses the physics engine to compute what a human observer (or ship sensor array) would actually perceive at relativistic velocity. This is not a creative liberty — it is a direct consequence of the `SpacetimeState` fields for aberration and Doppler shift.

**Design aesthetic:**
- Diegetic UI — the interface exists inside the simulation world
- 3D cockpit or heads-up display overlaying a computed starfield
- No elements that break the frame of reference

**Key elements:**

#### The Time-Lag Ghost

A projected hologram of Earth in the HUD. Because of finite light-travel time, the pilot sees Earth where it **was** — but a "Physics Ghost" (computed from the `SpacetimeState`) shows where Earth **actually is** in the SSBIF frame. To return home, you must aim for the Ghost, not the image.

This is not a game mechanic. It is the physical reality of navigating at relativistic speed: your eyes lie. The `earth_apparent_position` in the state object is always behind the `earth_position_ssbif`. The delta is $c \times \text{light\_delay}$.

#### The Relativistic Throttle

Increasing thrust does not just increase speed. It changes:

- **Star color** — Doppler shift compresses incoming wavelengths forward and stretches them aft. Both are computed directly from $\beta$ and the aberration matrix.
- **Field of view** — Relativistic aberration compresses the star field forward. At high $\beta$, stars behind the ship migrate toward the forward hemisphere.

Visual consequence at $\beta \to 1$:
- The stars behind vanish into a **red void** (infinite redshift, below visible band)
- The stars ahead crush into a **blue blinding point** (extreme blueshift, aberration collapse)

This is special relativity rendered honestly. No artistic license.

#### The Waiting Mechanic

To convey the reality of relativistic travel, the Kinetic interface can offer a **Time-Skip** mode: set thrust to $1g$, and the UI shows the **Subjective Calendar** (proper time) ticking alongside the **Home Calendar** (coordinate time) as the ship spends weeks or months accelerating to cruise velocity. The divergence between the two calendars is the visceral experience of time dilation.

---

## 7. Validation Strategy

MARTE's credibility depends on verification against known analytical results.

### 7.1 Unit Tests

Every physics function tested against hand-calculated or textbook values:

- $\gamma(0) = 1$
- $\gamma(0.6c) = 1.25$
- $\gamma(0.866c) = 2.0$
- Proper time for round-trip at $0.6c$ over 10 ly: verify against twin paradox solution
- Energy at $0.99c$: verify against known relativistic kinetic energy

### 7.2 Conservation Checks

- Proper time is always less than coordinate time for $v > 0$
- $\gamma \geq 1$ always
- $|v| < c$ always
- Minkowski interval sign is correct for timelike worldlines

### 7.3 Convergence Validation

- Solver residuals below machine epsilon tolerance
- Multiple initializations converge to consistent solutions
- Edge cases: $v \to 0$ (Newtonian limit), $v \to c$ (ultra-relativistic limit)

### 7.4 Cross-Verification

- SymPy symbolic solutions for simplified cases
- Comparison to published relativistic travel tables
- Independent reimplementation of core functions for comparison

---

## 8. Development Phases

### Phase 1 — Physics Prototype

**Goal:** Correct, tested physics engine with Matplotlib output.

Deliverables:
- [ ] Earth orbital model (circular, including orbital velocity $\sim 30$ km/s)
- [ ] Relativity module (γ, proper time, energy)
- [ ] Piecewise constant-velocity ship trajectory
- [ ] Trajectory solver (root-finding)
- [ ] Proper time integration
- [ ] Relativistic velocity addition for Earth-relative rendezvous
- [ ] Validation suite
- [ ] Matplotlib visualizations: orbital plot, Minkowski diagram, τ(t) curve
- [ ] CLI interface for parameter input

> [!NOTE]
> Even in the circular-orbit approximation, Earth moves at $\beta \approx 0.0001$. This is small but nonzero. A flight-grade tool must apply relativistic velocity addition between the ship's inbound vector and Earth's orbital velocity at $t_f$. This is not optional — it is the difference between a toy and an instrument.

**Exit criteria:** A physicist can input $(t_0, t_f, \tau)$ and receive a verified trajectory with proper time match. All unit tests pass. Earth's orbital velocity is correctly composed with the ship velocity at rendezvous.

---

### Phase 2 — Web Visualization

**Goal:** Interactive Three.js frontend consuming the physics engine via API.

Deliverables:
- [ ] FastAPI server exposing trajectory computation
- [ ] Three.js 3D orbital visualization
- [ ] Interactive Minkowski diagram
- [ ] Parameter input panel (departure time, arrival time, proper time)
- [ ] Real-time trajectory recomputation on parameter change
- [ ] Proper time / coordinate time comparison display
- [ ] Energy budget display
- [ ] Deployable to Netlify (static frontend) + Railway/Render (API backend)

**Exit criteria:** A user can open the web interface, set parameters, and see correct, interactive visualizations of the computed trajectory.

---

### Phase 3 — Advanced Physics

**Goal:** Physically richer trajectory models. This phase eliminates the most significant idealization in Version 1: instantaneous acceleration.

> [!IMPORTANT]
> In v1, the instantaneous turnaround requires infinite energy — it is a mathematical convenience, not a physical trajectory. Phase 3 must replace this with **constant proper acceleration** (typically $1g$ for crew comfort) as the primary trajectory mode. Relativistic navigation is fundamentally about hyperbolic worldlines, not piecewise-linear segments. This is the single most important physics upgrade in the roadmap.

Deliverables:
- [ ] Constant proper acceleration trajectories (relativistic rocket equation: $x = \frac{c^2}{a}(\cosh(a\tau/c) - 1)$, $t = \frac{c}{a}\sinh(a\tau/c)$)
- [ ] $1g$ comfort acceleration as default mode
- [ ] Hyperbolic worldline rendering (replaces straight-line segments on Minkowski diagram)
- [ ] Fuel mass modeling via Tsiolkovsky-relativistic rocket equation
- [ ] ΔE budget with exhaust velocity parameter
- [ ] **Jerk-limited acceleration profiles** — smooth transitions between acceleration phases via configurable $da/d\tau$ (jerk) bounds
- [ ] **Configurable crew g-tolerance** — with pressure suits and g-couches, the human body can sustain $3$–$9g$ for limited durations. MARTE should accept a **g-tolerance profile** (max sustained $g$, max peak $g$, max peak duration) and compute the fastest trajectory that stays within the envelope. $1g$ comfort remains the default; high-g burst mode is the option.
- [ ] Smooth acceleration ramp-up/ramp-down curves replacing the step-function transition between $0$ and $a_{max}$
- [ ] Elliptical Earth orbit
- [ ] Multi-solution branch detection and display
- [ ] Rapidity-based parameterization

> [!NOTE]
> Jerk is not cosmetic. An instantaneous jump from $0$ to $5g$ is as unphysical as an instantaneous jump to $0.6c$ — it just fails at a different scale. Modeling $j = da/d\tau$ correctly means the solver produces trajectories that are not only relativistically correct but **mechanically survivable**. This is what separates a trajectory planner from a physics demo.

**Exit criteria:** Trajectories with finite acceleration are correct, worldlines are hyperbolic, and energy/fuel budgets are physically meaningful. The $1g$ round-trip to Proxima Centauri produces the textbook result ($\sim 3.5$ years proper time each way). A $5g$-burst profile for the same trip produces a measurably shorter proper time with smooth jerk-limited transitions.

---

### Phase 4 — General Relativity & Ephemeris

**Goal:** Gravitational effects and real astronomical data.

Deliverables:
- [ ] Gravitational time dilation near massive bodies
- [ ] Schwarzschild metric corrections for near-body passes
- [ ] JPL Horizons ephemeris integration for Earth position
- [ ] Multi-body gravitational perturbation
- [ ] Comparison: SR-only vs. GR-corrected trajectories

**Exit criteria:** MARTE can compute trajectories using real ephemeris data with GR corrections, and the magnitude of GR effects is quantified.

---

### Phase 5 — Navigation Console

**Goal:** Production-grade interface for trajectory planning.

Deliverables:
- [ ] Full navigation console UI (Three.js or Unity)
- [ ] Multi-target support (not just Earth return)
- [ ] Mission planning mode (parameter sweeps, tradeoff curves)
- [ ] Export: trajectory data, worldline coordinates, mission reports
- [ ] Optimal trajectory computation (minimize energy, minimize proper time, etc.)

**Exit criteria:** MARTE functions as a self-contained mission planning tool.

---

### The Interface Fork

Starting from Phase 2, the Observer and Kinetic interfaces evolve in parallel. Both consume the same `SpacetimeState` stream. Their development is coupled by physics, not by UI.

| Phase | **Observer — Mission Control** | **Kinetic — The Pilot** |
|-------|-------------------------------|-------------------------|
| **Phase 2** | Web-based 2D Plotly/Matplotlib dashboards. Spacetime Loom (static). Residual Monitor. | Basic Three.js starfield with Doppler-shift shaders. |
| **Phase 3** | Integration of hyperbolic worldlines ($1g$ paths). Drag-to-solve Spacetime Loom. Energy Tax readout. | "Manual Mode" — user controls thrust vector; engine computes the resulting worldline and visual effects in real-time. |
| **Phase 4** | **The Intercept Solver** — auto-calculate the exact vector and turnaround time to hit Earth's future ephemeris position. | **The Nav-Computer** — a HUD element that tells the pilot "turn around NOW" to make the return window. Time-Lag Ghost computed from real ephemeris. |
| **Phase 5** | Multi-mission planning. Parameter sweeps. Fleet sync (multiple ships, different departure times). | VR support — "standing on the bridge" while the universe warps around you. Full aberration + Doppler starfield. |

---

## 9. Design Philosophy

### Physics before pixels

The physics must be correct before any visual is rendered. A beautiful but wrong visualization is worse than an ugly correct one. Build the engine first. Render it second.

### Modularity as a constraint

Every module has one job. The relativity module does not know about orbits. The orbital module does not know about rendering. The solver calls both but does neither. Boundaries are enforced by architecture, not discipline.

### Extensibility by substitution

Upgrading the Earth model from circular to Keplerian to ephemeris should require changing one function and zero solver code. The same for upgrading from instantaneous to continuous acceleration. Interfaces are designed for this from day one.

### Validation as a feature

The test suite is not an afterthought. It is a deliverable. Every physics function ships with its proof of correctness. If a function cannot be tested against a known result, its implementation is suspect.

### The physicist test

If a physics graduate student reads the source code, it should withstand scrutiny. Variable names match standard notation. Equations are cited. Units are explicit. Approximations are documented. This is the bar.

### The engineering test

If a propulsion engineer walks into the room with a relativistic drive and asks "can your software plan my mission?", the answer is not "almost" or "with some modifications." The answer is yes. The interfaces accept real parameters. The solver handles real constraints. The outputs are in real units at real precision. MARTE is not a prototype of navigation software. It **is** navigation software — tested against every scenario we can construct without the hardware, and architected to absorb every scenario the hardware will eventually reveal.

---

## 10. Technical Constraints

| Constraint | Rationale |
|------------|-----------|
| Python for physics core | Scientific computing ecosystem, SciPy/NumPy, rapid iteration |
| No physics in the frontend | Visualization is a consumer, not a producer, of physics data |
| SI units internally | Avoid unit conversion errors; display layer handles formatting |
| Speed of light is not 1 | Natural units obscure bugs. Use $c = 299792458 \text{ m/s}$ everywhere. |
| No global state in physics modules | Pure functions enable testing, parallelism, and reproducibility |
| Deterministic solver | Same inputs → same outputs. No randomized initialization without seed control. |

---

## 11. Known Physical & Numerical Edge Cases

These are not future concerns. They are constraints that must be addressed in the version where they become relevant, and acknowledged in every version before that.

### 11.1 The Turnaround Energy Singularity

Version 1 uses instantaneous acceleration. This implies infinite force and infinite energy at $t_0$, $t_{turn}$, and $t_f$. This is acceptable **only** as a mathematical idealization for prototyping the solver — the same way a physics textbook uses "massless ropes" and "frictionless surfaces."

But MARTE's ambition is flight-grade software. The transition to constant proper acceleration (Phase 3) is not an enhancement — it is a **correction**. The v1 trajectory model must be clearly marked as an idealization in all outputs, and the system must never present an infinite-energy trajectory as a real mission plan.

### 11.2 Earth's Orbital Velocity

Earth orbits the Sun at $\sim 30$ km/s ($\beta \approx 10^{-4}$). At first glance this is negligible compared to a ship at $0.6c$. It is not negligible in a flight-grade system.

The rendezvous condition $\mathbf{r}_{ship}(t_f) = \mathbf{r}_{Earth}(t_f)$ is a position constraint. But a real docking or flyby also requires **velocity matching** — or at minimum, computing the relative velocity at arrival. This requires relativistic velocity addition:

$$\mathbf{v}_{rel} = \frac{\mathbf{v}_{ship} - \mathbf{v}_{Earth}}{1 - \mathbf{v}_{ship} \cdot \mathbf{v}_{Earth} / c^2}$$

(generalized to 3D via the Wigner rotation formalism in later versions)

Even in Phase 1, Earth's velocity must be tracked. In Phase 3+, it becomes part of the arrival constraint.

### 11.3 Floating-Point Precision at Ultra-Relativistic $\beta$

At $\beta = 0.999$, we compute $\gamma = (1 - \beta^2)^{-1/2}$. The intermediate value $1 - \beta^2$ is $0.001999$. Fine for 64-bit floats.

At $\beta = 0.999999$, $1 - \beta^2 \approx 2 \times 10^{-6}$. Still fine.

At $\beta = 1 - 10^{-12}$, we are in **catastrophic cancellation** territory. The subtraction $1 - \beta^2$ loses nearly all significant digits. $\gamma^{-1} = \sqrt{1 - \beta^2}$ becomes numerically unreliable.

**Mitigations (must be implemented before ultra-relativistic regimes are supported):**

| Strategy | Description |
|----------|-------------|
| Rapidity parameterization | Work in $\phi = \text{arctanh}(\beta)$ instead of $\beta$. $\gamma = \cosh(\phi)$, $\beta\gamma = \sinh(\phi)$. No subtraction from 1. |
| Complementary $\beta$ | Store $\epsilon = 1 - \beta$ instead of $\beta$ when $\beta \to 1$. Then $1 - \beta^2 = \epsilon(2 - \epsilon) \approx 2\epsilon$. |
| `mpmath` / `Decimal` | Arbitrary-precision arithmetic for validation or for regimes where 64-bit is insufficient. |

The physics engine must detect when it enters a numerically dangerous regime and either switch parameterization or raise a precision warning. Silent precision loss is a bug.

---

## 12. Naming & Notation Conventions

| Symbol | Code Variable | Meaning |
|--------|---------------|---------|
| $t$ | `coord_time` | Coordinate time in SSBIF |
| $\tau$ | `proper_time` | Proper time along worldline |
| $\gamma$ | `lorentz_factor` | Lorentz factor |
| $v$ | `velocity` | 3-velocity (vector or magnitude from context) |
| $\beta$ | `beta` | $v/c$ |
| $\phi$ | `rapidity` | Rapidity: $\text{arctanh}(\beta)$ |
| $\mathbf{r}_E$ | `earth_pos` | Earth position vector |
| $\mathbf{r}_S$ | `ship_pos` | Ship position vector |
| $R$ | `orbit_radius` | Earth orbital radius (1 AU) |
| $\omega$ | `orbit_angular_vel` | Earth orbital angular velocity |

---

## 13. What "Done" Looks Like

MARTE is done when a user can:

1. Open the interface
2. Select a departure time
3. Select a future arrival time at Earth
4. Specify their desired experienced duration
5. Press compute
6. See the required velocity, energy cost, and trajectory
7. Watch the ship trace its worldline through spacetime
8. See the Minkowski diagram with proper time ticks
9. Verify that the ship meets Earth at the specified arrival time
10. Trust every number on the screen

And when someone asks "but we don't have a ship that can do this" — the answer is:

**We know. The software is ready. We're waiting for you.**
