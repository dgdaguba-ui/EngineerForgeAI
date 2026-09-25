// =====================================================================
//  PART: motor coupler — COMMON/connectors
//  Joins a 2 mm motor shaft (press fit, top) to a 3 mm kit shaft
//  (set screw, bottom). Lets any motor drive any kit shaft, and lets a
//  motor be used as a generator from a kit shaft.
//  Print: standing, 3 mm bore down. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

coupler_len = 16;
motor_coupler();

module motor_coupler(L = coupler_len) {
    mdepth = motor_shaft_len - 0.3;           // motor side bore depth
    difference() {
        rcyl(hub_d, L, top = 0.8, bottom = chamfer);
        // 3 mm shaft side (bottom) with standard set screw
        hub_cuts(0, L - mdepth - 0.6, hub_d, 2 * (L - mdepth - 0.6) / 2, bore = shaft_fixed_bore, set_screw = false);
        translate([0, 0, (L - mdepth) / 2]) teardrop_x(screw_clear_d, hub_d, center = false);
        nr = shaft_fixed_bore / 2 + (hub_d / 2 - shaft_fixed_bore / 2) / 2;
        translate([nr - nut_slot_t / 2, -nut_pocket_af / 2, (L - mdepth) / 2 - nut_pocket_af / cos(30) / 2 - 0.1])
            cube([nut_slot_t, nut_pocket_af, L]);
        // 2 mm motor side (top), press fit
        translate([0, 0, L - mdepth]) cylinder(d = motor_shaft_bore, h = mdepth + 1);
        translate([0, 0, L - 0.5]) cylinder(d1 = motor_shaft_bore, d2 = motor_shaft_bore + 1, h = 0.51);
    }
}
