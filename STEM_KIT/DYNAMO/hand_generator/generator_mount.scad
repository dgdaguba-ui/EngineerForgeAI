// =====================================================================
//  PART: generator mount (axial motor mount) — DYNAMO/hand_generator
//  Holds a 130-size DC motor used as a GENERATOR with its shaft pointing
//  straight into a plate (motor axis ⟂ mounting face, on a grid hole).
//  Motor shaft → motor_coupler → 3 mm kit shaft → through the grid hole
//  → 10T pinion inside the gearbox. Open sides let children watch the
//  coupler spin and reach its set screw.
//  Bar foot 10 mm wide with holes at (±20, 0); turn the mount 90° to
//  use a vertical pair instead (bottom-row holes then sit flush with the
//  base plate, so the foot never hits it).
//  Print: foot on the bed. No supports (floor bridges between the legs).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

generator_mount();

gm_floor_z = 21.1;            // bottom of the socket floor (coupler top is at 21.0)

module motor_section_y(c) {   // flats parallel to X (|y| limited)
    intersection() { circle(r = motor_d / 2 + c); square([motor_d + 4, motor_flat + 2 * c], center = true); }
}

module generator_mount() {
    t = foot_thickness;
    c = 0.1;                   // snug: motor is a push fit
    fz = gm_floor_z; ft = 2;   // floor
    sock = 16;                 // socket depth
    difference() {
        union() {
            // cross foot
            linear_extrude(t) stadium_c(2 * grid_pitch, grid_pitch);
            // two legs (±X)
            for (s = [-1, 1]) translate([s * 10.25, 0, t - 0.01]) linear_extrude(fz - t + 0.02) square([3.5, 7.6], center = true);
            // floor + socket
            translate([0, 0, fz]) linear_extrude(ft + sock) offset(r = wall_thickness) motor_section_y(c);
        }
        // socket pocket, floor hole (coupler passes through when fitting)
        translate([0, 0, fz + ft]) linear_extrude(sock + 1) motor_section_y(c);
        translate([0, 0, fz - 1]) cylinder(d = hub_d + 1, h = ft + 2);
        // wire exit slots in the socket rim
        for (s = [-1, 1]) translate([s * (motor_d / 2 + 1), 0, fz + ft + sock - 4]) cube([6, 5, 10], center = true);
        // shaft hole + mounting holes
        vhole(6, 20);
        for (p = [[20, 0], [-20, 0]]) translate([p[0], p[1], 0]) vhole(grid_hole_d, 20);
        // foot edge chamfer
        foot_chamfer(t);
    }
}
module stadium_c(half, w) { hull() { translate([-half, 0]) circle(d = w); translate([half, 0]) circle(d = w); } }
module foot_chamfer(t) {
    difference() {
        translate([-40, -40, t - 0.6]) cube([80, 80, 1]);
        translate([0, 0, t - 0.6]) linear_extrude(0.6, scale = 1) offset(delta = -0.6) stadium_c(2 * grid_pitch, grid_pitch);
        translate([0, 0, t - 0.7]) cylinder(r = 13, h = 2);
    }
}
