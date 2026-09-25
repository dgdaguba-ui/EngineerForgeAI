// =====================================================================
//  PART: hand crank arm — DYNAMO/hand_generator
//  Crank for a 3 mm shaft. Hub Ø16 with TWO M3 set screws (180° apart,
//  different heights) because a crank carries the most torque in the kit.
//  Knob holes at 20 mm and 30 mm radius: change the crank length and
//  feel the effect of leverage. Knob = crank_knob on an M3 x 40 screw,
//  head in the counterbore on the hub side, locked by a nut in front.
//  Print: knob side (flat face) down, hub up. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

crank_radius_max = 3 * grid_pitch;
hand_crank();

module hand_crank(R = crank_radius_max) {
    t = 6; w = 16; hd = 16; hh = 14;
    difference() {
        union() {
            translate([0, 0, 0]) linear_extrude(t, convexity = 4) offset(r = 0) stadium2d(R, w);
            translate([0, 0, t - 0.01]) rcyl(hd, hh + 0.01, top = 0.8, bottom = 0);
        }
        // edge rounding of the arm (top & bottom chamfers)
        arm_edge_chamfer(R, w, t);
        // bore + two set screws
        hub_cuts(t, t + hh, hd, hh / 2, bore = shaft_fixed_bore, set_screw = true, screw_angle = 0);
        hub_cuts(t + hh / 2, t + hh, hd, hh / 2, bore = shaft_fixed_bore, set_screw = true, screw_angle = 180);
        // knob holes at 20 and 30 mm: counterbore on the hub side for the screw head
        for (r = [2 * grid_pitch, 3 * grid_pitch]) if (r <= R) translate([r, 0, 0]) {
            vhole(grid_hole_d, 30);
            translate([0, 0, t - 2]) cylinder(d = counterbore_d, h = 5);
        }
        // radius labels on the flat (front) face — mirrored so they read correctly
        for (r = [2 * grid_pitch, 3 * grid_pitch]) translate([r - 5.5, 0, -1]) rotate(90) mirror([1, 0, 0])
            linear_extrude(1.6) text(str(r), size = 3, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}
module arm_edge_chamfer(R, w, t) {
    c = 1;
    difference() {
        translate([-w, -w, -1]) cube([R + 2 * w, 2 * w, t + 1 - 0.02]);
        hull() {
            translate([0, 0, c]) linear_extrude(t - 2 * c) stadium2d(R, w);
            linear_extrude(t) offset(delta = -c) stadium2d(R, w);
        }
    }
}
