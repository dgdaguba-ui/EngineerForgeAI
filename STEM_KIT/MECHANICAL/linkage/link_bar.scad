// =====================================================================
//  PART: link bar — MECHANICAL/linkage
//  Flat link with holes on the 10 mm grid pitch: links bolt to plates,
//  to each other and to gears/wheels (coupling holes). Joints = M3
//  screw + M3 nylock nut (snug, then back off 1/4 turn).
//  holes = 3 (20 mm), 5 (40 mm), 6 (50 mm) ... any N.
//  Print: flat. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

holes = 5;
link_bar(holes);

module link_bar(n, w = grid_pitch, t = foot_thickness) {
    L = (n - 1) * grid_pitch;
    difference() {
        hull() for (x = [0, L]) translate([x, 0, 0]) rcyl(w, t, top = 0.8, bottom = chamfer);
        for (i = [0 : n - 1]) translate([i * grid_pitch, 0, 0]) {
            vhole(grid_hole_d, 20);
            for (z = [-0.01, t - 0.4]) translate([0, 0, z]) cylinder(d1 = grid_hole_d + (z < 0 ? 0.8 : 0), d2 = grid_hole_d + (z < 0 ? 0 : 0.8), h = 0.41);
        }
        // length label between the first two holes (links >= 4 holes)
        if (n >= 4) translate([1.5 * grid_pitch, 0, 0]) engrave(str(L), size = 3.2, z = t);
    }
}
