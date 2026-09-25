// =====================================================================
//  PART: shaft collar — COMMON/shafts
//  Locks a shaft axially (or spaces gears) with the standard hub set
//  screw (M3 x 6 grub + M3 nut). Same hub geometry as every gear/wheel.
//  Print: flat. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

collar_h = 8;
shaft_collar();

module shaft_collar(h = collar_h) {
    difference() {
        rcyl(hub_d, h, top = 0.8, bottom = chamfer);
        hub_cuts(0, h, hub_d, h);
    }
}
