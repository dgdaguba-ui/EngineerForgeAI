// =====================================================================
//  PART: dynamo gearbox guard — DYNAMO/hand_generator
//  Finger guard for the hand-crank dynamo gearbox: an inverted U that
//  drops over the gearbox frame, closing the two open sides and the top
//  with a see-through diamond lattice (openings < 5 mm). Lips over the
//  frame plates' top edges locate it; the side walls stand on the table
//  next to the base plate. Gears stay visible; fingers stay out of the
//  pinch points.
//  Frame it fits: 100 x 100 plates, outer faces 60 mm apart.
//  Print: lying on one lip face (U cross-section on the bed) — the STL is
//  exported already in that orientation. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

// print orientation: lip face (y = -2.7) down on the bed
translate([0, 0, wall_thickness + 0.3]) rotate([90, 0, 0]) dynamo_gear_guard();

// guard coordinates = gearbox coordinates: plates occupy y 0..6 and
// 54..60, x 0..100, z 0..100 above the base plate top (z = 0).
module dynamo_gear_guard(S = plate_size, D = frame_gap + 2 * plate_thickness, t = wall_thickness) {
    c = 0.3;                        // clearance to the frame
    zt = S + c;                     // underside of the top wall
    lip_h = 10;
    base = -plate_thickness;        // side walls reach the table
    union() {
        // top wall (lattice), spans the full depth incl. lips
        translate([-c - t, -c - t, zt]) linear_extrude(t) lattice([S + 2 * c + 2 * t, D + 2 * c + 2 * t], margin = 5);
        // side walls (lattice) at x < 0 and x > S
        for (x0 = [-c - t, S + c]) translate([x0, -c - t, base]) rotate([90, 0, 90]) linear_extrude(t)
            lattice([D + 2 * c + 2 * t, zt + t - base], margin = 5);
        // lip down over plate A's outer face (this face lies on the bed when printing)
        translate([-c - t, -c - t, zt - lip_h]) cube([S + 2 * c + 2 * t, t, lip_h + t]);
        // plate B side: 45° wedge that hooks the plate's top edge (a full lip
        // here would be a 100 mm unsupported overhang in print orientation)
        translate([-c - t, D + c, zt]) rotate([90, 0, 90]) linear_extrude(S + 2 * c + 2 * t)
            polygon([[0, t], [t, t], [t, -t], [0, 0]]);
    }
}

// 2D lattice panel: solid border `margin`, diamond openings inside.
module lattice(size, margin = 5, p = 8, open_diag = 6.6) {
    difference() {
        offset(r = 1) offset(delta = -1) square(size);
        intersection() {
            translate([margin, margin]) square([size[0] - 2 * margin, size[1] - 2 * margin]);
            for (i = [0 : ceil(size[0] / p)], j = [0 : ceil(size[1] / p)])
                translate([i * p + ((j % 2) * p / 2), j * p / 2]) rotate(45) square(open_diag / sqrt(2), center = true);
        }
    }
}
