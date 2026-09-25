// =====================================================================
//  PART: bearing mount (pillow block) — COMMON/bearings
//  Holds one 625 bearing (5x16x5) — or, with an insert, a 623 bearing
//  or a printed plain bushing for 3 mm shafts — with its axis
//  `axis_height` above the surface, directly over a grid line.
//  Mounting: two M3 x 10 at (0, ±10), i.e. along the shaft direction (Y).
//  Print: standing on its foot. No supports (truncated teardrop pocket).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

bearing_mount();

module bearing_mount(h = axis_height) {
    pw = bearing_pocket_d;              // pocket diameter
    bw = bearing_size[2];               // bearing width
    th = bw + 3;                        // upright thickness (Y)
    W  = pw + 2 * 2.9;                  // upright width (X)
    t  = foot_thickness;
    difference() {
        union() {
            // foot
            rbox([W, 3 * grid_pitch, t], r = 3, top = 0.6);
            // upright: rectangle up to axis + round top
            translate([0, th / 2, 0]) rotate([90, 0, 0]) linear_extrude(th)
                hull() {
                    translate([-W / 2, 0]) square([W, 1]);
                    translate([0, h]) circle(d = W);
                }
        }
        // bearing pocket from +Y face, truncated teardrop (roof prints)
        translate([0, th / 2 - bw - 0.2, h]) rotate([-90, 0, 0]) linear_extrude(bw + 1)
            trunc_teardrop(pw);
        // shaft / inner-race clearance through the back wall
        translate([0, 0, h]) teardrop_y(bearing_size[0] + 6, 30);
        // mounting holes
        for (y = [-grid_pitch, grid_pitch]) translate([0, y, 0]) vhole(grid_hole_d, 20);
    }
}

module trunc_teardrop(d) {
    r = d / 2;
    intersection() {
        union() {
            circle(d = d);
            polygon([[-r * sqrt(2) / 2, -r * sqrt(2) / 2], [0, -r * sqrt(2)], [r * sqrt(2) / 2, -r * sqrt(2) / 2]]);
        }
        translate([-d, -r - 0.9]) square([2 * d, d + 0.9 + d]);
    }
}
