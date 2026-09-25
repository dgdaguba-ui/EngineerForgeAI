// =====================================================================
//  PART: solar panel tilt bracket — COMMON/mounts
//  Upright that holds one end boss of the solar panel frame on a pivot
//  (M3 x 12 into the frame's captive nut; tighten = lock the angle).
//  An engraved angle scale (every 15°, 0° = panel flat) sits on the
//  inner face. Use two brackets (second one turned 180°).
//  The foot reaches out to the nearest grid line automatically.
//  Print: foot on the bed. No supports (teardrop pivot hole).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>
include <solar_panel_dims.scad>

pivot_height = 50;
solar_tilt_bracket(pivot_height);

// bracket local frame: inner face (touching the frame boss) at x = 0,
// bracket extends to +x. Returned helper: x of the foot holes.
function stb_hole_x() = let(xin = sp_boss_end + 0.3) (10 * ceil((xin + 4 + 3.2 - 5) / 10) + 5) - xin;

module solar_tilt_bracket(H = 50) {
    t = 4; w = 20;
    hx = stb_hole_x();
    fl = hx + 7;
    difference() {
        union() {
            // upright (plate in the YZ plane, thickness along +X)
            rotate([90, 0, 90]) linear_extrude(t) hull() {
                translate([-w / 2, 0]) square([w, 1]);
                translate([0, H]) circle(d = w);
            }
            // foot
            translate([fl / 2, 0, 0]) rbox([fl, 3 * grid_pitch, foot_thickness], r = 2, top = 0.6);
            // gusset
            translate([0, 1.5, 0]) rotate([90, 0, 0]) linear_extrude(3)
                polygon([[t - 0.01, foot_thickness - 0.01], [hx - 3.5, foot_thickness - 0.01], [t - 0.01, H * 0.55]]);
        }
        translate([0, 0, H]) teardrop_x(grid_hole_d, 3 * t);
        for (y = [-grid_pitch, grid_pitch]) translate([hx, y, 0]) vhole(grid_hole_d, 20);
        // angle scale on the inner face: ticks every 15°, long ticks at 0/±45/±90
        for (a = [-90 : 15 : 90]) translate([0, 0, H]) rotate([a, 0, 0])
            translate([-0.01, -0.35, w / 2 - (a % 45 == 0 ? 3.2 : 2)]) cube([0.6, 0.7, 5]);
        translate([-0.01, 0, H + w / 2 - 4.8]) rotate([90, 0, 90]) linear_extrude(0.6)
            text("0", size = 2.2, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}
