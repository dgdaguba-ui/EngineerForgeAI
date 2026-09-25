// =====================================================================
//  asm_lib.scad — helpers for assemblies + "vitamins" (bought parts)
//  modelled at nominal size so tools/check_assembly.py can verify fits.
// =====================================================================
include <../PARAMETERS/config.scad>
use <../COMMON/stem_core.scad>
use <../COMMON/gears/spur_gear.scad>
use <../COMMON/mounts/motor_mount.scad>

// ---- gear placement on a shaft parallel to Y -------------------------
// mode +1: hub toward -Y (teeth y0..y0-6); mode -1: hub toward +Y.
// align = ["tooth"|"space", world direction in the XZ plane (deg, from
// +X toward +Z)]; world_rot = extra world rotation (animation).
function tooth_local(z) = 90 + 180 / z;
function space_local(z) = 90;
module gear_on_y(z, bore, c, y0, mode, align, world_rot = 0) {
    a0 = align[0] == "tooth" ? tooth_local(z) : space_local(z);
    d  = align[1] + world_rot;
    r  = mode > 0 ? d - a0 : -d - a0;
    translate([c[0], y0, c[1]]) rotate([mode > 0 ? 90 : -90, 0, 0]) rotate(r) spur_gear(z, bore);
}
function dir_xz(a, b) = atan2(b[1] - a[1], b[0] - a[0]);

// ---- vitamins ---------------------------------------------------------
module steel_shaft_y(L, c, y0) {           // Ø3 rod from y0 to y0+L at (x,z)=c
    translate([c[0], y0, c[1]]) rotate([-90, 0, 0]) cylinder(d = shaft_diameter, h = L, $fn = 24);
}
// 130 motor, axis +Y through origin, can centred (same frame as motor_mount)
module motor_130() {
    fl = motor_len / 2;
    translate([0, -fl, 0]) rotate([-90, 0, 0]) linear_extrude(motor_len)
        intersection() { circle(d = motor_d); square([motor_flat, motor_d + 2], center = true); }
    translate([0, fl - 0.01, 0]) rotate([-90, 0, 0]) cylinder(d = motor_boss_d, h = motor_boss_h + 0.01);
    translate([0, fl + motor_boss_h - 0.01, 0]) rotate([-90, 0, 0]) cylinder(d = motor_shaft_d, h = motor_shaft_len + 0.01, $fn = 16);
}
module bearing(b = bearing_size) {         // axis Z, sits on z = 0
    difference() { cylinder(d = b[1], h = b[2]); translate([0, 0, -1]) cylinder(d = b[0], h = b[2] + 2); }
}
module m3_nut() { difference() { cylinder(d = nut_af / cos(30), h = nut_thick, $fn = 6); translate([0, 0, -1]) cylinder(d = 3, h = 5, $fn = 16); } }
module solar_panel() { cube(solar_panel_size); }
