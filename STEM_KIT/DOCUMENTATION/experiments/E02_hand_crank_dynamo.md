# Experiment E02 — How fast must a generator spin to light an LED?

**Kit:** Hand-crank dynamo (Kit 2) · **Levels:** Explorer (LED/buzzer), Engineer (ratios, voltage), Inventor (power, efficiency)
**Energy chain:** hand → crank → gearbox → generator (a motor running backwards) → LED / buzzer / capacitor

## Question
Does the gear ratio change how bright the LED gets, even if you turn the
crank at the same speed?

## Prediction
At 1 crank turn per second, which ratios will light the red LED?
☐ 1:1 ☐ 2:1 ☐ 4:1 ☐ 8:1

## Build
Build the gearbox (assembly guide 02). The generator mount moves to a
different grid hole for each ratio — that is how you "change gear":

| Ratio | Crank shaft gear | Generator position (x, z) | Gear train |
|---|---|---|---|
| 1:1 | 10T, level B | (45, 35) | 10T → 10T |
| 2:1 | 20T, level B | (45, 25) | 20T → 10T |
| 4:1 | 40T, level B | (75, 15) | 40T → 10T (the 3-4-5 diagonal!) |
| 8:1 | 20T, level A | (45, 25) | 20T→10T, 20T→10T, 20T→10T on two extra shafts |

Connect the generator wires to the output panel: LED (long leg +), then try
the buzzer, then the capacitor. **Always fit the guard before cranking.**

## Experiment
Use a metronome app (60 bpm = 1 turn per second). Crank for 10 s at each ratio.
Then keep the ratio at 8:1 and change the crank radius (knob at 20 mm vs 30 mm).

## Measure

| Ratio | Generator rpm (= 60 × ratio at 1 turn/s) | Voltage, no load (V) | LED? (off/dim/bright) | Buzzer? | How hard to turn (1–5) |
|---|---|---|---|---|---|
| 1:1 | 60 | | | | |
| 2:1 | 120 | | | | |
| 4:1 | 240 | | | | |
| 8:1 | 480 | | | | |

Inventor: charge the capacitor for 20 s at each ratio, then time how long it
keeps the LED lit. Compare the energy ½CV² with the work you put in.

## Explain
A generator's voltage is proportional to its speed (V = k × rpm). The
recommended 12 V-rated motor makes roughly 2–3 mV per rpm, so it needs about
700–900 rpm for the 1.8 V a red LED needs — only the higher ratios (and a
fast hand) get there. The gearbox trades **force for speed**: at 8:1 the
generator spins 8× faster but you must push 8× harder (plus friction), which
is why it feels heavier as soon as the LED is connected: electrical power
taken out = mechanical power you put in. A longer crank (30 mm) makes the same
torque with less hand force — leverage.

## Build it wrong on purpose
* Put the generator on a hole 10 mm off the correct position. Why can't the
  gears mesh at all? (Centre distance must equal the sum of the pitch radii.)
* Use a 3 V toy motor as the generator. Measure the voltage at 8:1. Why is it
  about ten times lower?
* Take the guard off, look (don't touch) at the 8:1 train turning slowly: which
  shafts turn the same way as the crank?

## Challenge
Design a train that lights the LED at **half a crank turn per second**. You
may use up to two 40T gears and any number of 10T/20T. Check with the grid
rule: every pair of meshing shafts must be (z1 + z2) mm apart.
