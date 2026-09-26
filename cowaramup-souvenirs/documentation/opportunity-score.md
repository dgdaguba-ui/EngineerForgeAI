# Manufacturing opportunity score (INTERNAL)

> For internal product-development prioritisation ONLY. It ranks how easy/robust/distinctive a design is to manufacture with this printer. It does **not** predict sales or demand.

Score 0-100 = weighted sub-scores (0-5): print_time 15%, material_cost 10%, purge 15%, assembly 10%, durability 15%, visual_appeal 15%, differentiation 15%, packaging_ease 5%.
Measured sub-scores (print time, material cost, purge fraction, assembly) are relative across the prototype set at recommended batch size; durability / visual appeal / differentiation / packaging ease are design-team ratings in `scripts/reports.py` to be revised after physical tests.

| Rank | Product | Score | Time/unit | Purge/unit vs part | print_time | material_cost | purge | assembly | durability | visual_appeal | differentiation | packaging_ease |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CRW-002-cowaramup-magnet | **90.8** | 36.2 min | 5.9% | 4.8 | 4.9 | 3.3 | 5.0 | 5 | 5 | 4 | 5 |
| 2 | CRW-001-cowaramup-keyring-classic | **88.5** | 26.8 min | 6.1% | 5.0 | 5.0 | 3.2 | 5.0 | 5 | 4 | 4 | 5 |
| 3 | CRW-003-mini-cow-classic | **82.4** | 43.8 min | 8.1% | 4.6 | 4.6 | 2.5 | 5.0 | 4 | 4 | 5 | 3 |
| 4 | CRW-004-cow-phone-stand | **56.5** | 224.0 min | 0.6% | 0.0 | 0.0 | 5.0 | 1.2 | 5 | 3 | 4 | 3 |
| 5 | CRW-005-articulated-cow | **52.1** | 124.9 min | 15.6% | 2.5 | 2.8 | 0.0 | 0.0 | 3 | 4 | 5 | 3 |
