// =====================================================================
//  PART: axle mount — COMMON/mounts
//  Low-cost plain-bore pillow block for 3 mm axles (vehicles, idlers).
//  Axis `h` above the surface over a grid line; screws at (0, ±10).
//  slot > 0 turns the holes into slots across the shaft (X) so the shaft
//  can be slid sideways — belt tensioning, or deliberately bad gear mesh
//  experiments.
//  Print: standing on its foot. No supports (teardrop bore).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

axle_h = axis_height;
axle_slot = 0;
axle_mount(axle_h, axle_slot);

module axle_mount(h = axis_height, slot = 0) {
    W  = 12;              // upright width (X)
    th = 8;               // upright thickness (Y) = bushing length
    t  = foot_thickness;
    fw = W + slot;
    difference() {
        union() {
            rbox([fw, 3 * grid_pitch, t], r = 3, top = 0.6);
            translate([0, th / 2, 0]) rotate([90, 0, 0]) linear_extrude(th)
                hull() {
                    translate([-W / 2 - (h > 25 ? 4 : 0), 0]) square([W + (h > 25 ? 8 : 0), 1]);
                    translate([0, h]) circle(d = W);
                }
        }
        translate([0, 0, h]) teardrop_y(shaft_free_bore, 30);
        for (y = [-grid_pitch, grid_pitch]) translate([0, y, 0])
            if (slot > 0) slot_x(slot, grid_hole_d, 20); else vhole(grid_hole_d, 20);
        // slot travel marks (every 5 mm) engraved on the foot
        if (slot > 0) for (k = [-floor(slot / 10) : floor(slot / 10)])
            translate([k * 5, -1.5 * grid_pitch + 1.5, t - 0.4]) cube([0.6, 2.5, 1], center = true);
    }
}
