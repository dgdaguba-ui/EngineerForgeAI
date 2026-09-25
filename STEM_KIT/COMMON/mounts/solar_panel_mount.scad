// =====================================================================
//  PART: solar panel frame — COMMON/mounts
//  Holds a BOUGHT epoxy solar panel (size from config: solar_panel_size,
//  default 110 x 69 x 3 mm, 5 V 1 W). The panel slides in from the open
//  long side (+Y) under 45° lips and clicks past a detent ridge.
//   • Back bars (y = ±15) carry grid holes at odd multiples of 5 mm from
//     the frame centre → bolt straight onto pillars / the grid (FIXED).
//   • End bosses with a captive nut → pivot in the tilt bracket (HINGED).
//  Print: back down. No supports (45° lips, teardrop pivot holes).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>
include <solar_panel_dims.scad>

solar_panel_frame();

module solar_panel_frame() {
    P = sp_pocket; O = sp_outer;
    bar_w = 9;
    nb = floor((P[0] / 2 - 4) / grid_pitch);          // holes per half-bar
    difference() {
        union() {
            translate([0, 0, 0]) rbox(O, r = 3, top = 0.8);
            // pivot bosses (D-shaped so they sit flat on the bed)
            for (s = [-1, 1]) translate([s * (O[0] / 2 + sp_boss_len / 2 - 0.01), 0, 0])
                rotate([0, 90, 0]) translate([0, 0, -sp_boss_len / 2]) linear_extrude(sp_boss_len + 0.02)
                    hull() { translate([-sp_boss_z, 0]) circle(r = sp_boss_r); translate([-0.01, -sp_boss_r]) square([0.01, 2 * sp_boss_r]); }
        }
        // panel pocket, open along the +Y long side so the panel slides in
        // sideways (the pivot bosses on the X ends stay clear of its path)
        translate([-P[0] / 2, -P[1] / 2, sp_back]) cube([P[0], P[1] + O[1], P[2]]);
        // 45° lips over the two short ends and the closed long side
        hull() {
            translate([-P[0] / 2, -P[1] / 2, sp_back + P[2] - 0.01]) cube([P[0], P[1] + O[1], 0.01]);
            translate([-P[0] / 2 + sp_lip, -P[1] / 2 + sp_lip, sp_back + P[2] + sp_lip]) cube([P[0] - 2 * sp_lip, P[1] + O[1], 0.02]);
        }
        // back window (wires, cooling, weight) leaving a ledge + two bars
        for (y0 = [[-P[1] / 2 + 6, -15 - bar_w / 2], [-15 + bar_w / 2, 15 - bar_w / 2], [15 + bar_w / 2, P[1] / 2 - 6]])
            translate([-P[0] / 2 + 6, y0[0], -1]) linear_extrude(sp_back + 2)
                offset(r = 2) offset(delta = -2) square([P[0] - 12, y0[1] - y0[0]]);
        // bar holes on the grid (odd multiples of 5 from centre), counterbored from the panel side
        for (y = [-15, 15], i = [-nb : nb - 1]) translate([grid_pitch / 2 + i * grid_pitch, y, 0]) {
            vhole(grid_hole_d, 30);
            translate([0, 0, sp_back - 2]) cylinder(d = counterbore_d, h = 10);
        }
        // pivot holes + captive nut slots
        for (s = [-1, 1]) {
            translate([s * (O[0] / 2 + sp_boss_len / 2), 0, sp_boss_z]) teardrop_x(grid_hole_d, sp_boss_len + 8);
            translate([s * (O[0] / 2 + sp_boss_len / 2) - nut_slot_t / 2, -nut_pocket_af / 2, sp_boss_z - nut_pocket_af / cos(30) / 2 - 0.1])
                cube([nut_slot_t, nut_pocket_af, 20]);
        }
    }
    // detent ridge along the open side (+Y): the panel clicks past it
    // (just outside the seated panel's edge: gentle ramp outward, steep face toward the panel)
    translate([0, P[1] / 2 + 1.3, sp_back - 0.01]) rotate([90, 0, 90]) linear_extrude(P[0] - 30, center = true)
        polygon([[-0.5, 0], [1.4, 0], [0.5, 0.7], [-0.4, 0.7]]);
}
