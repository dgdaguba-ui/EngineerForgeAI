# Bill of materials — MVP (phase 1)

Printed-part quantities per build come from `tools/parts.py` (`KIT_QTY`); the
part list with sizes, masses and print settings is in [PARTS.md](PARTS.md).

## 1. Printed parts per build

| Build | Printed parts (qty) |
|---|---|
| **Solar vehicle** (Kit 4, version B) | chassis 1 · spoked wheel 4 · axle mount 4 · slotted motor mount 1 · 10T motor pinion 1 · 20T gear 1 · pillar 48 mm 4 · solar panel frame 1 (+ versions A/C/D: 10T gear 1 · 20T motor gear 1 · 2nd motor mount + pinion) |
| **Hand-crank dynamo** (Kit 2, all ratios) | base plate 1 · gearbox frame plate 2 · pillar 48 mm 4 · corner connector 2 · 10T gear 4 · 20T gear 3 · 40T gear 1 · hand crank 1 · crank knob 1 · generator mount 1 · motor coupler 1 · gear guard 1 · output panel 1 (+ 1 base plate to mount it) |
| **Wind turbine** (Kit 5) | base plate 1 · tower segment 2 · motor mount 1 · motor coupler 1 · hubs 2/3/4-blade 1 each · blades standard/torque/speed 4 each |
| **Pulley lab** (Kit 8 MVP) | base plate 1 · motor mount 1 · motor coupler 1 · bearing mount 1 · bushing insert 1 · axle mount 1 · belt pulley mount 2 · pulleys Ø20/Ø40/Ø60 1 each |
| **Four-bar linkage** (Kit 10 MVP) | base plate 1 · link bars 3-, 5-, 6-hole 1 each · crank knob 1 |
| **Tilting solar stand** | base plate 2 · rail 5 · 2 · solar panel frame 1 · tilt bracket 2 · thumb nut 2 |
| **Calibration** | STEM_TOLERANCE_TEST 1 (print first) |

Shared parts are printed once per classroom set, not per build: the same
base plate, motor mount, coupler, gears and knob move between kits.

## 2. Non-printed components

### Hardware pack (covers every MVP build at once)

| Item | Spec | Qty | Used for |
|---|---|---|---|
| Button-head screw | M3 × 10, ISO 7380, A2 stainless | 60 | the standard joint (4 mm foot + 6 mm plate) |
| Button-head screw | M3 × 12 | 20 | plate-to-plate, tower flanges, ground pivots |
| Button-head screw | M3 × 16 | 6 | linkage pivot, gear-to-gear coupling |
| Button-head screw | M3 × 40 | 2 | crank knob axles |
| Screw | M3 × 8 (self-tapping into printed Ø2.6) | 4 | turbine blade pitch locks |
| Grub (set) screw | M3 × 6, cup point | 30 | every hub (gears, wheels, pulleys, collars, coupler, crank ×2) |
| Hex nut | M3, DIN 934 | 80 | hex pockets, hub nut slots, pillar slots |
| Nylock nut | M3, DIN 985 | 6 | knobs and moving linkage pivots |
| Steel rod | Ø3 mm silver steel or stainless, 330 mm | 4 | cut to 40 / 60 / 80 / 120 mm shafts (deburr ends) |
| Hex key | 1.5 mm (grub) + 2 mm (button head) | 1 each | all fastening |

### Motors, bearings, rubber

| Item | Spec | Qty | Notes |
|---|---|---|---|
| DC motor (drive) | **130-size**, 1.5–6 V, Ø20 body with 15 mm flats, 2 mm shaft | 2 | Solar builds: pick a *low-current "solar motor"* in 130 size (start current < 100 mA). |
| DC motor (generator) | **130-size rated 12 V** (≈ 4 000–6 000 rpm at 12 V) | 1 | Same body, more windings → ~10× the voltage per rpm of a 3 V motor. A 3 V toy motor generates only ~0.25 V at 1 000 rpm — the LED will not light (a good experiment, a bad default). |
| Ball bearing | 625 (5 × 16 × 5) | 2 | optional; direct fit in the bearing mount (5 mm shafts) |
| Ball bearing | 623 (3 × 10 × 4) | 2 | optional; via the 623 adapter ring (3 mm shafts) |
| O-ring (tyre) | NBR 50 × 3 mm (ID × CS) | 4 | wheel V-groove tyres |
| O-ring (belt) | NBR, 2.5 mm cross-section, ID 70–80 mm (Ø20→Ø60 at the pulley lab spacing: belt centre-line 258 mm → O-ring ID ≈ 76 mm, i.e. ~4 % stretch) | 2 | round belts; or strong rubber bands |

### Electrical (all ≤ 12 V DC — no mains anywhere in the kit)

| Item | Spec | Qty |
|---|---|---|
| Solar panel | 110 × 69 × 3 mm epoxy panel, 5 V, ~1 W (frame is parametric for other sizes) | 1 |
| LED | 5 mm, red (lowest turn-on voltage ≈ 1.8 V) + green/white for comparison | 3 |
| Buzzer | Ø12 mm active buzzer, 3–5 V | 1 |
| Capacitor | 1 F 5.5 V super-capacitor **or** 2 200 µF 16 V electrolytic (observe polarity) | 1 |
| Meter | multimeter (DC V, DC mA) or a 0–30 V panel voltmeter module | 1 |
| Wire | 2 × crocodile-clip leads, 0.5 m hook-up wire, 2-way screw terminal block | set |
| Switch | slide switch (optional, solar car) | 1 |
| Rechargeable module | optional: 2 × AA NiMH holder + Schottky diode (1N5817), or a 5 V "USB solar charger" board | 1 |

### Consumables

Zip ties 100 × 2.5 mm (output panel, cable management) · masking tape and a
marker (rotation counting) · filament at the listed infill (from the measured
STL volumes): ≈ 0.6 kg for one of every part, ≈ 1.1 kg to have all six MVP
builds assembled at the same time (solar car 194 g, dynamo 303 g, wind 279 g,
pulley lab 119 g, linkage 57 g, tilting stand 144 g).
