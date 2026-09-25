# Experiment E03 — Blades: how many, what shape, what angle?

**Kit:** Wind turbine (Kit 5) · **Levels:** Explorer (counting spins), Engineer (voltage vs pitch), Inventor (power curve, optimisation)
**Energy chain:** moving air → blades (rotation) → generator → electricity

## Question
Which blade count, shape and pitch angle make the most electricity from the
same fan?

## Prediction
Rank these from most to least voltage: 2 standard · 3 standard · 4 standard ·
3 torque (wide) · 3 speed (narrow). ______________

## Build
Assembly guide 03. Set every blade to the **same pitch** using the tick marks
around each hub socket (0° = blade flat, facing the wind; ticks every 15°).
Lock each blade with its M3 × 8 screw. Put a piece of tape on one blade tip.

**Safety:** fan on its lowest setting, 1 m away, eye level above the rotor,
nobody within arm's reach of the blades while turning. Stop the rotor with
the fan off — never by hand.

## Experiment
1. Blade count: 2, 3, 4 standard blades at 20° pitch.
2. Pitch: 3 standard blades at 0°, 15°, 30°, 45°.
3. Shape: 3 torque vs 3 standard vs 3 speed blades at their best pitch.
4. Load: connect the LED or a 100 Ω resistor and measure again.

## Measure

| Set-up | rpm (tape passes in 10 s × 6) | Voltage, open circuit (V) | Voltage with 100 Ω (V) | Power = V²/100 (mW) |
|---|---|---|---|---|
| | | | | |

## Explain
A blade at 0° pitch is pushed straight back by the wind — no turning force.
As pitch increases the wind is deflected sideways and the rotor turns; too
much pitch and the blade "stalls". Wide blades catch more wind at low speed
(high torque, good starting), narrow blades have less drag (higher top speed).
More blades = more torque but more drag: the best number depends on the load.
The generator voltage follows rpm; the power you can actually take out depends
on both speed and force.

## Build it wrong on purpose
Set one blade at +30° and another at −30°. What happens? (They fight each
other.) Mount the hub facing backwards: does it still turn? Why?

## Challenge
Find the blade set and pitch that light the LED with the fan on its lowest
setting. If direct drive is not enough, sketch a gear-up nacelle using the
bearing mount, a 40T gear and a 10T pinion (phase-2 part).
