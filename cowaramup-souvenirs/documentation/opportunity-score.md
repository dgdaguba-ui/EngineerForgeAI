# Manufacturing opportunity score (INTERNAL)

> For internal product-development prioritisation ONLY. It ranks how easy/robust/distinctive a design is to manufacture with this printer. It does **not** predict sales or demand.

Score 0-100 = weighted sub-scores (0-5): print_time 15%, material_cost 10%, purge 15%, assembly 10%, durability 15%, visual_appeal 15%, differentiation 15%, packaging_ease 5%.
Measured sub-scores (print time, material cost, purge fraction, assembly) are relative across the prototype set at recommended batch size; durability / visual appeal / differentiation / packaging ease are design-team ratings in `scripts/reports.py` to be revised after physical tests.

| Rank | Product | Score | Time/unit | Purge/unit vs part | print_time | material_cost | purge | assembly | durability | visual_appeal | differentiation | packaging_ease |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CRW-002-cowaramup-magnet | **93.9** | 26.1 min | 1.0% | 4.8 | 4.7 | 4.5 | 4.8 | 5 | 5 | 4 | 5 |
| 2 | CRW-001-cowaramup-keyring-classic | **90.7** | 15.7 min | 1.4% | 5.0 | 5.0 | 3.9 | 5.0 | 5 | 4 | 4 | 5 |
| 3 | CRW-003-mini-cow-classic | **74.4** | 29.5 min | 4.1% | 4.7 | 4.7 | 0.0 | 4.5 | 4 | 4 | 5 | 3 |
| 4 | CRW-005-articulated-cow | **57.4** | 94.3 min | 3.5% | 3.1 | 3.1 | 0.9 | 0.0 | 3 | 4 | 5 | 3 |
| 5 | CRW-004-cow-phone-stand | **56.3** | 224.0 min | 0.6% | 0.0 | 0.0 | 5.0 | 1.1 | 5 | 3 | 4 | 3 |
