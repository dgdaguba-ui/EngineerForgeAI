// =====================================================================
//  PART: corner connector (90° bracket) — COMMON/connectors
//  Stands any plate/rail upright on the grid. Horizontal leg bolts to
//  the base (hole 15 mm from the vertical face); vertical leg bolts to
//  the upright plate (hole 15 mm above the base). Both stay on the grid
//  when the upright's face is on a grid line (multiple of 10 mm).
//  Coordinates: vertical face at y = 0, bracket occupies y < 0.
//  Print: horizontal leg on the bed. No supports (teardrop hole).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

corner_connector();

module corner_connector(width = 2 * grid_pitch, reach = 2 * grid_pitch) {
    t = foot_thickness;
    difference() {
        union() {
            // horizontal leg
            translate([0, -reach / 2, 0]) rbox([width, reach, t], r = 2, top = 0.6);
            // vertical leg
            translate([0, -t / 2, 0]) rotate([90, 0, 0]) translate([0, 0, -t / 2])
                linear_extrude(t) translate([0, reach / 2]) rrect([width, reach], 2);
            // central gusset (between the screw heads)
            translate([-1.5, 0, 0]) rotate([90, 0, 90]) linear_extrude(3)
                polygon([[-0.01, t - 0.01], [-(reach - 9), t - 0.01], [-0.01, reach - 9]]);
        }
        for (x = [-grid_pitch / 2, grid_pitch / 2]) {
            // horizontal leg holes (vertical axis) at y = -15
            translate([x, -1.5 * grid_pitch, 0]) vhole(grid_hole_d, 20);
            // vertical leg holes (along Y) at z = 15
            translate([x, 0, 1.5 * grid_pitch]) teardrop_y(grid_hole_d, 20);
        }
    }
}
