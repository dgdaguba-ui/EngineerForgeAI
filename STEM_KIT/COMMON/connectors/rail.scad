// =====================================================================
//  PART: rail — COMMON/connectors
//  1 x N strip, 10 wide x 6 tall (same thickness as a base plate), so
//  anything that bolts to a plate bolts to a rail with the same M3 x 10.
//  Uses: joining plates (M3 x 12), chassis rails, frames, braces, towers.
//  Print: flat, pockets down. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

holes = 10;
rail(holes);

module rail(n) {
    L = n * grid_pitch;
    difference() {
        translate([L / 2, 0, 0]) rbox([L, grid_pitch, plate_thickness], r = grid_pitch / 2 - 0.01, top = 0.8);
        for (i = [0 : n - 1]) translate([grid_pitch / 2 + i * grid_pitch, 0, 0]) {
            vhole(grid_hole_d, 20);
            translate([0, 0, -0.01]) nut_pocket();
            translate([0, 0, plate_thickness - 0.5]) cylinder(d1 = grid_hole_d, d2 = grid_hole_d + 1, h = 0.51);
        }
    }
}
