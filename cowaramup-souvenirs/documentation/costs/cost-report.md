# Cost & Batch Report

> **Manufacturing estimates only.** Mass/time come from a slicer-free geometry model (`cad/core/analysis.py`) with the assumptions in `config/*.json`. Retail ranges are the configured price bands raised to a cost floor; they are **not** a prediction of market demand.

## Toolhead utilisation (per unit, STANDARD sizes)

| Product | T1 | T2 | T3 | T4 | Purge (1 unit) | Total | Tool changes | Est. time |
|---|---|---|---|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | 6.3 g PLA | 3.2 g PLA | 0.9 g PLA | 0.0 g TPU | 19.08 g | 29.5 g | 318 | 78 min |
| CRW-002-cowaramup-magnet | 4.3 g PLA | 1.4 g PLA | 1.7 g PLA | 3.1 g TPU | 7.44 g | 18.0 g | 124 | 57 min |
| CRW-003-mini-cow-classic | 10.5 g PLA | 5.1 g PLA | 1.4 g PLA | - | 21.84 g | 38.8 g | 364 | 101 min |
| CRW-004-cow-phone-stand | 79.0 g PLA | 2.3 g PLA | 0.4 g PLA | 4.5 g TPU | 1.68 g | 87.9 g | 28 | 235 min |
| CRW-005-articulated-cow | 33.6 g PLA | 5.9 g PLA | 3.1 g PLA | 1.3 g TPU | 13.74 g | 57.8 g | 229 | 144 min |

## Batch plans

### CRW-001-cowaramup-keyring-classic

Max units on a 250x250 mm bed: **30** (spacing 6.0 mm). Recommended batch: **30**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 1.31 h | 78.5 min | 29.5 g | 19.08 g | 19.08 g | 64.7% |
| 4 | yes | 2.56 h | 38.4 min | 60.7 g | 19.08 g | 4.77 g | 31.4% |
| 8 | yes | 4.22 h | 31.7 min | 102.3 g | 19.08 g | 2.385 g | 18.7% |
| 16 | yes | 7.55 h | 28.3 min | 185.5 g | 19.08 g | 1.192 g | 10.3% |
| 30 | yes | 13.38 h | 26.8 min | 331.1 g | 19.08 g | 0.636 g | 5.8% |
| 32 | no | 14.22 h | 26.7 min | 351.9 g | 19.08 g | 0.596 g | 5.4% |

### CRW-002-cowaramup-magnet

Max units on a 250x250 mm bed: **12** (spacing 6.0 mm). Recommended batch: **12**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.95 h | 57.3 min | 18.0 g | 7.44 g | 7.44 g | 41.3% |
| 4 | yes | 2.67 h | 40.0 min | 49.7 g | 7.44 g | 1.86 g | 15.0% |
| 8 | yes | 4.96 h | 37.2 min | 91.9 g | 7.44 g | 0.93 g | 8.1% |
| 12 | yes | 7.24 h | 36.2 min | 134.2 g | 7.44 g | 0.62 g | 5.5% |
| 16 | no | 9.53 h | 35.7 min | 176.4 g | 7.44 g | 0.465 g | 4.2% |
| 32 | no | 18.67 h | 35.0 min | 345.4 g | 7.44 g | 0.233 g | 2.2% |

### CRW-003-mini-cow-classic

Max units on a 250x250 mm bed: **25** (spacing 6.0 mm). Recommended batch: **16**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 1.69 h | 101.2 min | 38.8 g | 21.84 g | 21.84 g | 56.3% |
| 4 | yes | 3.69 h | 55.3 min | 89.6 g | 21.84 g | 5.46 g | 24.4% |
| 8 | yes | 6.35 h | 47.6 min | 157.3 g | 21.84 g | 2.73 g | 13.9% |
| 16 | yes | 11.68 h | 43.8 min | 292.7 g | 21.84 g | 1.365 g | 7.5% |
| 25 | yes | 17.68 h | 42.4 min | 445.1 g | 21.84 g | 0.874 g | 4.9% |
| 32 | no | 22.35 h | 41.9 min | 563.6 g | 21.84 g | 0.682 g | 3.9% |

### CRW-003-mini-cow-classic-deluxe

Max units on a 250x250 mm bed: **15** (spacing 6.0 mm). Recommended batch: **8**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 2.64 h | 158.6 min | 64.0 g | 30.12 g | 30.12 g | 47.1% |
| 4 | yes | 6.55 h | 98.3 min | 165.6 g | 30.12 g | 7.53 g | 18.2% |
| 8 | yes | 11.76 h | 88.2 min | 301.0 g | 30.12 g | 3.765 g | 10.0% |
| 15 | yes | 20.88 h | 83.5 min | 538.0 g | 30.12 g | 2.008 g | 5.6% |
| 16 | no | 22.18 h | 83.2 min | 571.9 g | 30.12 g | 1.883 g | 5.3% |
| 32 | no | 43.02 h | 80.7 min | 1113.6 g | 30.12 g | 0.941 g | 2.7% |

### CRW-004-cow-phone-stand

Max units on a 250x250 mm bed: **3** (spacing 6.0 mm). Recommended batch: **3**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 3.92 h | 235.2 min | 87.9 g | 1.68 g | 1.68 g | 1.9% |
| 3 | yes | 11.2 h | 224.0 min | 260.3 g | 1.68 g | 0.56 g | 0.6% |
| 4 | no | 14.84 h | 222.6 min | 346.5 g | 1.68 g | 0.42 g | 0.5% |
| 8 | no | 29.41 h | 220.5 min | 691.3 g | 1.68 g | 0.21 g | 0.2% |
| 16 | no | 58.53 h | 219.5 min | 1380.9 g | 1.68 g | 0.105 g | 0.1% |
| 32 | no | 116.79 h | 219.0 min | 2760.1 g | 1.68 g | 0.052 g | 0.1% |

### CRW-005-articulated-cow

Max units on a 250x250 mm bed: **2** (spacing 6.0 mm). Recommended batch: **2**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 2.4 h | 143.9 min | 57.8 g | 13.74 g | 13.74 g | 23.8% |
| 2 | yes | 4.16 h | 124.9 min | 101.9 g | 13.74 g | 6.87 g | 13.5% |
| 4 | no | 7.69 h | 115.4 min | 190.1 g | 13.74 g | 3.435 g | 7.2% |
| 8 | no | 14.75 h | 110.6 min | 366.4 g | 13.74 g | 1.718 g | 3.8% |
| 16 | no | 28.86 h | 108.2 min | 719.0 g | 13.74 g | 0.859 g | 1.9% |
| 32 | no | 57.08 h | 107.0 min | 1424.3 g | 13.74 g | 0.429 g | 1.0% |

## Unit economics (AUD)

Batch = recommended batch size. Margin = gross margin at the middle of the suggested range, ex-GST.

| Product | Scenario | Batch | Material | Purge | Power | HW | Pack | Labour | Fail | **Cost** | Suggested retail | Margin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | LOW-COST | 30 | 0.25 | 0.01 | 0.04 | 0.28 | 0.15 | 0.00 | 0.01 | **0.74** | $5-10 | 89% |
| CRW-001-cowaramup-keyring-classic | NORMAL | 30 | 0.29 | 0.02 | 0.04 | 0.28 | 0.25 | 0.60 | 0.04 | **1.51** | $5-10 | 78% |
| CRW-001-cowaramup-keyring-classic | PREMIUM | 30 | 0.41 | 0.03 | 0.04 | 0.28 | 0.45 | 0.72 | 0.07 | **1.99** | $5-10 | 71% |
| CRW-002-cowaramup-magnet | LOW-COST | 12 | 0.30 | 0.02 | 0.05 | 0.60 | 0.15 | 0.00 | 0.02 | **1.13** | $5-10 | 83% |
| CRW-002-cowaramup-magnet | NORMAL | 12 | 0.35 | 0.02 | 0.05 | 0.60 | 0.25 | 0.75 | 0.04 | **2.06** | $6-10 | 72% |
| CRW-002-cowaramup-magnet | PREMIUM | 12 | 0.49 | 0.03 | 0.05 | 0.60 | 0.45 | 0.90 | 0.09 | **2.60** | $7-10 | 66% |
| CRW-003-mini-cow-classic | LOW-COST | 16 | 0.40 | 0.03 | 0.06 | 0.00 | 0.36 | 0.00 | 0.03 | **0.88** | $10-20 | 94% |
| CRW-003-mini-cow-classic | NORMAL | 16 | 0.47 | 0.04 | 0.06 | 0.00 | 0.60 | 0.69 | 0.06 | **1.92** | $10-20 | 86% |
| CRW-003-mini-cow-classic | PREMIUM | 16 | 0.66 | 0.05 | 0.06 | 0.00 | 1.08 | 0.82 | 0.12 | **2.80** | $10-20 | 80% |
| CRW-003-mini-cow-classic-deluxe | LOW-COST | 8 | 0.81 | 0.09 | 0.12 | 0.00 | 0.96 | 0.00 | 0.05 | **2.02** | $15-35 | 91% |
| CRW-003-mini-cow-classic-deluxe | NORMAL | 8 | 0.95 | 0.10 | 0.12 | 0.00 | 1.60 | 1.12 | 0.12 | **4.01** | $15-35 | 82% |
| CRW-003-mini-cow-classic-deluxe | PREMIUM | 8 | 1.33 | 0.15 | 0.12 | 0.00 | 2.88 | 1.35 | 0.24 | **6.06** | $16-35 | 74% |
| CRW-004-cow-phone-stand | LOW-COST | 3 | 2.12 | 0.02 | 0.30 | 0.00 | 0.36 | 0.00 | 0.12 | **2.91** | $10-20 | 79% |
| CRW-004-cow-phone-stand | NORMAL | 3 | 2.49 | 0.02 | 0.30 | 0.00 | 0.60 | 2.25 | 0.28 | **5.94** | $15-20 | 63% |
| CRW-004-cow-phone-stand | PREMIUM | 3 | 3.49 | 0.03 | 0.30 | 0.00 | 1.08 | 2.70 | 0.57 | **8.16** | $21-21 | 57% |
| CRW-005-articulated-cow | LOW-COST | 2 | 1.07 | 0.17 | 0.17 | 0.00 | 1.32 | 0.00 | 0.07 | **2.80** | $20-50 | 91% |
| CRW-005-articulated-cow | NORMAL | 2 | 1.26 | 0.20 | 0.17 | 0.00 | 2.20 | 3.00 | 0.16 | **6.99** | $20-50 | 78% |
| CRW-005-articulated-cow | PREMIUM | 2 | 1.76 | 0.28 | 0.17 | 0.00 | 3.96 | 3.60 | 0.33 | **10.10** | $26-50 | 71% |

## Single-unit vs batch (NORMAL scenario)

| Product | Cost @1 | Cost @batch | Purge/unit @1 | Purge/unit @batch |
|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | 5.07 | 1.51 | 19.08 g | 0.636 g |
| CRW-002-cowaramup-magnet | 5.07 | 2.06 | 7.44 g | 0.62 g |
| CRW-003-mini-cow-classic | 5.44 | 1.92 | 21.84 g | 1.365 g |
| CRW-003-mini-cow-classic-deluxe | 7.55 | 4.01 | 30.12 g | 3.765 g |
| CRW-004-cow-phone-stand | 7.99 | 5.94 | 1.68 g | 0.56 g |
| CRW-005-articulated-cow | 8.73 | 6.99 | 13.74 g | 6.87 g |
