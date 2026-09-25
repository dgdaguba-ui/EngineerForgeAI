// =====================================================================
//  PART: crank knob — DYNAMO/hand_generator
//  Free-spinning handle: slides over an M3 x 40 screw that is locked to
//  the crank arm; an M3 nylock nut (hidden in the top recess) keeps it
//  on without clamping it, so it turns in the child's hand (no skin
//  friction). Shared by the hand generator and the linkage lab.
//  Print: standing, recess up. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

knob_len = 28;
crank_knob(knob_len);

module crank_knob(L = 28, d = 18) {
    r = d / 2;
    difference() {
        rotate_extrude() polygon([[0, 0], [r - 2.6, 0], [r - 2, 0.6], [r, 6], [r, L - 8], [r - 2, L - 2], [r - 3, L], [0, L]]);
        vhole(shaft_free_bore + 0.2, 3 * L);
        // nylock recess (nylock M3 is 4 mm tall)
        translate([0, 0, L - 4.8]) cylinder(d = (nut_af + 0.6) / cos(30), h = 10, $fn = 6);
    }
}
