# Level 3 — Inventor (ages ≈ 12–14)

Goal: quantitative modelling, efficiency, optimisation, sensors and control
with Arduino / ESP32. Students design their own experiments and parts.

---

## Lesson 3.1 — Power and efficiency (90 min)
* Mechanical power P = τ·ω; electrical power P = V·I.
* Hand dynamo: estimate input power (force on the knob × knob speed) and
  output power (V²/R into a 47 Ω resistor). Efficiency = out ÷ in. Where did
  the rest go?
* Compare ratios 2:1 (one stage) and 8:1 (three stages): each stage adds
  friction. Does efficiency drop per stage?

## Lesson 3.2 — Motor curves and optimal gearing (90 min)
* A DC motor's torque falls linearly with speed; power peaks at half the
  no-load speed.
* Solar car: measure panel V and I at stall and while running for versions
  A–D. Plot the panel's I–V curve with a variable resistor (10–200 Ω) and find
  the maximum power point. Which gear ratio keeps the motor nearest to it?

## Lesson 3.3 — Measuring rpm with a microcontroller (90 min)
* Tape a small magnet on a gear and use a Hall sensor, or an IR slot sensor
  across the lattice openings of the frame plate (the lattice is a free
  encoder disc for gears with windows!).
* Arduino/ESP32 sketch: count pulses in 1 s → rpm; log generator voltage on an
  analog pin through a 2:1 divider (never exceed 3.3 V on ESP32 pins).
* Plot rpm vs voltage live; compare k with Lesson 2.4.

## Lesson 3.4 — Control: a sun-tracking panel (2 × 90 min)
* Two LDRs on the panel frame, one each side of a divider fin.
* Hobby servo drives the tilt axis (phase-2 servo bracket; meanwhile a 130
  motor + 40T/10T through the grid works as a slow actuator).
* Proportional control: error = LDR_left − LDR_right; move until error ≈ 0.
* Measure energy collected over an hour: fixed vs tracking.

## Lesson 3.5 — Linkage synthesis (90 min)
* Grashof, transmission angle, coupler curves (Experiment E05).
* Use a spreadsheet or Python to simulate a four-bar (the kit's own
  `tools/linkage_check.py` is a readable example) and find link lengths on the
  10 mm grid that trace a walking-foot curve.

## Lesson 3.6 — Design your own part (2 × 90 min)
* Open `PARAMETERS/config.scad` and one part file in OpenSCAD.
* Change a parameter (e.g. `wheel_diameter = 80`), rebuild, print, test.
* Design a new part that follows the ForgeGrid standard (holes on the 10 mm
  grid, 4 mm feet, axis at 17 mm) and prove it fits with
  `tools/check_assembly.py`.

## Inventor badge challenge
Optimise one kit for one number (fastest solar car, highest generator voltage
at 1 turn/s, most wind power at the lowest fan setting). Show your model, your
data, your iterations, and the final improvement in %.
