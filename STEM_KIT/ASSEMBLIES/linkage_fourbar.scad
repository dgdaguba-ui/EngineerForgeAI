// =====================================================================
//  ASSEMBLY: Four-bar linkage (Kit 10, MVP)
//  Ground A = (25,35), B = (85,35) on the base plate (60 mm apart).
//  Crank 20 mm (3-hole link), coupler 50 mm (6-hole), rocker 40 mm
//  (5-hole). Grashof: 20 + 60 <= 50 + 40  →  crank turns fully, rocker
//  rocks 60°; transmission angle stays 51°–125°. Knob on the crank pin.
//  Layers (z): crank & rocker 8.6–12.6, coupler 15.2–19.2.
//  Ground pivots: M3 x 12 head-up, locked to the plate by two nuts;
//  moving pivots: M3 screw head-down, nut on the lower link, nylock top.
// =====================================================================
include <../PARAMETERS/config.scad>
use <asm_lib.scad>
use <../COMMON/mounts/base_plate.scad>
use <../MECHANICAL/linkage/link_bar.scad>
use <../DYNAMO/hand_generator/crank_knob.scad>

crank = 30;          // crank angle (deg)
only = "";

module item(name, col = "SteelBlue") {
    echo("ITEM", name);
    if (only == "" || only == name || (is_list(only) && len([for (o = only) if (o == name) 1]) > 0)) color(col) children();
}

A = [25, 35]; B = [85, 35];
a = 20; b = 50; c = 40;
P = A + a * [cos(crank), sin(crank)];
d = norm(B - P);
u = (B - P) / d;
a1 = (b * b - c * c + d * d) / (2 * d);
h = sqrt(max(b * b - a1 * a1, 0));
Cp = P + a1 * u + h * [-u[1], u[0]];               // upper branch
z1 = plate_thickness + nut_thick + 0.2;            // lower layer
z2 = z1 + foot_thickness + nut_thick;              // coupler layer (15.2)

function ang(p, q) = atan2(q[1] - p[1], q[0] - p[0]);
echo("FOURBAR", P, Cp, ang(B, Cp));

item("base_plate", "Gold") grid_plate(10, 10);
for (g = [A, B]) item(str("ground_nut_", g[0]), "Black") translate([g[0], g[1], plate_thickness]) m3_nut();
item("crank", "Crimson") translate([A[0], A[1], z1]) rotate(crank) link_bar(3);
item("rocker", "SteelBlue") translate([B[0], B[1], z1]) rotate(ang(B, Cp)) link_bar(5);
item("coupler", "Orange") translate([P[0], P[1], z2]) rotate(ang(P, Cp)) link_bar(6);
for (q = [P, Cp]) item(str("lock_nut_", round(q[0])), "Black") translate([q[0], q[1], z1 + foot_thickness]) m3_nut();
item("knob", "Crimson") translate([P[0], P[1], z2 + foot_thickness + 0.2]) crank_knob();
