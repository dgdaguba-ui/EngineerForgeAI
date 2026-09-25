// =====================================================================
//  PART: printed shaft — COMMON/shafts
//  Ø3 mm (shaft_diameter) printed shaft for light-duty builds. The kit
//  standard is 3 mm STEEL rod (see BOM); printed shafts are a stand-in
//  when steel is not available. A 0.3 mm flat on the underside makes it
//  printable lying down and gives set screws something to bite on.
//  Print: lying flat, 100 % infill, 0.12–0.16 mm layers recommended.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

length = 60;
printed_shaft(length);

module printed_shaft(L) {
    d = shaft_diameter;
    flat = 0.3;
    c = 0.4;
    translate([0, 0, d / 2 - flat]) rotate([0, 90, 0]) difference() {
        rotate_extrude() polygon([[0, 0], [d / 2 - c, 0], [d / 2, c], [d / 2, L - c], [d / 2 - c, L], [0, L]]);
        translate([d / 2 - flat, -d, -1]) cube([d, 2 * d, L + 2]);
    }
}
