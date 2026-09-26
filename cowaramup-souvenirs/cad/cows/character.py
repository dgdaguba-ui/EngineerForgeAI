"""'Cowa' v2 - the sculpted Cowaramup cow character (SDF model).

Replaces the ellipsoid-assembly cow. Designer-toy proportions: the head is ~40 %
of the height, the body is chunky and short-legged, and every join is a smooth
blend. Personality comes from:

  * eyes    - recessed sockets, glossy black pupils, a highlight, and a relaxed
              upper lid (content, friendly expression)
  * muzzle  - a wide pink bean with deep nostril recesses and an engraved,
              slightly lopsided smile
  * ears    - asymmetric: one perky, one relaxed; dished pink inner ear
  * horns   - thick, curved, tapered (no thin spikes)
  * head    - turned toward the 3/4 camera and tilted, with a black forelock tuft
  * patches - raised 0.4 mm (tactile), organic edges, following the body; the
              signature patch covers the cow's right eye and right ear
  * hooves  - black, with a moulded split
  * tail    - lies on the ground and curls round, with a black tuft (or forms the
              key loop on the keyring)
  * story   - collar with bell and an ear tag (tool 4 accent)

Coordinates: cow faces -y (toward a camera at the front), z up, ground at z = zb.
Design units are for scale 1.0 (a ~60 mm sitting figure). Absolute feature sizes
(grooves, highlights, relief) are NOT scaled, so small versions stay printable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core import sdf
from ..core.sdf import Frame, rot


@dataclass
class CowaParams:
    scale: float = 1.0
    zb: float = 0.0                  # ground height (top of base)
    head_yaw: float = -16.0          # + turns the face toward +x
    head_roll: float = 7.0
    head_pitch: float = 13.0         # + lifts the chin (less chin overhang, curious look)
    ear_left: tuple = (22.0, -12.0)  # (lift deg, sweep-back deg) cow's LEFT ear (+x)
    ear_right: tuple = (-2.0, -24.0)
    horn_len: float = 1.0
    horn_r: float = 1.0
    tail: str = "ground"             # "ground" | "loop" (keyring)
    collar: bool = True
    bell: bool = True
    ear_tag: bool = True
    relief: float = 0.4              # raised patch height (mm, absolute)
    smile: bool = True
    extra: dict = field(default_factory=dict)


def _surface_point(c, r, direction):
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    t = 1.0 / np.sqrt(np.sum((d / np.asarray(r)) ** 2))
    return np.asarray(c) + d * t, d


def _wobble(x, y, z, amp, seed=0.0):
    return amp * np.sin(0.55 * x + 1.3 + seed) * np.sin(0.47 * y + 0.4 * seed) * np.sin(0.61 * z + 0.7)


def fields(g: sdf.Grid, P: CowaParams, xyz=None) -> dict:
    """Evaluate the character. Returns {'env': body field (pre-closure),
    'layers': [(tool, field, name), ...] in painter order}."""
    k = P.scale
    X, Y, Z = g.P if xyz is None else xyz
    # design space (unit scale), ground at 0
    x, y, z = X / k, Y / k, (Z - P.zb) / k
    A = lambda v: v / k                  # absolute mm -> design units
    D = lambda d: d * k                  # design-unit distance -> mm

    # ------------------------------------------------------------ head (local frame)
    H = np.array([0.0, -6.5, 43.0])
    Rh = rot("z", P.head_yaw) @ rot("y", P.head_roll) @ rot("x", P.head_pitch)
    hf = Frame(H, Rh)
    hx, hy, hz = hf.local(x, y, z)

    skull_c, skull_r = (0, 0, 0), (10.5, 9.6, 10.0)
    head = sdf.ellipsoid(hx, hy, hz, skull_c, skull_r)
    for s in (-1, 1):
        head = sdf.smin(head, sdf.ellipsoid(hx, hy, hz, (s * 5.4, -4.2, -4.0), (5.2, 5.0, 5.0)), 2.0)
    muz_c, muz_r = np.array([0.0, -9.6, -6.2]), np.array([9.4, 6.6, 6.3])
    muzzle = sdf.ellipsoid(hx, hy, hz, muz_c, muz_r)
    head = sdf.smin(head, muzzle, 2.6)

    # forelock tuft (3 lobes)
    lobes = [((-2.4, -3.2, 9.0), (2.2, 3.4, 1.9)), ((0.3, -4.2, 9.4), (2.4, 3.8, 2.0)), ((2.8, -3.0, 8.7), (2.0, 3.1, 1.7))]
    forelock = None
    for c, r in lobes:
        e = sdf.ellipsoid(hx, hy, hz, c, r)
        forelock = e if forelock is None else sdf.smin(forelock, e, 0.6)
    head = sdf.smin(head, forelock, 1.2)

    # horns: thick, curved, tapered
    horns = None
    for s in (-1, 1):
        L = P.horn_len
        pts = sdf.bezier_pts((s * 4.6, 2.0, 7.8), (s * (4.6 + 5.2 * L), 2.4, 9.8 + 1.2 * L),
                             (s * (4.2 + 5.0 * L), 4.2, 10.2 + 5.2 * L), 9)
        hn = sdf.tube(hx, hy, hz, pts, 2.5 * P.horn_r, 1.45 * P.horn_r, 0.4)
        horns = hn if horns is None else np.minimum(horns, hn)
    head = sdf.smin(head, horns, 1.3)

    # ears (asymmetric)
    ear_sel, inner_sel, ears, tag = None, None, None, None
    for s, (lift, sweep) in ((1, P.ear_left), (-1, P.ear_right)):
        root = np.array([s * 8.6, 1.6, 4.4])
        Re = rot("z", s * sweep * -1) @ rot("y", -s * lift)
        ef = Frame(root, Re)
        ex, ey, ez = ef.local(hx, hy, hz)
        ex = ex * s
        ear = sdf.ellipsoid(ex, ey, ez, (5.8, 0.0, 0.0), (6.8, 2.3, 3.7))
        dish = sdf.ellipsoid(ex, ey, ez, (6.4, -1.9, 0.0), (4.4, 0.95, 2.2))
        ear = sdf.sub(ear, dish, 0.3)
        inner = sdf.ellipsoid(ex, ey, ez, (6.4, -2.3, 0.0), (4.7, 1.9, 2.45))
        ears = ear if ears is None else np.minimum(ears, ear)
        inner_sel = inner if inner_sel is None else np.minimum(inner_sel, inner)
        if s == -1:
            ear_sel = sdf.ellipsoid(ex, ey, ez, (5.8, 0.0, 0.0), (7.3, 3.0, 4.2))
        if s == 1 and P.ear_tag:
            tag = sdf.box(ex, ey, ez, (6.6, -1.0, -3.4), (2.2, 0.8, 2.0), 0.7)
    head = sdf.smin(head, ears, 1.6)

    # eyes: socket, pupil, highlight, relaxed upper lid
    pupils, highlights, lids, rings = None, None, None, None
    for s in (-1, 1):
        sp, n = _surface_point(skull_c, skull_r, (s * 0.52, -0.80, 0.30))
        socket = sdf.ellipsoid(hx, hy, hz, sp + n * 0.2, (3.3, 2.4, 3.9))
        head = sdf.sub(head, socket, 0.7)
        pc = sp + n * 0.15
        pupil = sdf.ellipsoid(hx, hy, hz, pc, (2.7, 1.9, 3.3))
        hr = max(1.0, A(1.05))
        hl = sdf.sphere(hx, hy, hz, pc + n * 1.55 + np.array([s * 1.0, 0, 0.45]), hr)   # clear of the lid
        lid = sdf.ellipsoid(hx, hy, hz, sp + np.array([s * 0.3, 0.0, 2.75]) + n * 0.55, (3.35, 1.45, 1.45))
        ring = sdf.ellipsoid(hx, hy, hz, sp, (4.5, 3.2, 5.0))
        pupils = pupil if pupils is None else np.minimum(pupils, pupil)
        highlights = hl if highlights is None else np.minimum(highlights, hl)
        lids = lid if lids is None else np.minimum(lids, lid)
        if s == -1:
            rings = ring
    head = np.minimum(head, pupils)
    head = sdf.smin(head, lids, 1.1)

    # nostrils + smile (engraved)
    nostril_sel = None
    for s in (-1, 1):
        nos = sdf.ellipsoid(hx, hy, hz, (s * 3.4, -15.8, -4.6), (1.35, 1.7, 1.95))
        head = sdf.sub(head, nos, 0.5)
        nostril_sel = nos if nostril_sel is None else np.minimum(nostril_sel, nos)
    smile_sel = None
    if P.smile:
        pts = []
        for t in np.linspace(-1, 1, 9):
            px = 4.4 * t
            pz = -9.4 - 1.0 * (1 - t * t) + 0.35 * t          # lopsided grin
            q = 1 - ((px - muz_c[0]) / muz_r[0]) ** 2 - ((pz - muz_c[2]) / muz_r[2]) ** 2
            py = muz_c[1] - muz_r[1] * np.sqrt(max(q, 0.0)) + 0.12
            pts.append((px, py, pz))
        groove = sdf.tube(hx, hy, hz, pts, A(0.6), A(0.6), 0.2)
        head = sdf.sub(head, groove, 0.25)
        smile_sel = groove

    # ------------------------------------------------------------ body (sitting)
    haunch = sdf.ellipsoid(x, y, z, (0, 7.0, 11.5), (14.5, 13.5, 11.5))
    tx, ty, tz = Frame((0, -1.0, 22.0), rot("x", -12)).local(x, y, z)
    torso = sdf.ellipsoid(tx, ty, tz, (0, 0, 0), (11.6, 10.0, 14.2))
    chest = sdf.ellipsoid(x, y, z, (0, -6.2, 24.0), (10.2, 6.8, 10.0))
    body = sdf.smin(sdf.smin(haunch, torso, 5.0), chest, 3.0)
    neck_top = hf.world((0, 1.5, -6.0))
    body = sdf.smin(body, sdf.capsule(x, y, z, (0, -3.0, 29.0), neck_top, 7.6, 7.0), 4.0)

    hooves_sel = None
    legs = None
    front_hooves = []
    for s in (-1, 1):
        leg = sdf.tube(x, y, z, [(s * 6.2, -4.8, 24.0), (s * 6.6, -7.2, 12.0), (s * 6.9, -8.6, 3.4)], 4.4, 3.8, 1.0)
        hoof = sdf.ellipsoid(x, y, z, (s * 6.9, -9.3, 2.5), (4.35, 4.9, 3.0))
        leg = sdf.smin(leg, hoof, 1.2)
        # folded hind leg lying forward along the ground
        thigh = sdf.ellipsoid(x, y, z, (s * 11.6, 6.0, 9.2), (5.6, 10.4, 8.0))
        shin = sdf.tube(x, y, z, [(s * 12.2, 3.5, 3.8), (s * 12.4, -6.5, 3.1)], 3.6, 3.3, 0.5)
        hhoof = sdf.ellipsoid(x, y, z, (s * 12.4, -8.7, 2.6), (3.7, 4.3, 2.8))
        hind = sdf.smin(sdf.smin(thigh, shin, 2.0), hhoof, 1.0)
        both = np.minimum(leg, hind)
        legs = both if legs is None else np.minimum(legs, both)
        hs = np.minimum(np.maximum(sdf.ellipsoid(x, y, z, (s * 6.9, -9.3, 2.5), (5.0, 5.6, 3.2)), z - 4.2),
                        np.maximum(sdf.ellipsoid(x, y, z, (s * 12.4, -8.7, 2.6), (4.3, 4.9, 3.2)), z - 4.0))
        hooves_sel = hs if hooves_sel is None else np.minimum(hooves_sel, hs)
        front_hooves.append((s * 6.9, -9.3, s * 12.4, -8.7))
    body = sdf.smin(body, legs, 2.2)

    # hoof splits (moulded groove, absolute 0.9 mm wide)
    w = A(0.45)
    for s in (-1, 1):
        for hxw, hyw, zt in ((s * 6.9, -9.3, 4.4), (s * 12.4, -8.7, 4.0)):
            split = np.maximum(np.maximum(np.abs(x - hxw) - w, y - (hyw - 1.4)), z - zt)
            body = np.maximum(body, -split)

    # tail
    if P.tail == "loop":
        loop_c = np.array([0.0, 21.0, 16.0])
        tail = sdf.tube(x, y, z, [(0, 17.0, 10.0), (0, 20.0, 11.5), loop_c + (0, 0, -3.2)], 2.2, 2.0, 0.8)
        ring = sdf.torus(x, y, z, loop_c, A(2.6) + A(1.95), A(1.95), axis="x")
        tail = sdf.smin(tail, ring, 0.8)
        tuft = sdf.ellipsoid(x, y, z, loop_c + (0, 1.2, 4.6), (2.6, 2.2, 2.4))
    else:
        tail = sdf.tube(x, y, z, sdf.bezier_pts((-2.5, 19.0, 9.0), (-9.0, 23.0, 1.6), (-15.5, 14.0, 1.9), 10), 1.95, 1.65, 0.6)
        tuft = None
        for c, r in (((-16.8, 11.2, 2.2), (3.0, 4.2, 2.3)), ((-18.2, 12.4, 2.0), (2.2, 3.4, 1.9)), ((-15.2, 10.6, 2.0), (2.0, 3.2, 1.9))):
            e = sdf.ellipsoid(x, y, z, c, r)
            tuft = e if tuft is None else sdf.smin(tuft, e, 0.5)
    body = sdf.smin(body, sdf.smin(tail, tuft, 0.8), 1.2)

    env = sdf.smin(body, head, 3.2)
    # dewlap: the fold of skin under a cow's throat - anatomical, and it carries the chin
    # overhang down to the chest so the muzzle prints without support
    chin = hf.world((0.0, -10.5, -10.8))
    dew = sdf.capsule(x, y, z, chin, (0.0, -9.0, 25.0), 3.4, 5.5)
    env = sdf.smin(env, dew, 2.5)
    env = np.maximum(env, -z)  # flat bottom on the ground

    # ------------------------------------------------------------ markings (raised, organic)
    patch_body = None
    for c, r in (((3.0, 12.5, 20.0), 7.2), ((-2.5, 15.5, 14.5), 6.0), ((7.5, 8.0, 25.0), 4.8),
                 ((11.5, -2.0, 21.5), 5.4), ((10.5, 2.0, 15.5), 4.4),
                 ((-13.2, 8.5, 11.5), 5.2), ((-11.0, 14.0, 8.5), 4.0),
                 ((-9.5, -7.5, 20.5), 3.6), ((-8.2, -9.6, 15.0), 2.8),      # right shoulder -> front leg
                 ((-6.0, 3.0, 33.5), 3.4), ((-3.5, 6.5, 31.0), 3.0)):     # neck/back marking
        e = sdf.sphere(x, y, z, c, r)
        patch_body = e if patch_body is None else sdf.smin(patch_body, e, 1.5)
    patch_body = patch_body + _wobble(x, y, z, 0.9)
    patch_head = None
    for c, r in (((-5.2, -7.6, 2.6), 5.4), ((-8.2, -3.0, 4.2), 4.8), ((-10.0, 1.2, 5.2), 4.0)):
        e = sdf.sphere(hx, hy, hz, c, r)
        patch_head = e if patch_head is None else sdf.smin(patch_head, e, 1.2)
    patch_head = np.minimum(patch_head + _wobble(hx, hy, hz, 0.6, 2.0), ear_sel)
    patch = np.minimum(patch_body, patch_head)
    rel = A(P.relief)
    raised = np.maximum(env - rel, np.minimum(patch_body, patch_head))
    raised = np.maximum(raised, -(rings + 0.6))       # no relief over the eye inside the patch
    raised = np.maximum(raised, -(inner_sel - A(0.4)))  # ...or inside the dished inner ear
    env = np.minimum(env, raised)

    # ------------------------------------------------------------ story accents (tool 4)
    accents = []
    if P.collar:
        a0, a1 = np.array([0, -3.0, 29.0]), np.asarray(neck_top)
        ax = (a1 - a0) / np.linalg.norm(a1 - a0)
        c0 = a0 + (a1 - a0) * 0.22
        px, py, pz = x - c0[0], y - c0[1], z - c0[2]
        pa = px * ax[0] + py * ax[1] + pz * ax[2]
        radial = np.sqrt(np.maximum(px * px + py * py + pz * pz - pa * pa, 0))
        # a 3.4 mm band that follows the neck surface, standing 1.2 mm proud
        collar = np.maximum(np.abs(pa) - 1.7, body - 1.2)
        collar = np.maximum(collar, -(body + 1.8))
        collar = np.maximum(collar, radial - 11.2)
        env = np.minimum(env, collar)
        accents.append(("collar", collar))
        if P.bell:
            bc = np.array([0.0, -13.9, 25.4])
            bell = sdf.smin(sdf.ellipsoid(x, y, z, bc, (3.0, 2.8, 3.1)),
                            sdf.capsule(x, y, z, bc + (0, 0.6, 2.2), bc + (0, 1.3, 4.2), 1.2), 0.6)
            bell = sdf.sub(bell, np.maximum(np.abs(z - (bc[2] - 1.3)) - A(0.4), y - (bc[1] - 1.5)), 0.2)
            env = np.minimum(env, bell)
            accents.append(("bell", bell))
    if tag is not None:
        env = np.minimum(env, tag)
        accents.append(("ear tag", tag))

    # ------------------------------------------------------------ painter layers (priority order)
    grow = A(0.15)
    skin = A(1.4)   # surface-colour regions must reach past blended skin
    layers = [
        ("tool_2", np.minimum(patch - grow, forelock - A(0.6)), "raised patches + forelock"),
        ("tool_2", hooves_sel, "hooves"),
        ("tool_2", tuft - A(0.5), "tail tuft"),
        ("tool_1", rings, "eye ring (in patch)"),
        ("tool_3", muzzle - skin, "muzzle"),
        ("tool_3", inner_sel, "inner ears"),
        ("tool_1", lids - A(0.35), "eyelids"),
        ("tool_2", pupils - A(0.3), "pupils"),
        ("tool_1", highlights - A(0.35), "eye highlights"),
    ]
    if nostril_sel is not None:
        layers.insert(6, ("tool_2", nostril_sel - A(0.35), "nostrils"))
    if smile_sel is not None:
        layers.insert(6, ("tool_2", smile_sel - A(0.35), "smile"))
    for name, f in accents:
        layers.append(("tool_4", f - A(0.35), name))
    return {"env": D(env), "layers": [(t, D(f), n) for t, f, n in layers]}
