# CRW-002 - Cowa Head Magnet

*A - Multi-colour impulse - STANDARD - tier IMPULSE*

Dimensional bas-relief Cowa head (~64 mm) with sculpted eyes, lids, muzzle, horns and ears; curved scroll ribbon with raised COWARAMUP lettering; two 12x3 mm magnets in the back.

![four-colour](../../previews/CRW-002-cowaramup-magnet/2-four-colour.png)

## Manufacturing

- **Strategy:** E - printed + hardware (magnets)
- **Print orientation:** Face up, flat back on the bed (magnet pockets on the bed face).
- **Plate footprint:** 67.37 x 55.92 x 11.49 mm
- **Supports:** required
- **Hardware:** neodymium_disc_12x3, neodymium_disc_12x3
- **Recommended batch:** 12 per plate

## Toolhead utilisation (per unit, estimate)

| Tool | Material / colour | Used for | Grams |
|---|---|---|---|
| tool_1 | PLA Cow White | head, horns, eyelids, highlights, raised lettering | 4.30 |
| tool_2 | PLA Cow Black | patches, forelock, pupils, nostrils, smile | 1.45 |
| tool_3 | PLA Cow Pink | muzzle, inner ears | 1.67 |
| tool_4 | TPU Earth Brown | scroll ribbon, ear tag | 3.14 |

- Purge (single unit): **7.44 g** from **124** tool changes on 52/58 layers
- Total material (single unit incl. purge): **18.0 g**
- Estimated print time (single unit): **57.3 min** (extrusion 33.9, tool changes 16.5, layers 1.4, heat-up 5.0)

![tool layers](../../previews/CRW-002-cowaramup-magnet/tool-layers.png)

## Economics (NORMAL scenario, recommended batch) - estimate only

- Unit cost **$2.06**; suggested retail **$6-10** (price band / cost floor - not a demand forecast)

## Self-critique

- **character:** Same face as the collection; the ribbon now frames it instead of a label.
- **still to improve:** Pockets sit under the muzzle (thickest area); ceiling is measured from the geometry in checks.ceiling_above_pocket.

## Notes / known risks

- Bas-relief compression 45 %: reads as full 3D from the front 3/4, ~14 mm deep.
- Letters cap 5.8 mm, raised 0.7 mm on the ribbon (top layers only).

## Toolhead set-up issues

- [WARN] CRW-002 prefers rigid (PLA) in tool_4; TPU loaded - printable, but: ribbon should be rigid and crisp
- [WARN] colour Earth Brown is not commonly available in TPU

## Files

- `3mf/prototypes/CRW-002-cowaramup-magnet.3mf`
- `3mf/prototypes/variants/CRW-002-cowaramup-magnet--aussie.3mf`
- `3mf/prototypes/variants/CRW-002-cowaramup-magnet--christmas.3mf`
- `stl/prototypes/CRW-002-cowaramup-magnet.stl`
- `stl/prototypes/CRW-002-cowaramup-magnet/CRW-002-cowaramup-magnet.scad`
- STEP: not generated (see documentation/assumptions.md)

Previews: `previews/CRW-002-cowaramup-magnet/` (single-colour, four-colour, multi-material, dimensions, print orientation, variants)
