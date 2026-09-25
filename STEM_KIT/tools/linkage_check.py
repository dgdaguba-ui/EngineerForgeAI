#!/usr/bin/env python3
"""Kinematic verification of the MVP four-bar linkage (crank-rocker).

Sweeps the crank through 360° in 1° steps and checks:
  * Grashof condition and that the loop closes at every angle (full rotation)
  * transmission angle range (how well the coupler pushes the rocker)
  * crank vs rocker clearance (they share a layer)
  * moving-pivot screw heads vs the ground-pivot nuts on the plate
  * the whole mechanism stays on the 100 x 100 base plate
Writes build/qc/linkage_fourbar_kinematics.json.
"""
import json, math, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = np.array([25.0, 35.0]); B = np.array([85.0, 35.0])
a, b, c = 20.0, 50.0, 40.0          # crank, coupler, rocker
g = float(np.linalg.norm(B - A))    # ground
W = 10.0                            # link width
HEAD_R, NUT_R = 5.7 / 2, 5.5 / math.cos(math.radians(30)) / 2


def seg_dist(p1, p2, q1, q2):
    def pt_seg(p, s1, s2):
        d = s2 - s1; t = np.clip(np.dot(p - s1, d) / np.dot(d, d), 0, 1)
        return np.linalg.norm(p - (s1 + t * d))
    return min(pt_seg(p1, q1, q2), pt_seg(p2, q1, q2), pt_seg(q1, p1, p2), pt_seg(q2, p1, p2))


def main():
    L = sorted([a, b, c, g])
    grashof = L[0] + L[3] <= L[1] + L[2]
    res = {"links_mm": {"ground": g, "crank": a, "coupler": b, "rocker": c},
           "grashof": grashof, "crank_is_shortest": min(a, b, c, g) == a}
    mu, clr, head, xs, ys, rock = [], [], [], [], [], []
    closes = True
    for deg in range(360):
        t = math.radians(deg)
        P = A + a * np.array([math.cos(t), math.sin(t)])
        d = np.linalg.norm(B - P)
        if not (abs(b - c) <= d <= b + c):
            closes = False; continue
        u = (B - P) / d
        a1 = (b * b - c * c + d * d) / (2 * d)
        h = math.sqrt(max(b * b - a1 * a1, 0))
        C = P + a1 * u + h * np.array([-u[1], u[0]])
        mu.append(math.degrees(math.acos((b * b + c * c - d * d) / (2 * b * c))))
        clr.append(seg_dist(A, P, B, C) - W)                       # >0 = gap between link edges
        head.append(min(np.linalg.norm(P - B), np.linalg.norm(C - A)) - HEAD_R - NUT_R)
        rock.append(math.degrees(math.atan2(C[1] - B[1], C[0] - B[0])))
        for p in (A, B, P, C):
            xs.append(p[0]); ys.append(p[1])
    res.update({
        "full_rotation": closes,
        "transmission_angle_deg": [round(min(mu), 1), round(max(mu), 1)],
        "rocker_swing_deg": [round(min(rock), 1), round(max(rock), 1)],
        "min_crank_rocker_gap_mm": round(min(clr), 2),
        "min_pivot_head_to_nut_gap_mm": round(min(head), 2),
        "footprint_mm": [round(min(xs) - W / 2, 1), round(max(xs) + W / 2, 1), round(min(ys) - W / 2, 1), round(max(ys) + W / 2, 1)],
    })
    fp = res["footprint_mm"]
    res["ok"] = (grashof and closes and min(clr) > 0.5 and min(head) > 0.3 and fp[0] >= 0 and fp[1] <= 100
                 and fp[2] >= 0 and fp[3] <= 100 and 30 <= min(mu) and max(mu) <= 150)
    os.makedirs(os.path.join(ROOT, "build", "qc"), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, "build", "qc", "linkage_fourbar_kinematics.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
    raise SystemExit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
