# Cost & Batch Report

> **Manufacturing estimates only.** Mass/time come from a slicer-free geometry model (`cad/core/analysis.py`) with the assumptions in `config/*.json`. Retail ranges are the configured price bands raised to a cost floor; they are **not** a prediction of market demand.

## Toolhead utilisation (per unit, STANDARD sizes)

| Product | T1 | T2 | T3 | T4 | Purge (1 unit) | Total | Tool changes | Est. time |
|---|---|---|---|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | 5.0 g PLA | 0.5 g PLA | 0.8 g PLA | 0.2 g TPU | 1.08 g | 7.5 g | 18 | 23 min |
| CRW-002-cowaramup-magnet | 8.4 g PLA | 0.4 g PLA | 1.0 g PLA | 0.6 g TPU | 0.90 g | 11.3 g | 15 | 33 min |
| CRW-003-mini-cow-classic | 5.8 g PLA | 1.0 g PLA | 0.6 g PLA | 4.7 g PLA | 11.94 g | 24.0 g | 199 | 63 min |
| CRW-004-cow-phone-stand | 79.0 g PLA | 2.3 g PLA | 0.4 g PLA | 4.5 g TPU | 1.68 g | 87.9 g | 28 | 235 min |
| CRW-005-articulated-cow | 33.0 g PLA | 1.3 g PLA | 0.5 g PLA | 1.3 g TPU | 2.52 g | 38.7 g | 42 | 101 min |

## Batch plans

### CRW-001-cowaramup-keyring-classic

Max units on a 250x250 mm bed: **12** (spacing 6.0 mm). Recommended batch: **12**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.38 h | 23.0 min | 7.5 g | 1.08 g | 1.08 g | 14.4% |
| 4 | yes | 1.14 h | 17.0 min | 26.7 g | 1.08 g | 0.27 g | 4.0% |
| 8 | yes | 2.14 h | 16.1 min | 52.3 g | 1.08 g | 0.135 g | 2.1% |
| 12 | yes | 3.15 h | 15.7 min | 77.9 g | 1.08 g | 0.09 g | 1.4% |
| 16 | no | 4.15 h | 15.6 min | 103.5 g | 1.08 g | 0.068 g | 1.0% |
| 32 | no | 8.17 h | 15.3 min | 205.9 g | 1.08 g | 0.034 g | 0.5% |

### CRW-001-cowaramup-keyring-classic-small

Max units on a 250x250 mm bed: **20** (spacing 6.0 mm). Recommended batch: **20**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.3 h | 18.2 min | 5.4 g | 1.08 g | 1.08 g | 19.9% |
| 4 | yes | 0.82 h | 12.2 min | 18.5 g | 1.08 g | 0.27 g | 5.8% |
| 8 | yes | 1.5 h | 11.3 min | 35.9 g | 1.08 g | 0.135 g | 3.0% |
| 16 | yes | 2.87 h | 10.8 min | 70.7 g | 1.08 g | 0.068 g | 1.5% |
| 20 | yes | 3.55 h | 10.7 min | 88.1 g | 1.08 g | 0.054 g | 1.2% |
| 32 | no | 5.6 h | 10.5 min | 140.3 g | 1.08 g | 0.034 g | 0.8% |

### CRW-001-cowaramup-keyring-classic-large

Max units on a 250x250 mm bed: **9** (spacing 6.0 mm). Recommended batch: **9**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.51 h | 30.4 min | 10.6 g | 1.08 g | 1.08 g | 10.2% |
| 4 | yes | 1.63 h | 24.4 min | 39.3 g | 1.08 g | 0.27 g | 2.7% |
| 8 | yes | 3.13 h | 23.4 min | 77.5 g | 1.08 g | 0.135 g | 1.4% |
| 9 | yes | 3.5 h | 23.3 min | 87.0 g | 1.08 g | 0.12 g | 1.2% |
| 16 | no | 6.12 h | 22.9 min | 153.9 g | 1.08 g | 0.068 g | 0.7% |
| 32 | no | 12.11 h | 22.7 min | 306.7 g | 1.08 g | 0.034 g | 0.4% |

### CRW-002-cowaramup-magnet

Max units on a 250x250 mm bed: **9** (spacing 6.0 mm). Recommended batch: **9**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.55 h | 33.0 min | 11.3 g | 0.9 g | 0.9 g | 8.0% |
| 4 | yes | 1.81 h | 27.2 min | 42.4 g | 0.9 g | 0.225 g | 2.1% |
| 8 | yes | 3.5 h | 26.2 min | 83.9 g | 0.9 g | 0.113 g | 1.1% |
| 9 | yes | 3.92 h | 26.1 min | 94.3 g | 0.9 g | 0.1 g | 1.0% |
| 16 | no | 6.87 h | 25.8 min | 167.0 g | 0.9 g | 0.056 g | 0.5% |
| 32 | no | 13.61 h | 25.5 min | 333.1 g | 0.9 g | 0.028 g | 0.3% |

### CRW-002-cowaramup-magnet-small

Max units on a 250x250 mm bed: **16** (spacing 6.0 mm). Recommended batch: **16**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.41 h | 24.7 min | 7.8 g | 0.9 g | 0.9 g | 11.5% |
| 4 | yes | 1.26 h | 18.8 min | 28.7 g | 0.9 g | 0.225 g | 3.1% |
| 8 | yes | 2.38 h | 17.9 min | 56.4 g | 0.9 g | 0.113 g | 1.6% |
| 16 | yes | 4.64 h | 17.4 min | 111.9 g | 0.9 g | 0.056 g | 0.8% |
| 32 | no | 9.14 h | 17.1 min | 223.0 g | 0.9 g | 0.028 g | 0.4% |

### CRW-002-cowaramup-magnet-large

Max units on a 250x250 mm bed: **6** (spacing 6.0 mm). Recommended batch: **6**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 0.77 h | 45.9 min | 16.6 g | 0.9 g | 0.9 g | 5.4% |
| 4 | yes | 2.67 h | 40.1 min | 63.6 g | 0.9 g | 0.225 g | 1.4% |
| 6 | yes | 3.94 h | 39.4 min | 95.0 g | 0.9 g | 0.15 g | 0.9% |
| 8 | no | 5.22 h | 39.1 min | 126.3 g | 0.9 g | 0.113 g | 0.7% |
| 16 | no | 10.3 h | 38.6 min | 251.8 g | 0.9 g | 0.056 g | 0.4% |
| 32 | no | 20.47 h | 38.4 min | 502.7 g | 0.9 g | 0.028 g | 0.2% |

### CRW-003-mini-cow-classic

Max units on a 250x250 mm bed: **24** (spacing 6.0 mm). Recommended batch: **24**.

| Units | Fits | Batch time | Time/unit | Material/batch | Purge/batch | Purge/unit | Waste |
|---|---|---|---|---|---|---|---|
| 1 | yes | 1.05 h | 63.3 min | 24.0 g | 11.94 g | 11.94 g | 49.7% |
| 4 | yes | 2.46 h | 36.9 min | 60.3 g | 11.94 g | 2.985 g | 19.8% |
| 8 | yes | 4.33 h | 32.5 min | 108.7 g | 11.94 g | 1.492 g | 11.0% |
| 16 | yes | 8.07 h | 30.3 min | 205.4 g | 11.94 g | 0.746 g | 5.8% |
| 24 | yes | 11.81 h | 29.5 min | 302.1 g | 11.94 g | 0.497 g | 4.0% |
| 32 | no | 15.56 h | 29.2 min | 398.8 g | 11.94 g | 0.373 g | 3.0% |

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
| 1 | yes | 1.68 h | 100.7 min | 38.7 g | 2.52 g | 2.52 g | 6.5% |
| 2 | yes | 3.14 h | 94.3 min | 74.9 g | 2.52 g | 1.26 g | 3.4% |
| 4 | no | 6.07 h | 91.1 min | 147.3 g | 2.52 g | 0.63 g | 1.7% |
| 8 | no | 11.93 h | 89.5 min | 292.0 g | 2.52 g | 0.315 g | 0.9% |
| 16 | no | 23.64 h | 88.7 min | 581.6 g | 2.52 g | 0.158 g | 0.4% |
| 32 | no | 47.07 h | 88.3 min | 1160.6 g | 2.52 g | 0.079 g | 0.2% |

## Unit economics (AUD)

Batch = recommended batch size. Margin = gross margin at the middle of the suggested range, ex-GST.

| Product | Scenario | Batch | Material | Purge | Power | HW | Pack | Labour | Fail | **Cost** | Suggested retail | Margin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | LOW-COST | 12 | 0.15 | 0.00 | 0.02 | 0.28 | 0.15 | 0.00 | 0.01 | **0.62** | $5-10 | 91% |
| CRW-001-cowaramup-keyring-classic | NORMAL | 12 | 0.18 | 0.00 | 0.02 | 0.28 | 0.25 | 0.65 | 0.02 | **1.41** | $5-10 | 79% |
| CRW-001-cowaramup-keyring-classic | PREMIUM | 12 | 0.26 | 0.00 | 0.02 | 0.28 | 0.45 | 0.78 | 0.04 | **1.83** | $5-10 | 73% |
| CRW-001-cowaramup-keyring-classic-small | LOW-COST | 20 | 0.10 | 0.00 | 0.01 | 0.28 | 0.15 | 0.00 | 0.01 | **0.56** | $5-10 | 92% |
| CRW-001-cowaramup-keyring-classic-small | NORMAL | 20 | 0.12 | 0.00 | 0.01 | 0.28 | 0.25 | 0.55 | 0.01 | **1.23** | $5-10 | 82% |
| CRW-001-cowaramup-keyring-classic-small | PREMIUM | 20 | 0.17 | 0.00 | 0.01 | 0.28 | 0.45 | 0.66 | 0.03 | **1.61** | $5-10 | 76% |
| CRW-001-cowaramup-keyring-classic-large | LOW-COST | 9 | 0.23 | 0.00 | 0.03 | 0.28 | 0.15 | 0.00 | 0.01 | **0.71** | $5-10 | 90% |
| CRW-001-cowaramup-keyring-classic-large | NORMAL | 9 | 0.27 | 0.00 | 0.03 | 0.28 | 0.25 | 0.73 | 0.03 | **1.60** | $5-10 | 76% |
| CRW-001-cowaramup-keyring-classic-large | PREMIUM | 9 | 0.38 | 0.01 | 0.03 | 0.28 | 0.45 | 0.88 | 0.06 | **2.09** | $6-10 | 71% |
| CRW-002-cowaramup-magnet | LOW-COST | 9 | 0.26 | 0.00 | 0.04 | 0.60 | 0.15 | 0.00 | 0.01 | **1.06** | $5-10 | 84% |
| CRW-002-cowaramup-magnet | NORMAL | 9 | 0.30 | 0.00 | 0.04 | 0.60 | 0.25 | 0.78 | 0.03 | **2.00** | $6-10 | 72% |
| CRW-002-cowaramup-magnet | PREMIUM | 9 | 0.42 | 0.00 | 0.04 | 0.60 | 0.45 | 0.94 | 0.07 | **2.52** | $7-10 | 67% |
| CRW-002-cowaramup-magnet-small | LOW-COST | 16 | 0.17 | 0.00 | 0.02 | 0.60 | 0.15 | 0.00 | 0.01 | **0.95** | $5-10 | 86% |
| CRW-002-cowaramup-magnet-small | NORMAL | 16 | 0.20 | 0.00 | 0.02 | 0.60 | 0.25 | 0.64 | 0.02 | **1.74** | $5-10 | 75% |
| CRW-002-cowaramup-magnet-small | PREMIUM | 16 | 0.28 | 0.00 | 0.02 | 0.60 | 0.45 | 0.77 | 0.05 | **2.17** | $6-10 | 70% |
| CRW-002-cowaramup-magnet-large | LOW-COST | 6 | 0.39 | 0.00 | 0.05 | 0.60 | 0.15 | 0.00 | 0.02 | **1.21** | $5-10 | 82% |
| CRW-002-cowaramup-magnet-large | NORMAL | 6 | 0.45 | 0.01 | 0.05 | 0.60 | 0.25 | 0.95 | 0.05 | **2.36** | $6-10 | 68% |
| CRW-002-cowaramup-magnet-large | PREMIUM | 6 | 0.64 | 0.01 | 0.05 | 0.60 | 0.45 | 1.14 | 0.10 | **2.99** | $8-10 | 64% |
| CRW-003-mini-cow-classic | LOW-COST | 24 | 0.29 | 0.01 | 0.04 | 0.00 | 0.36 | 0.00 | 0.02 | **0.72** | $10-20 | 95% |
| CRW-003-mini-cow-classic | NORMAL | 24 | 0.34 | 0.01 | 0.04 | 0.00 | 0.60 | 0.62 | 0.04 | **1.66** | $10-20 | 88% |
| CRW-003-mini-cow-classic | PREMIUM | 24 | 0.47 | 0.02 | 0.04 | 0.00 | 1.08 | 0.75 | 0.08 | **2.44** | $10-20 | 82% |
| CRW-004-cow-phone-stand | LOW-COST | 3 | 2.12 | 0.02 | 0.30 | 0.00 | 0.36 | 0.00 | 0.12 | **2.91** | $10-20 | 79% |
| CRW-004-cow-phone-stand | NORMAL | 3 | 2.49 | 0.02 | 0.30 | 0.00 | 0.60 | 2.25 | 0.28 | **5.94** | $15-20 | 63% |
| CRW-004-cow-phone-stand | PREMIUM | 3 | 3.49 | 0.03 | 0.30 | 0.00 | 1.08 | 2.70 | 0.57 | **8.16** | $21-21 | 57% |
| CRW-005-articulated-cow | LOW-COST | 2 | 0.88 | 0.04 | 0.13 | 0.00 | 1.32 | 0.00 | 0.05 | **2.42** | $20-50 | 92% |
| CRW-005-articulated-cow | NORMAL | 2 | 1.04 | 0.04 | 0.13 | 0.00 | 2.20 | 3.00 | 0.12 | **6.53** | $20-50 | 80% |
| CRW-005-articulated-cow | PREMIUM | 2 | 1.45 | 0.06 | 0.13 | 0.00 | 3.96 | 3.60 | 0.24 | **9.44** | $24-50 | 72% |

## Single-unit vs batch (NORMAL scenario)

| Product | Cost @1 | Cost @batch | Purge/unit @1 | Purge/unit @batch |
|---|---|---|---|---|
| CRW-001-cowaramup-keyring-classic | 4.20 | 1.41 | 1.08 g | 0.09 g |
| CRW-001-cowaramup-keyring-classic-small | 4.13 | 1.23 | 1.08 g | 0.054 g |
| CRW-001-cowaramup-keyring-classic-large | 4.31 | 1.60 | 1.08 g | 0.12 g |
| CRW-002-cowaramup-magnet | 4.71 | 2.00 | 0.9 g | 0.1 g |
| CRW-002-cowaramup-magnet-small | 4.59 | 1.74 | 0.9 g | 0.056 g |
| CRW-002-cowaramup-magnet-large | 4.90 | 2.36 | 0.9 g | 0.15 g |
| CRW-003-mini-cow-classic | 4.93 | 1.66 | 11.94 g | 0.497 g |
| CRW-004-cow-phone-stand | 7.99 | 5.94 | 1.68 g | 0.56 g |
| CRW-005-articulated-cow | 8.08 | 6.53 | 2.52 g | 1.26 g |
