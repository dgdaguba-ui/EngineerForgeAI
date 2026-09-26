# Physical prototype test protocol (brief section 30)

Print each prototype **once as a single unit and once at the recommended batch size**. For every print add a row to
`print-log.csv`.

1. Slice the `3mf/prototypes/<stem>.3mf` file; record the slicer's own time/filament estimate.
2. Print; record actual time, filament used (weigh spool before/after or read the machine counter), purge (collect
   and weigh), number of tool changes (machine log or slicer), failures and failure mode.
3. Inspect: colour boundaries crisp? islands present? layer adhesion at colour interfaces? TPU pads retained?
   joints free? keyring loop strength (hang 5 kg for 1 min)?
4. Drop test: 1 m onto a hard floor x 3 (suitcase proxy). Record damage.
5. Rate surface and colour quality 1-5.
6. Run `python3 scripts/cost.py --calibrate` and apply the suggested calibration factors.

Specific questions per prototype:

| Product | Must answer |
|---|---|
| CRW-001 | Do 0.6 mm double-sided inlays look clean on the bed face? Horn tips chip? |
| CRW-002 | Magnet press-fit tight at 0.15 mm clearance? Banner lettering legible at 2 m? |
| CRW-003 | Real tool-change count and purge vs the 199 / 11.9 g estimate; chin keel acceptable? |
| CRW-004 | Pad slide-in force; pads stay put without a phone; stand slides on a desk? |
| CRW-005 | Joints free after break-in? Too loose to stand? Tail-body bond survives 50 flexes? |
