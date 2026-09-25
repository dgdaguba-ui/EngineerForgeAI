// =====================================================================
//  PART: belt pulley — MECHANICAL/pulley
//  Round-belt pulley for an O-ring / elastic band belt (2.5 mm cord).
//  size = effective (belt-line) diameter: 20 | 40 | 60 mm.
//  Standard set-screw hub; 40 & 60 have coupling holes (bolt to gears,
//  wheels) so a pulley+gear compound can be built.
//  Print: flat, hub up. No supports (45° groove flanks).
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

size = 40;
pulley(size);

module pulley(D) {
    cs = belt_cs;
    Rb = D / 2;                  // belt centre-line radius
    Rg = Rb - cs / 2;            // groove bottom radius
    Rf = Rb + cs / 2 + 1.2;      // flange radius
    W  = 2 * (Rf - Rg) + 2.8;    // pulley width: keeps both groove flanks at 45°
    total_h = W + hub_h;
    difference() {
        union() {
            rotate_extrude($fn = 120) polygon([
                [0, 0], [Rf - 0.5, 0], [Rf, 0.5], [Rf, 1.2],
                [Rg, W / 2 - 0.2], [Rg, W / 2 + 0.2],
                [Rf, W - 1.2], [Rf, W - 0.5], [Rf - 0.5, W], [0, W]]);
            hub_body(W - 0.01, hub_d, hub_h + 0.01);
        }
        hub_cuts(W, total_h, hub_d, hub_h);
        if (D >= 40) for (a = [0 : 90 : 270]) rotate(a) translate([grid_pitch, 0, 0]) vhole(grid_hole_d, 40);
        if (D >= 60) for (k = [0 : 3]) rotate(45 + k * 90) translate([(hub_d / 2 + Rg) / 2 + 2, 0, -1]) cylinder(d = Rg - hub_d / 2 - 12, h = W + 2);
        // size label on the top face
        if (D >= 40) rotate(45) translate([(Rg + hub_d / 2) / 2 + (D >= 60 ? -3 : 1), 0, 0]) rotate(-45 + 90 - 45)
            engrave(str(D), size = 3.5, z = W);
    }
}
