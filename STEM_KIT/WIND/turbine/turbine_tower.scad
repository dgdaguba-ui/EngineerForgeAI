// =====================================================================
//  PART: turbine tower segment — WIND/turbine
//  100 mm stackable C-channel (34 x 34 mm). Both flanges carry the 3 x 3
//  grid pattern (0, ±10); the top flange has nut pockets underneath,
//  reachable through the open side — so segments stack (M3 x 12), the
//  bottom bolts to a base plate (M3 x 12) and ANY common mount (motor
//  mount, bearing mount, axle mount) bolts on top (M3 x 10).
//  Print: standing, bottom flange on the bed. Top flange bridges 29 mm
//  between the side walls (no supports needed on a tuned printer).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

segment_h = 100;
turbine_tower(segment_h);

module turbine_tower(H = 100) {
    S = 34; w = wall_thickness; f = plate_thickness;
    difference() {
        union() {
            rbox([S, S, f], r = 3, top = 0.6);                         // bottom flange
            translate([0, 0, H - f]) rbox([S, S, f], r = 3, top = 0.8, bottom = 0);   // top flange
            // C-channel walls: back (−X) and two sides (±Y), open to +X
            translate([-S / 2, -S / 2, 0]) cube([w, S, H]);
            for (s = [-1, 1]) translate([-S / 2, s > 0 ? S / 2 - w : -S / 2, 0]) cube([S - 3, w, H]);
        }
        for (i = [-1 : 1], j = [-1 : 1]) translate([i * grid_pitch, j * grid_pitch, 0]) {
            vhole(grid_hole_d, 3 * H);
            translate([0, 0, H - f - 0.01]) nut_pocket();
        }
        // round the channel's open edges
        for (s = [-1, 1]) translate([S / 2 - 3, s * (S / 2), f]) rotate([0, 0, 0]) cylinder(r = 1.2, h = H - 2 * f, $fn = 12);
    }
}
