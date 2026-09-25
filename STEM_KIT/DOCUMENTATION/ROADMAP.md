# Roadmap, known limitations, suggested improvements

## Recommended next 20 components (phase 2)

Ordered by how many kits each one unlocks.

| # | Component | Kits unlocked | Notes |
|---|---|---|---|
| 1 | **Servo mount (SG90 / MG90S)** on the grid, horn-to-hub adapter | robot arm, sun tracker, satellite | parametric servo size; horn adapter bolts to the gear coupling holes |
| 2 | **Electronics mount** — Arduino Uno / Nano / ESP32 DevKit tray with adjustable slots | Inventor lessons, robotics | slot rows, no hard-coded boards |
| 3 | **Battery holder** 2 × AA / 18650 with switch pocket | vehicles, robot arm | low voltage only |
| 4 | **Worm + worm wheel** (m2, 20T wheel, CD 20 on grid) | gearbox lab, robot arm, satellite | self-locking demo |
| 5 | **Rack and pinion** (m2 rack with grid holes) | gearbox lab, linkage lab | linear motion |
| 6 | **Bevel gear pair** 1:1 and 2:1 (m2) with a 90° frame bracket | gearbox lab, hand drill demo | |
| 7 | **Planetary gear set** (sun 10T / planets 10T / ring 30T internal, carrier) | planetary lab | 4:1 on one axis, see-through carrier |
| 8 | **Gear-up nacelle** for the wind turbine (bearing mount + 40T/10T, yaw bearing, tail vane) | wind | fixes the low-rpm limitation below |
| 9 | **Hinged solar panel wing** + 2-axis experimental mount | satellite, solar | uses the frame's existing pivot bosses |
| 10 | **Satellite body** (120–180 mm, removable top, battery bay, sensor/antenna bosses) | Kit 1 | built from rails + frame plates |
| 11 | **Reaction-wheel module** (motor + heavy printed flywheel with nut ballast) | satellite | angular momentum demo |
| 12 | **Deployable boom** (spring-loaded linkage, rubber-band actuated) | satellite | |
| 13 | **Water turbine set** — Pelton, paddle, turbine wheels, nozzle holder, splash housing | Kit 6 | tap-flow only (< 0.5 bar) |
| 14 | **Robot arm joints** (base turntable, shoulder, elbow with servo + gear reduction) | Kit 9 | |
| 15 | **Grippers** (parallel rack gripper, scissor gripper) | Kit 9 | |
| 16 | **Crank-slider, Scotch yoke, cam & follower** plates on the linkage base | Kit 10 | |
| 17 | **Walking linkage** (Jansen / Klann on grid lengths) | Kit 10 | |
| 18 | **Dynamo vehicle** chassis extension (hand-crank on board, 2nd motor) | Kit 3 | |
| 19 | **Hall-sensor / IR slot sensor bracket** that reads the lattice or gear windows | all (rpm logging) | |
| 20 | **Spring-scale / force gauge** (printed compliant flexure with a scale) | all (force measurement) | |

## Known design limitations (MVP)

* **Generator voltage.** A 3 V toy motor makes only ~0.25 V per 1 000 rpm; the
  kit therefore specifies a 12 V-rated 130 motor as generator (~2.5 V per
  1 000 rpm). Even so, the red LED needs roughly 2 crank turns per second at
  8:1. A 16:1 train does not fit a single 100 × 100 frame with the current
  three gear levels (a second frame module is needed).
* **Wind turbine is direct drive.** Rotor rpm in a desk-fan wind is a few
  hundred, so the generator gives well under 2 V: enough for the meter,
  usually not for an LED. The gear-up nacelle (#8) is the fix.
* **Horizontal shafts at 17 mm over a flat plate** can only carry gears up to
  10T; larger gears need the gearbox frame, the chassis slot, the 37 mm high
  mounts or a plate edge (see STANDARD.md §8).
* **Bearing mounts** (22 mm wide) cannot sit side by side at 20 mm centre
  distance.
* **Set screws on round 3 mm rod** hold roughly 0.2–0.4 N·m. Enough for the
  kit's loads, but the crank should bear on a small filed flat (or use D-shaft
  rod and `shaft_flat = 0.5`).
* **Printed 3 mm shafts** are flexible and only suitable for light, low-speed
  use.
* **Snap-in motor cradle** relies on wall flex: PLA works but PETG is kinder
  to the walls over many insertions.
* **Tower top flange** bridges 29 mm; poor bridging printers may sag slightly
  (no functional impact on the nut pockets).
* **Solar vehicle version D** drives one common axle with two motors (a
  "two-motor" drive). A true split-axle, independently driven two-wheel drive
  needs an extra axle-support part.
* **Verification scope.** Geometry, fits, collisions and gear engagement are
  checked virtually against nominal dimensions. Friction, stiffness, real
  printer tolerances and electrical performance are *not* simulated — they are
  what the tolerance test and the experiments are for. None of the parts has
  been physically printed yet in this phase.
* Hardware (screws, nuts, grub screws) is not modelled in the collision check,
  except the generator-mount nuts inside the gearbox and the linkage pivot
  nuts.

## Suggested improvements

1. **Snap pegs** (printed push-pins on the 10 mm grid) for tool-free
   prototyping by the youngest children; keep M3 for durable builds.
2. **Colour code** by function (gears orange, mounts blue, structure grey) —
   consistent with the renders — and engrave part IDs on every part.
3. **Printed hex-shaft option** (5 mm AF) for high-torque, set-screw-free
   drives in the Explorer level.
4. **Second gearbox frame depth** (frame_gap = 58 mm, four gear levels) to
   allow 16:1 and 32:1 generator trains.
5. **Low-friction bushings**: offer the 623 bearing adapter as the default for
   the solar car axles (friction dominates at solar power levels).
6. Add **thumb-screw heads** (printed knobs pressed onto M3 button heads) so
   the M3 × 10 joint needs no key at all.
7. **CI**: run `tools/build.py`, `tools/qc.py` and `tools/verify_all.py` in
   GitHub Actions on every change to `STEM_KIT/`, and publish the STL
   artifacts.
8. **3MF export** with per-part print settings embedded (orientation,
   infill), and a plate-packing script for classroom batches.
9. **Physical test programme**: print the MVP set in PLA and PETG, measure the
   real clearances, torques and generator voltages, and feed them back into
   `config.scad` defaults.
10. **Accessibility**: large-format instruction cards with pictograms and QR
    codes linking to the renders.
