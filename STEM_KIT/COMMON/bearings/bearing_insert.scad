// =====================================================================
//  PART: bearing inserts — COMMON/bearings
//  Drop into the 16 mm pocket of any bearing mount:
//    type = "623"     adapter ring for a 623 (3x10x4) ball bearing
//    type = "bushing" printed plain bearing for a 3 mm shaft (no bearing)
//  Print: flat, shoulder down. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

type = "623";
bearing_insert(type);

module bearing_insert(type) {
    od = bearing_size[1];
    h  = bearing_size[2];
    difference() {
        rcyl(od, h, top = 0.4, bottom = 0.4);
        if (type == "623") {
            // bearing seat from top, 1 mm shoulder at the bottom
            translate([0, 0, 1]) cylinder(d = bearing_small[1] + 0.1, h = h);
            translate([0, 0, -1]) cylinder(d = bearing_small[1] - 3, h = h + 2);
        } else {
            translate([0, 0, -1]) cylinder(d = shaft_free_bore - 0.1, h = h + 2);
            // oil groove
            translate([0, 0, h / 2]) rotate_extrude() translate([(shaft_free_bore - 0.1) / 2, 0]) circle(d = 0.8, $fn = 12);
            for (z = [-0.01, h - 0.4]) translate([0, 0, z]) cylinder(d1 = shaft_free_bore + (z < 0 ? 0.8 : 0), d2 = shaft_free_bore + (z < 0 ? 0 : 0.8), h = 0.41);
        }
        // grip slot to pull the insert back out
        translate([od / 2 - 1.2, -1.5, h - 1]) cube([3, 3, 2]);
    }
}
