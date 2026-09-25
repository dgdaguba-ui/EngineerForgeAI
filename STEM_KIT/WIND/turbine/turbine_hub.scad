// =====================================================================
//  PART: wind turbine hub — WIND/turbine
//  blades = 2 | 3 | 4 sockets. Each socket takes a blade root peg; the
//  blade can be TWISTED in its socket to change pitch (tick marks every
//  15° around each socket), then locked with an M3 x 8 screw from the
//  top (self-taps into the Ø2.6 hole). Standard set-screw hub on top →
//  mounts on any 3 mm shaft (motor_coupler → 3 mm stub → hub).
//  Print: flat, hub up. No supports (truncated-teardrop sockets).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

blades = 3;
turbine_hub(blades);

th_R = 22;          // hub disc radius
th_T = 14;          // hub disc thickness
th_peg_d = 8;       // blade root peg diameter
th_depth = 12;      // socket depth
function th_socket_z() = th_T / 2;

module turbine_hub(n) {
    zc = th_socket_z();
    sd = th_peg_d + 0.4;
    total_h = th_T + hub_h;
    difference() {
        union() {
            rcyl(2 * th_R, th_T, top = 1.2, bottom = chamfer);
            hub_body(th_T - 0.01, hub_d, hub_h + 0.01);
        }
        hub_cuts(th_T, total_h, hub_d, hub_h);
        for (k = [0 : n - 1]) rotate(k * 360 / n) {
            // socket (radial, along +X), truncated teardrop
            translate([th_R - th_depth, 0, zc]) rotate([0, 90, 0]) rotate([0, 0, -90])
                linear_extrude(th_depth + 1) intersection() {
                    union() { circle(d = sd); polygon([[-sd / 2 * 0.7071, -sd / 2 * 0.7071], [0, -sd / 2 * 1.4142], [sd / 2 * 0.7071, -sd / 2 * 0.7071]]); }
                    translate([-sd, -sd / 2 - 0.9]) square([2 * sd, 2 * sd]);
                }
            // pitch lock screw (self-tapping) from the top
            translate([th_R - th_depth / 2, 0, zc]) cylinder(d = screw_tap_d, h = th_T);
            // pitch ticks around the socket mouth (every 15°, long at 0°)
            for (a = [-45 : 15 : 45]) translate([th_R, 0, zc]) rotate([a, 0, 0])
                translate([-0.5, -0.3, sd / 2 + 0.6]) cube([1, 0.6, a == 0 ? 2.4 : 1.4]);
        }
        // blade-count label on the hub face
        rotate(180 / n) translate([th_R - 7.5, 0, 0]) rotate(90) engrave(str(n), size = 4, z = th_T);
    }
}
