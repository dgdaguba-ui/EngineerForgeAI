# Print settings - CRW-005 Articulated Cow - Walking Cowa

Slicer-agnostic set-up sheet. Values are starting points from generic material data - tune on the real machine and record results in `research/print-log.csv`.

## Load

- Production file: `3mf/prototypes/CRW-005-articulated-cow.3mf` (parts named `T1..T4 ...`, colours embedded)
- If the slicer asks 'multi-part object?' answer **yes** (keep parts together).
- Assign extruders by part-name prefix: T1 -> tool 1, T2 -> tool 2, T3 -> tool 3, T4 -> tool 4.

## Tools

| Tool | Material | Colour | Nozzle C | Bed C | Role |
|---|---|---|---|---|---|
| tool_1 | PLA | Cow White | 200-220 | 50-65 | all structural members, joint posts/rings, eye highlights |
| tool_2 | PLA | Cow Black | 200-220 | 50-65 | patches, eye, nostril, hooves |
| tool_3 | PLA | Cow Pink | 200-220 | 50-65 | muzzle, inner ear, udder |
| tool_4 | TPU | Cow Black | 215-235 | 40-60 | flexible tail (TPU) |

## Process

- Layer height 0.2 mm (inlay depth 0.6 mm = exactly 3 layers - keep 0.2 mm or 0.15/0.3 multiples so colour boundaries fall on layer boundaries)
- Bed temperature: common window 50-60 C for PLA, TPU
- Walls 2 perimeters (0.9 mm), top/bottom 4 layers, infill 15 % (estimates assume this)
- Orientation: Lying on its (left) side, joints vertical. No supports. Break joints free gently after printing.
- Supports: none
- Prime/wipe: use the machine's standard tool-change prime; prime tower off unless ooze is seen (if enabled, set `prime_tower: true` in config/toolheads.json to cost it)
- Standby temperature on idle tools: ~40 C below print temp to limit ooze (verify)
- TPU: print slowly (<= 25 mm/s), retraction minimal, no fan limitation needed for pads

## Record after printing

Add a row to `research/print-log.csv`: actual time, filament, purge, tool changes, failures, weak points, assembly time, surface and colour quality.
