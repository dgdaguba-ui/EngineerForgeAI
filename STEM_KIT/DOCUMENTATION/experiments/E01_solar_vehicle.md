# Experiment E01 — Which gearing makes the fastest solar car?

**Kit:** Solar vehicle (Kit 4) · **Levels:** Explorer (A/B), Engineer (all), Inventor (data + optimisation)
**Energy chain:** sunlight → solar panel (electrical) → motor (mechanical) → gears → wheels (motion)

## Question
The same panel and motor can drive the wheels through four different gear
set-ups. Which one gets the car across 2 metres fastest — and which one can
climb a ramp?

## Prediction
Tick one before you test: ☐ A (1:1) ☐ B (2:1 reduction) ☐ C (1:2 overdrive) ☐ D (two motors).
Why do you think so? ______________________

## Build
Build version B first (assembly guide 01). Then swap:

| Version | Motor position (chassis hole x) | Motor gear | Axle gear | Motor turns per wheel turn |
|---|---|---|---|---|
| A | 65 | 10T motor pinion | 10T | 1 |
| B | 75 | 10T motor pinion | 20T | 2 |
| C | 75 | 20T motor gear | 10T | 0.5 |
| D | 75 **and** 15 | 10T pinion on each | 20T | 2 (two motors) |

The motor must sit on the exact grid hole for each version — that is what
makes the gears mesh.

## Experiment
1. Mark a 2 m track in full sun (or under a 100 W-equivalent LED lamp held
   at a fixed height). Keep the light the same for every run.
2. Time 3 runs per version. Change **only** the gears.
3. Build a ramp (a book under a board). Find the steepest ramp each version
   can climb.

## Measure

| Version | Run 1 (s) | Run 2 (s) | Run 3 (s) | Average (s) | Speed = 2 m / avg (m/s) | Steepest ramp (books) |
|---|---|---|---|---|---|---|
| A | | | | | | |
| B | | | | | | |
| C | | | | | | |
| D | | | | | | |

Engineer/Inventor: also measure panel voltage and current (multimeter in
series) while the car is held still and while it runs.

## Explain
The panel can only deliver a limited **power** (≈ 1 W in full sun).
Power = speed × force. A **reduction** (B) turns the motor fast and the wheels
slowly with more force — good for starting and ramps. An **overdrive** (C)
asks the motor for more force than a weak panel can give; the car may not
start at all, or only on a flat floor. Version D splits the panel's current
between two motors: each gets less, so it is not automatically twice as good.
The best gear keeps the motor near the speed where it makes the most power.

## Build it wrong on purpose
Slide the motor in its slotted mount 4 mm **toward** the axle, then 4 mm
**away**. What happens to the noise, the speed and the gears? (Too close:
teeth jam, the motor stalls. Too far: teeth skip and click.) Why does the
grid position work best?

## Challenge
Design a version that climbs a 3-book ramp in weak light. You may use any
gears in the kit and the second motor. Draw your gear train, predict the
ratio, then test it.
