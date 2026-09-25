// =====================================================================
//  PART: gearbox frame plate (open lattice) — MECHANICAL/gearbox
//  100 x 100 x 6 mm see-through plate with a ring at EVERY grid point:
//  each ring is a 6 mm plain bushing for a 3 mm shaft, so a shaft can go
//  anywhere on the lattice and any two gears on the grid mesh.
//  Openings are < 6.2 mm (no child's finger fits through).
//  Two plates + four 48 mm vertical supports = the gearbox frame used by
//  the Gearbox Lab and the Hand-Crank Dynamo.
//  Print: flat. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

gearbox_frame_plate();

module gearbox_frame_plate(n = plate_size / grid_pitch, t = plate_thickness) {
    S = n * grid_pitch;
    ring_d = 8; bar = 3.6; band = 6.5;
    difference() {
        intersection() {
            translate([S / 2, S / 2, 0]) rbox([S, S, t], r = 3, top = 0.8, bottom = chamfer);
            linear_extrude(t) union() {
                difference() { square([S, S]); translate([band, band]) square([S - 2 * band, S - 2 * band]); }
                for (i = [0 : n - 1]) {
                    translate([grid_pitch / 2 + i * grid_pitch - bar / 2, 0]) square([bar, S]);
                    translate([0, grid_pitch / 2 + i * grid_pitch - bar / 2]) square([S, bar]);
                }
                for (i = [0 : n - 1], j = [0 : n - 1])
                    translate([grid_pitch / 2 + i * grid_pitch, grid_pitch / 2 + j * grid_pitch]) circle(d = ring_d);
            }
        }
        for (i = [0 : n - 1], j = [0 : n - 1]) translate([grid_pitch / 2 + i * grid_pitch, grid_pitch / 2 + j * grid_pitch, 0]) {
            vhole(grid_hole_d, 3 * t);
            for (z = [-0.01, t - 0.4]) translate([0, 0, z]) cylinder(d1 = grid_hole_d + (z < 0 ? 0.8 : 0), d2 = grid_hole_d + (z < 0 ? 0 : 0.8), h = 0.41);
        }
    }
}
