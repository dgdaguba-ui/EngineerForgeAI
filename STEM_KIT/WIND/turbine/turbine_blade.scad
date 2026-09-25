// =====================================================================
//  PART: wind turbine blade — WIND/turbine
//  Flat, thick-edged (≥ 2 mm, rounded) blade: safe to touch, prints flat.
//  style = "standard" | "torque" (wide & short: starts in light wind,
//          strong turning force) | "speed" (narrow & long: spins fast).
//  Root peg Ø8 fits every hub socket; the small fin on the root is the
//  pitch pointer — line it up with the hub's tick marks.
//  Print: flat. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

style = "standard";
turbine_blade(style);

function blade_dims(s) =            // [length, root width, tip width]
    s == "torque" ? [80, 44, 34] :
    s == "speed"  ? [100, 22, 12] :
                    [90, 32, 20];

module turbine_blade(s = "standard") {
    d = blade_dims(s);
    L = d[0]; wr = d[1]; wt = d[2];
    t = 3;                       // blade thickness
    pr = 4;                      // peg radius
    pz = t / 2 + 1.0;            // peg axis height (peg flat on the bed)
    peg = 12.5;                  // peg length (socket 12)
    x0 = peg + 6;                // blade starts here
    c = 0.5;                     // edge chamfer → 2 mm flat edge
    union() {
        // root peg with a flat underside
        difference() {
            translate([0, 0, pz]) rotate([0, 90, 0])        // chamfered tip = lead-in
                rotate_extrude() polygon([[0, 0], [pr - 0.8, 0], [pr, 0.8], [pr, peg + 0.5], [0, peg + 0.5]]);
            translate([-1, -5, -5]) cube([peg + 3, 10, 5]);
        }
        // neck: peg → blade
        hull() {
            translate([peg, 0, 0]) intersection() {
                translate([0, 0, pz]) rotate([0, 90, 0]) cylinder(r = pr, h = 0.5);
                translate([-1, -5, 0]) cube([3, 10, 10]);
            }
            translate([x0 + 4, 0, 0]) linear_extrude(t) square([1, wr * 0.8], center = true);
        }
        // pitch pointer fin on top of the neck
        translate([peg + 1, -0.6, pz + pr - 0.8]) cube([3, 1.2, 1.4]);
        // blade body with chamfered (rounded) edges
        hull() {
            translate([0, 0, c]) linear_extrude(t - 2 * c) blade2d(x0, L, wr, wt);
            linear_extrude(t) offset(delta = -c) blade2d(x0, L, wr, wt);
        }
    }
}
module blade2d(x0, L, wr, wt) {
    hull() {
        translate([x0, -wr / 2 * 0.8]) square([1, wr * 0.8]);
        translate([x0 + wr / 2 + 2, 0]) circle(d = wr);          // never reaches behind the root
        translate([x0 + L - wt / 2, 0]) circle(d = wt);
    }
}
