# Experiment E06 — Counting teeth: gear ratio, direction and idlers

**Kit:** Gearbox lab (Kit 7, uses the gearbox frame) · **Levels:** Explorer, Engineer

## Question
If a 10-tooth gear drives a 40-tooth gear, how many turns does the small one
make for one turn of the big one? What does an extra gear in the middle do?

## Prediction
10T → 40T: ____ turns. 10T → 20T (idler) → 40T: ____ turns, direction ____.

## Build
Gearbox frame (two lattice plates + four 48 mm pillars). Put shafts through
grid holes; remember the rule: **shafts (z1 + z2) mm apart**.

| Pair | Centre distance | Example holes (x, z) |
|---|---|---|
| 10T–10T | 20 mm | (45,55) & (65,55) |
| 10T–20T | 30 mm | (45,55) & (75,55) |
| 20T–20T | 40 mm | (25,55) & (65,55) |
| 10T–40T | 50 mm | (45,55) & (75,15) (diagonal 30 × 40) |

Every gear has a small triangle marker on one tooth: count turns with it.

## Experiment
1. 10T drives 40T. Turn the 40T once, count the 10T.
2. Add a free-spinning 20T idler between two 10T gears. Compare direction.
3. Build a compound: 10T → 20T, with a 10T fixed on the same shaft as the 20T,
   driving another 20T. Predict, then count.

## Measure

| Train | Input turns | Output turns | Ratio | Same or opposite direction |
|---|---|---|---|---|
| 10T → 40T | | | | |
| 10T → 20T idler → 10T | | | | |
| 10T → 20T = 10T → 20T | | | | |

## Explain
Teeth pass one-for-one, so turns × teeth is the same on both gears: ratio =
teeth(driven) / teeth(driver). An idler changes direction but not the ratio.
In a compound train the ratios multiply (2 × 2 = 4).

## Build it wrong on purpose
Put the 10T and 40T on holes 40 mm apart. Why can't they mesh? Put them 60 mm
apart — what happens now?

## Challenge
Make an output that turns 16× slower than the input, in the same direction,
inside one 100 × 100 frame.
