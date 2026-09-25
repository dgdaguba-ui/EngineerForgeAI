# Printing instructions

## 0. Print the tolerance test first

`STL/common/STEM_TOLERANCE_TEST.stl` — see
[assembly/00_tolerance_test.md](assembly/00_tolerance_test.md). It tells you
whether the default clearances (`tolerance = 0.2`, grid hole 3.4, hub bore
3.15, nut pocket 5.85 AF) suit your printer. Adjust `PARAMETERS/config.scad`,
rebuild, and every part follows.

## 1. Default slicer profile

| Setting | Value |
|---|---|
| Nozzle / layer | 0.4 mm / 0.2 mm (0.12–0.16 mm for printed shafts and 10T gears) |
| Perimeters | 3 (6 for gears, hubs, crank, coupler — or use the listed 100 % infill) |
| Top / bottom layers | 5 / 4 |
| Infill | per part, see [PARTS.md](PARTS.md) (gyroid or grid) |
| Supports | **none** — every part is designed to print without them |
| Brim | only for the 100 mm-tall tower segment and the 48 mm pillars (5 mm) |
| Elephant-foot compensation | 0.15 mm if your slicer has it (bottom edges are already chamfered 0.6 mm) |
| Material | PLA for plates, rails, frames, wheels, blades; **PETG** for parts that flex or carry torque: motor mounts (snap walls), coupler, crank, printed shafts, pinions |

## 2. Orientation

Every STL is exported in its print orientation (flat face on z = 0), so just
drop it on the bed. Notes:

* **dynamo_gear_guard** — exported lying on one lip face, so the U-shaped
  cross-section (105 × 109 mm) is on the bed and it is extruded 65 mm up; all
  lattice openings are self-supporting diamonds.
* **turbine_tower_segment** — the top flange is a 29 mm bridge between the side
  walls. Enable "bridge" settings (fan 100 %, slower bridge speed).

## 3. Why no supports are needed

* horizontal holes are **teardrops** (45° roof), big pockets are **truncated
  teardrops** (bearing mount, turbine hub sockets);
* nut-pocket ceilings, pillar nut slots and frame windows are short **bridges**
  (≤ 6 mm, except the tower top flange);
* solar-frame lips, pulley flanks and wheel tyre grooves are **45°**;
* the crank knob, blade roots and panel-frame bosses have flat printing faces.

`tools/qc.py` measures the remaining downward-facing area of every part
(PARTS.md, "Printability measurements").

## 4. After printing

1. Press M3 nuts into hub slots and thumb nuts (a vice or a light tap).
2. Run a 3 mm drill (by hand) through any bushing that binds — not needed if
   the tolerance test passed.
3. Deburr cut steel rods; a file flat where a set screw bears greatly increases
   holding torque (the crank shaft especially).
4. Check that the motor snaps into the motor mount; if the walls are too stiff
   (PLA), print in PETG or set `tolerance = 0.25`.

## 5. Print time and material

Masses are estimated per part in PARTS.md: ≈ 0.6 kg of filament for one of
every part, ≈ 1.1 kg for all six MVP builds assembled at once. A 100 × 100
base plate takes roughly 1.5–2 h at 0.2 mm; one of every part is on the order
of 50 printer-hours on a typical 60 mm/s printer (slicer estimates will vary).
