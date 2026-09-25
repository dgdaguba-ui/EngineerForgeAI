// =====================================================================
//  PART: wheel — COMMON/wheels
//  Ø60 x 10 mm wheel on the standard set-screw hub. A V-groove takes an
//  O-ring tyre (50 x 3 mm) — or the wheel doubles as a belt pulley.
//  Coupling holes on the 10 mm radius accept any 20T+ gear or pulley
//  (M3 x 16) to build geared wheels.
//  style = "disc"  : sturdy, 6 round windows (common wheel)
//          "spoke" : 5 thin spokes, lightest (solar vehicle wheel)
//  Print: flat, hub up. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

wheel_style = "disc";
wheel(wheel_diameter, wheel_width, wheel_style);

module wheel(D = wheel_diameter, W = wheel_width, style = "disc") {
    R = D / 2;
    g = oring_cs * 0.55;          // groove depth
    rim_t = 4;
    total_h = W + hub_h;
    difference() {
        union() {
            // rim with 45° V groove (printable)
            rotate_extrude($fn = 120) polygon([
                [R - rim_t - g, 0], [R - 0.6, 0], [R, 0.6], [R, W / 2 - g],
                [R - g, W / 2], [R, W / 2 + g], [R, W - 0.6], [R - 0.6, W], [R - rim_t - g, W]]);
            // web
            difference() {
                cylinder(r = R - rim_t - g + 0.5, h = style == "spoke" ? 3 : 4);
                if (style == "spoke") translate([0, 0, -1]) cylinder(r = R - rim_t - g, h = 10);
                else for (k = [0 : 5]) rotate(30 + k * 60) translate([(R - rim_t - g + hub_d / 2 + 5) / 2 + 1, 0, -1])
                    cylinder(d = (R - rim_t - g) - hub_d / 2 - 9, h = 10);
            }
            if (style == "spoke") for (k = [0 : 4]) rotate(k * 72 + 36)
                translate([0, -2, 0]) cube([R - rim_t - g + 0.5, 4, 5]);
            // coupling boss ring
            cylinder(r = grid_pitch + 3.5, h = style == "spoke" ? 3 : 4);
            hub_body(0, hub_d, total_h);
        }
        hub_cuts(W, total_h, hub_d, hub_h);
        for (a = [0 : 90 : 270]) rotate(a) translate([grid_pitch, 0, 0]) vhole(grid_hole_d, 40);
    }
}
