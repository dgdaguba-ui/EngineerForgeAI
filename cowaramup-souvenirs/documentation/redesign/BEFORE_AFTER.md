# Commercial design overhaul: before / after

Audit: `DESIGN_AUDIT.md`. Originals: `stl/archive/before-redesign/`, `3mf/archive/before-redesign/`,
`cad/archive/before-redesign/`, `previews/archive/before-redesign/`.
Comparison images: `previews/<product>/before-after.png`. Product photos: `previews/<product>/photo-3q.png`.
Four views: `previews/<product>/views.png`.

![after - collection](../../previews/collection-overview.png)

All numbers are estimates from the geometry model (single unit unless stated), NORMAL cost scenario,
recommended batch. They are manufacturing estimates, not demand predictions.

---

## 0. Mascot: "Cowa" v2 (`cad/cows/character.py`)

**What changed:** a new sculpted character built with a signed-distance-field engine (`cad/core/sdf.py`),
replacing ellipsoid assemblies and flat drawings.

| Element | Before | After |
|---|---|---|
| Proportion | small head on a big body | designer-toy proportion: the head is ~40 % of height, chunky body, short legs |
| Pose | symmetric, static | sitting, head turned 16 deg toward the 3/4 camera, 7 deg roll, 13 deg chin lift |
| Eyes | flat black ovals | recessed sockets, domed glossy pupils, a highlight, a relaxed upper lid |
| Muzzle | flat pink oval | a volume with deep nostril recesses and an engraved, slightly lopsided smile |
| Ears | symmetric leaves | one perky, one relaxed; dished pink inner ear |
| Horns | capsules | thick, curved, tapered tubes |
| Hair | none | black forelock tuft between the horns |
| Markings | flat blobs | raised 0.4 mm (tactile), organic edges; the signature patch covers the right eye and ear |
| Legs/hooves | pill capsules | shaped legs, black hooves with a moulded split |
| Tail | capsule chain | tail curling round on the ground with a three-lobe tuft |
| Chin | 45-degree keel "beak" | a dewlap (the real fold under a cow's throat) that carries the chin overhang |
| Story | none | collar, bell and ear tag in the tool-4 story colour |

**Why:** the audit found that no product had personality or any detail to discover when picked up.

**Added complexity:** true 3D colour means colour changes on most layers (see economics below). Modelling time
goes from seconds to about 100 s per product (cached).

---

## 1. CRW-003 Mini collectible: Standard + Deluxe (No. 01 Classic)

| | Before | After: Standard | After: Deluxe |
|---|---|---|---|
| Size | 54 x 34 x 29 mm (lying) | 41 x 43 x 61 mm (sitting) | 77 x 43 x 68 mm on base |
| Colours | 4 | 3 (T1 body, T2 markings, T3 muzzle/ears) | 4 (+ T4 paddock, collar, bell, tag) |
| Base | plain oval | none; stands on its own | Cowaramup Paddock: grass tufts, fence, COWARAMUP inlaid, COW TOWN WA on the back, "01 CLASSIC / COWARAMUP WA / CRW-003" underneath |
| Material | 12.1 g | 16.9 g | 33.9 g |
| Tool changes (1 unit) | 199 | 364 | 502 |
| Purge (1 unit / at batch) | 11.9 g / 0.50 g | 21.8 g / 1.37 g (x16) | 30.1 g / 3.77 g (x8) |
| Time per unit at batch | - (not recorded) | 44 min | 88 min |
| Unit cost | $1.66 | $1.92 | $4.01 |
| Suggested retail band | $10-20 | $10-20 | $15-35 |

## 2. CRW-001 Keyring

| | Before | After |
|---|---|---|
| Form | flat 4.2 mm face cut-out | miniature 3D sitting Cowa, 32 x 40 x 48 mm |
| Key loop | separate tab | the **tail curls into the loop** (5.2 mm hole, 3.9 mm solid ring, fused into the rump) |
| Durability | flat, robust | horns x0.78 length / x1.25 thickness; no part under 2.3 mm except the tag |
| Branding | none | COWARAMUP / WA debossed under the base (hidden detail) |
| Material / purge / changes | 6.4 g / 1.1 g / 18 | 10.4 g / 19.1 g / 318 |
| Batch | 12 (flat, 59 mm) | 30 per plate: 13.4 h plate, 0.64 g purge per unit |
| Unit cost | $1.41 | $1.51 |

## 3. CRW-002 Magnet

| | Before | After |
|---|---|---|
| Form | flat face + rectangle banner, 6 mm | **bas-relief bust** (depth compressed to 45 %), 67 x 56 x 11.5 mm |
| Branding | text knocked out of a rectangle | curved scroll ribbon with **raised arc lettering** |
| Magnets | 2 pockets, assumed ceiling | 2 pockets under the thick muzzle; **measured** ceiling 2.7 mm |
| Material / purge / changes | 11.3 g / 0.9 g / 15 | 10.6 g / 7.4 g / 124 |
| Batch | 9 | 12 per plate: 0.62 g purge per unit |
| Unit cost | $2.00 | $2.06 |

## 4. CRW-005 Articulated cow

| | Before | After |
|---|---|---|
| Members | square-edged 18 mm slabs | pillow-rounded members: 3.2 mm top fillet, 45-degree bed chamfer |
| Face | flat sticker | sculpted muzzle dome, recessed eye with domed pupil, lid, highlight, nostril |
| Head | 30 mm | 34 mm (bigger, more character) |
| Markings | flat skins | raised patches (never wider than the outline, so joint clearance is kept) |
| Hooves | skin only | black wraps all round |
| Joints | validated bicone | unchanged geometry; clearance re-imposed exactly after sculpting (0.353 mm normal gap, ROM sweep clear) |
| Hidden detail | none | COWARAMUP CRW-005 debossed on the bed-side flank |
| Material / purge / changes | 38.7 g / 2.5 g / 42 | 43.7 g / 13.7 g / 229 |
| Unit cost | $6.53 | $6.99 |

## 5. CRW-004 Phone stand: NOT redesigned this session

This product is next in line. Plan: a sculpted resting Cowa whose back cradles the phone, with a TPU saddle
liner, TPU feet, and a branded Paddock-style base.

---

## Design scorecard (internal, /10)

Scored honestly against "would I put this on a tourist-shop shelf?". Before -> after.

| | Character | Tourist appeal | Cowaramup identity | Visual quality | 4-tool use | Printability | Durability | Collectibility |
|---|---|---|---|---|---|---|---|---|
| CRW-003 Deluxe | 3 -> 8 | 4 -> 8 | 3 -> 8 | 3 -> 8 | 7 -> 9 | 8 -> 6 | 8 -> 7 | 3 -> 8 |
| CRW-003 Standard | 3 -> 8 | 4 -> 7 | 3 -> 4 | 3 -> 8 | 7 -> 7 | 8 -> 7 | 8 -> 7 | 3 -> 6 |
| CRW-001 Keyring | 5 -> 8 | 5 -> 8 | 1 -> 5 | 5 -> 8 | 8 -> 7 | 9 -> 7 | 9 -> 7 | 3 -> 7 |
| CRW-002 Magnet | 5 -> 8 | 6 -> 8 | 7 -> 9 | 5 -> 8 | 8 -> 8 | 9 -> 7 | 9 -> 8 | 3 -> 6 |
| CRW-005 Articulated | 4 -> 6 | 5 -> 6 | 1 -> 3 | 3 -> 6 | 8 -> 8 | 8 -> 7 | 7 -> 7 | 5 -> 6 |
| CRW-004 Phone stand | 3 (unchanged) | 4 | 5 | 3 | 8 | 9 | 9 | 3 |

### Still needs improvement (not "good enough" yet)

- **Articulated cow:** still reads as a flexi toy. It needs separate left/right legs, a proper wagging-tail joint
  and branding on the product (ear tag). It is the weakest of the redesigned four.
- **Printability of the sculpted pieces:**
  - Ear rims keep 40-60 mm^2 of support-required overhang (> 60 deg, > 2 mm drop). The Deluxe adds its fence rails, which bridge between posts.
  - Target: ear undersides shaped at 45 deg.
- **Mesh export:** 5-34 isolated pinch edges per sculpted product, where three colour regions meet tangentially (eye rims,
  fence feet). The indexed 3MF is exact. STL readers weld these, and slicers auto-repair them on import; they should
  still be driven to 0.
- **Economics:** real 3D colour costs 124-502 tool changes per plate. Batch printing is mandatory, and the Deluxe
  collectible's purge (3.8 g per unit at a batch of 8) is the highest.
  - The per-change purge on the real machine decides whether the Deluxe is viable at $15-35.
  - A lever to keep in reserve is fewer colour regions: the Standard edition drops 138 changes.
- **Standard mini identity:** it has no visible branding. Candidates are a small collar tag or the underside deboss.
