# Experiment E07 — Where should a solar panel point?

**Kit:** Solar panel frame + tilt brackets (Kit 1/4) · **Levels:** Explorer, Engineer, Inventor (sun tracking)

## Question
How much does the tilt angle of a panel change the power it makes?

## Prediction
Draw the graph you expect: voltage (up) against angle (0°…90°).

## Build
Tilting stand: two base plates joined by rails, two tilt brackets, the panel
frame on its pivots, thumb nuts to lock the angle. Read the angle from the
engraved ticks (every 15°).

## Experiment
Outdoors at midday (or with a lamp fixed above the table): measure the panel
current into a small load (the motor or a 22 Ω resistor) at every tick from
−90° to +90°.

## Measure

| Angle (°) | −90 | −60 | −45 | −30 | −15 | 0 | 15 | 30 | 45 | 60 | 90 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Voltage (V) | | | | | | | | | | | |
| Current (mA) | | | | | | | | | | | |

## Explain
A panel collects the most light when it faces the light square-on; the power
falls roughly with the cosine of the angle away from that direction. The
best tilt changes during the day and the year — that is why satellites and
solar farms rotate their panels.

## Challenge (Inventor)
Add two light sensors (LDRs) on either side of the panel frame and a servo
(phase 2 part) to make a one-axis sun tracker with an Arduino/ESP32.
