// =====================================================================
//  PART: vertical support / pillar — COMMON/mounts
//  10 x 10 mm pillar with an M3 through-hole and a captive-nut slot
//  2.8 mm from each end. An M3 x 10 through a 6 mm plate (or 4 mm foot
//  + counterbore) engages the nut. Uses: gearbox frame spacers (48 mm),
//  solar-panel standoffs (48 mm), towers, raised mounts.
//  Print: standing. No supports (slot roofs bridge 5.9 mm).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

pillar_len = frame_gap;
vertical_support(pillar_len);

module vertical_support(L) {
    s = grid_pitch;
    difference() {
        rbox([s, s, L], r = 1.2, top = 0.6, bottom = chamfer);
        vhole(grid_hole_d, 3 * L);
        for (z = [2.8, L - 2.8]) translate([0, 0, z]) nut_slot_x(s);
        // mid-length label: length in mm
        translate([s / 2 - 0.5, 0, L / 2]) rotate([90, 0, 90]) linear_extrude(1)
            text(str(L), size = 4, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}
