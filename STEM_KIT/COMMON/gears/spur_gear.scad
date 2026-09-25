// =====================================================================
//  PART: spur gear (module 2, 6 mm wide) — COMMON/gears
//  Variants (set with -D):  teeth = 10 | 20 | 30 | 40
//                           bore  = "fixed"  3 mm shaft, M3 set screw hub
//                                   "free"   spins freely (idler)
//                                   "motor"  press-fit on 2 mm motor shaft
//  Print: flat, big face down, hub up. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>
use <gear_lib.scad>

teeth = 20;
bore  = "fixed";

spur_gear(teeth, bore);

module spur_gear(z, bore = "fixed") {
    w  = gear_width;
    rf = root_r(z);
    motor = bore == "motor";
    collar_d = min(10, 2 * rf - 2);
    total_h = motor ? w + 2 : w + hub_h;
    difference() {
        union() {
            gear_body(z, w);
            if (motor) translate([0, 0, w - 0.01]) rcyl(collar_d, 2.01, top = 0.4, bottom = 0);
            else hub_body(w - 0.01, hub_d, hub_h + 0.01);
        }
        // bore + set screw
        if (motor) {
            translate([0, 0, -1]) cylinder(d = motor_shaft_bore, h = total_h + 2);
            translate([0, 0, -0.01]) cylinder(d1 = motor_shaft_bore + 1, d2 = motor_shaft_bore, h = 0.5);
        } else {
            hub_cuts(w, total_h, hub_d, hub_h,
                     bore = bore == "free" ? shaft_free_bore : shaft_fixed_bore,
                     set_screw = bore == "fixed");
        }
        // coupling holes on the 10 mm grid radius: bolt gears to gears,
        // wheels or pulleys to make compound gears (z >= 20)
        if (z >= 20) for (a = (z >= 30 ? [0, 90, 180, 270] : [0, 180]))
            rotate(a) translate([grid_pitch, 0, 0]) vhole(grid_hole_d, 40);
        // windows so children can see through big gears
        if (z >= 30) {
            r_in = hub_d / 2 + 7; r_out = rf - 4;
            for (k = [0 : 3]) rotate(45 + k * 90) window(r_in, r_out, 360 / 4 - 22, w);
        }
        // labels: tooth count + tooth marker (count revolutions!)
        if (!motor && z >= 20) {
            la = 90;
            rotate(la) translate([z >= 30 ? (hub_d / 2 + 7 + rf - 4) / 2 : (hub_d / 2 + rf) / 2 + 0.5, 0, 0])
                rotate(z >= 30 ? 45 - 90 : -90) engrave(str(z, "T"), size = z >= 30 ? 5 : 3.2, z = w);
        }
        marker_r = rf - 1.6;
        rotate(90 + 180 / z) translate([marker_r, 0, w]) marker();
    }
}

// Sector window between two radii, `ang` degrees wide, rounded corners.
module window(r1, r2, ang, h) {
    translate([0, 0, -1]) linear_extrude(h + 2) offset(r = 2) offset(delta = -2)
        intersection() {
            difference() { circle(r = r2); circle(r = r1); }
            polygon([[0, 0], [2 * r2 * cos(-ang / 2), 2 * r2 * sin(-ang / 2)],
                     [2 * r2, 0], [2 * r2 * cos(ang / 2), 2 * r2 * sin(ang / 2)]]);
        }
}

// Small engraved triangle pointing outward at one tooth.
module marker() {
    translate([0, 0, -0.6]) linear_extrude(1) polygon([[1.2, 0], [-1.0, 1.1], [-1.0, -1.1]]);
}
