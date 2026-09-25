// =====================================================================
//  PART: universal base plate — COMMON/mounts
//  100 x 100 x 6 mm, 10 x 10 grid of M3 holes (10 mm pitch, 5 mm from
//  every edge) with hex nut pockets underneath. Everything in the kit
//  bolts to this lattice. Plates tile edge-to-edge without breaking the
//  lattice; join them with rails (M3 x 12).
//  Print: flat, pockets down. No supports (pocket ceilings bridge 6 mm).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

nx = plate_size / grid_pitch;
ny = plate_size / grid_pitch;

grid_plate(nx, ny);

// Generic grid plate, corner at origin, holes at (5 + 10 i, 5 + 10 j).
// skip = list of [i, j] holes to omit; cut() children are subtracted.
module grid_plate(nx, ny, t = plate_thickness, pockets = true, r = 3, skip = []) {
    w = nx * grid_pitch; d = ny * grid_pitch;
    difference() {
        translate([w / 2, d / 2, 0]) rbox([w, d, t], r = r, top = 0.8, bottom = chamfer);
        for (i = [0 : nx - 1], j = [0 : ny - 1])
            if (len(search([[i, j]], skip)) == 0 || search([[i, j]], skip)[0] == [])
                translate([grid_pitch / 2 + i * grid_pitch, grid_pitch / 2 + j * grid_pitch, 0]) {
                    vhole(grid_hole_d, 3 * t);
                    // countersink-style entry chamfer on top (easier screw start)
                    translate([0, 0, t - 0.5]) cylinder(d1 = grid_hole_d, d2 = grid_hole_d + 1, h = 0.51);
                    if (pockets) translate([0, 0, -0.01]) nut_pocket();
                }
        children();
    }
}
