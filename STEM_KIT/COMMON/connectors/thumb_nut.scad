// =====================================================================
//  PART: thumb nut — COMMON/connectors
//  Knurled knob with a pressed-in M3 nut: children tighten joints by
//  hand, no spanner needed. Also the friction lock for tilting mounts.
//  Print: flat, nut pocket up. Press an M3 nut in (vice or tap lightly).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

thumb_nut();

module thumb_nut(d = 18, h = 8) {
    difference() {
        union() {
            rcyl(d - 2, h, top = 1.2, bottom = chamfer);
            for (a = [0 : 30 : 359]) rotate(a) translate([d / 2 - 1.5, 0, 0])
                cylinder(d = 3, h = h - 1.2, $fn = 16);
        }
        vhole(grid_hole_d, 40);
        // tight pocket: nut is pressed in and can't spin
        translate([0, 0, h - nut_thick - 0.2]) cylinder(d = (nut_af + 0.1) / cos(30), h = 10, $fn = 6);
    }
}
