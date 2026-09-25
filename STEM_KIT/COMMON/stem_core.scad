// =====================================================================
//  stem_core.scad — shared geometry helpers for every STEM_KIT part.
// =====================================================================
include <../PARAMETERS/config.scad>
// =====================================================================

// ---------- rounded / chamfered prisms --------------------------------

// Rounded rectangle (2D), centred.
module rrect(size, r) {
    rr = min(r, min(size[0], size[1]) / 2 - 0.01);
    offset(r = rr) square([size[0] - 2 * rr, size[1] - 2 * rr], center = true);
}

// Box with rounded vertical edges, chamfered bottom edge (elephant-foot
// relief) and rounded-ish (chamfered) top edge. Sits on z = 0, centred XY.
module rbox(size, r = 2, top = edge_r, bottom = chamfer) {
    h = size[2];
    hull() {
        linear_extrude(0.01) rrect([size[0] - 2 * bottom, size[1] - 2 * bottom], max(r - bottom, 0.1));
        translate([0, 0, bottom]) linear_extrude(h - bottom - top) rrect([size[0], size[1]], r);
        translate([0, 0, h - 0.01]) linear_extrude(0.01) rrect([size[0] - 2 * top, size[1] - 2 * top], max(r - top, 0.1));
    }
}

// Cylinder with chamfered/rounded top and bottom edges (safe hubs, knobs).
module rcyl(d, h, top = edge_r, bottom = chamfer) {
    rotate_extrude() polygon([
        [0, 0], [d / 2 - bottom, 0], [d / 2, bottom],
        [d / 2, h - top], [d / 2 - top, h], [0, h]
    ]);
}

// Stadium (slot / rounded bar) 2D between two points on the X axis.
module stadium2d(len, w) {
    hull() { circle(d = w); translate([len, 0]) circle(d = w); }
}

// ---------- holes ------------------------------------------------------

// Vertical through hole with small top/bottom chamfers.
module vhole(d = grid_hole_d, h = 50, ch = 0.4) {
    translate([0, 0, -h / 2]) cylinder(d = d, h = h);
}

// Horizontal hole along +Y, printable without supports (teardrop tip up).
module teardrop_y(d, len, center = true) {
    translate([0, center ? -len / 2 : 0, 0]) rotate([-90, 0, 0])
        linear_extrude(len) teardrop2d(d);
}
module teardrop_x(d, len, center = true) {
    translate([center ? -len / 2 : 0, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, -90])
        linear_extrude(len) teardrop2d(d);
}
// 2D teardrop: circle + 45° roof pointing "up" in the final part (+Z).
// After rotate([-90,0,0]) local +Y becomes -Z, so the roof points to -Y here.
module teardrop2d(d) {
    r = d / 2;
    union() {
        circle(d = d);
        polygon([[-r * sqrt(2) / 2, -r * sqrt(2) / 2], [0, -r * sqrt(2)], [r * sqrt(2) / 2, -r * sqrt(2) / 2]]);
    }
}

// Hex nut pocket (flat sides parallel to X), opening at z = 0 going +Z.
module nut_pocket(depth = nut_pocket_depth, af = nut_pocket_af) {
    cylinder(d = af / cos(30), h = depth, $fn = 6);
}

// Side-entry nut slot: nut plane is XY, slot opens toward +dir (X).
// Centred on the screw axis (Z), slot height nut_slot_t, runs out `len`.
module nut_slot_x(len = 10, af = nut_pocket_af, t = nut_slot_t) {
    translate([0, 0, -t / 2]) hull() {
        cylinder(d = af / cos(30), h = t, $fn = 6);
        translate([len, 0, 0]) cylinder(d = af / cos(30), h = t, $fn = 6);
    }
}

// Counterbored clearance hole from top surface at height `top` downward.
module cbore(top, depth, d = counterbore_d) {
    translate([0, 0, top - depth]) cylinder(d = d, h = depth + 20);
    translate([0, 0, -20]) cylinder(d = grid_hole_d, h = top + 40);
}

// Grid of vertical holes: nx x ny, pitch grid_pitch, first hole centred
// at `origin` (XY). Used by every plate.
module grid_holes(nx, ny, origin = [0, 0], h = 100, d = grid_hole_d) {
    for (i = [0 : nx - 1], j = [0 : ny - 1])
        translate([origin[0] + i * grid_pitch, origin[1] + j * grid_pitch, 0]) vhole(d, h);
}

// Slot (for adjustable mounting) along X, length = travel.
module slot_x(travel, d = grid_hole_d, h = 100) {
    translate([-travel / 2, 0, -h / 2]) linear_extrude(h) stadium2d(travel, d);
}

// ---------- shaft bores ------------------------------------------------

// 2D bore profile: round, or D if shaft_flat > 0.
module bore2d(d) {
    if (shaft_flat > 0)
        intersection() { circle(d = d); translate([-d, -d / 2]) square([2 * d, d - shaft_flat + (d - shaft_diameter) / 2]); }
    else circle(d = d);
}

// Standard HUB: cylinder hub_d x hub_h standing on z = z0, with bore,
// radial M3 set screw at mid height and a captive-nut slot from the top.
// Call inside difference() for the cut-outs: hub_body()/hub_cuts().
module hub_body(z0, d = hub_d, h = hub_h) {
    translate([0, 0, z0]) rcyl(d, h, top = 0.8, bottom = 0);
}
module hub_cuts(z0, total_h, d = hub_d, h = hub_h, bore = shaft_fixed_bore, set_screw = true, screw_angle = 0) {
    // bore through everything
    translate([0, 0, -1]) linear_extrude(total_h + 2) bore2d(bore);
    // entry chamfer on bore
    translate([0, 0, total_h - 0.6]) cylinder(d1 = bore, d2 = bore + 1.2, h = 0.61);
    translate([0, 0, -0.01]) cylinder(d1 = bore + 1.2, d2 = bore, h = 0.6);
    if (set_screw) rotate([0, 0, screw_angle]) {
        zs = z0 + h / 2;
        // radial screw hole (teardrop, prints without support)
        translate([0, 0, zs]) teardrop_x(screw_clear_d, d, center = false);
        // captive nut slot, entered from the hub top face
        nr = bore / 2 + (d / 2 - bore / 2) / 2;       // radial position of nut
        translate([nr - nut_slot_t / 2, -nut_pocket_af / 2, zs - nut_pocket_af / cos(30) / 2 - 0.1])
            cube([nut_slot_t, nut_pocket_af, total_h + 10]);   // open to the hub top face
    }
}

// ---------- labels -----------------------------------------------------

// Engrave text into a top surface at height z (depth 0.6 = 3 layers).
module engrave(txt, size = 5, z = 0, depth = 0.6, halign = "center") {
    translate([0, 0, z - depth]) linear_extrude(depth + 1)
        text(txt, size = size, font = "Liberation Sans:style=Bold", halign = halign, valign = "center");
}

// ---------- misc -------------------------------------------------------

function grid_snap(v) = ceil(v / grid_pitch) * grid_pitch;
