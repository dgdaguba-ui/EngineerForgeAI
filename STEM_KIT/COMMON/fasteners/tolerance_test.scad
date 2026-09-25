// =====================================================================
//  PART: STEM_TOLERANCE_TEST — COMMON/fasteners
//  Print this FIRST. It tells you which clearances YOUR printer needs.
//   A  Hole plate: vertical holes 2.8 / 3.0 / 3.2 / 3.4 / 3.6 mm and the
//      same five as horizontal teardrop holes in the wall behind them,
//      plus M3 nut pockets 5.6 / 5.85 / 6.1 mm across flats.
//   B  Pin comb: 3 mm pins (the kit shaft size) + 2.8 … 3.6 mm pins.
//   C  Snap-fit test: three hooks (0.4 / 0.6 / 0.8 mm interference) and a
//      matching slotted receiver.
//  How to use: see DOCUMENTATION/assembly/00_tolerance_test.md
//  Print: all flat as laid out. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

holes = [2.8, 3.0, 3.2, 3.4, 3.6];
nuts  = [5.6, 5.85, 6.1];
snaps = [0.4, 0.6, 0.8];

tolerance_test();

module tolerance_test() {
    hole_plate();
    translate([0, -22, 0]) pin_comb();
    translate([0, -46, 0]) snap_receiver();
    for (i = [0 : 2]) translate([i * 34, -62, 0]) snap_hook(snaps[i]);
}

module label(txt, size = 2.6) {
    linear_extrude(0.6) text(txt, size = size, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
}

module hole_plate() {
    difference() {
        union() {
            translate([37.5, 7.5, 0]) rbox([75, 15, 4], r = 2, top = 0.6);
            translate([37.5, 17.5, 0]) rbox([75, 5, 12], r = 1, top = 0.6);  // wall for horizontal holes
            translate([88, 10, 0]) rbox([28, 20, 4], r = 2, top = 0.6);     // nut pocket block
        }
        for (i = [0 : 4]) {
            translate([8 + i * 14, 6, 0]) vhole(holes[i], 20);
            translate([8 + i * 14, 17.5, 8]) teardrop_y(holes[i], 10);
        }
        for (i = [0 : 2]) translate([81 + i * 9, 10, 1.2]) {
            cylinder(d = nuts[i] / cos(30), h = 10, $fn = 6);
            vhole(grid_hole_d, 20);
        }
    }
    for (i = [0 : 4]) translate([8 + i * 14, 12.2, 3.99]) label(str(holes[i]), 2.4);
    for (i = [0 : 2]) translate([81 + i * 9, 3.2, 3.99]) label(str(nuts[i]), 1.9);
}

module pin_comb() {
    pins = concat([3.0], holes);
    translate([45, 7, 0]) rbox([92, 14, 3], r = 2, top = 0.5);
    for (i = [0 : len(pins) - 1]) translate([7 + i * 15.2, 4, 2.99]) {
        cylinder(d = pins[i], h = 12.01);
        translate([0, 0, 12]) cylinder(d1 = pins[i], d2 = pins[i] - 0.8, h = 0.4);
    }
    for (i = [0 : len(pins) - 1]) translate([7 + i * 15.2, 10.8, 2.99]) label(i == 0 ? "S3" : str(pins[i]), 2.2);
}

// receiver: 3 rectangular windows 6 x 4 in a 3 mm wall
module snap_receiver() {
    difference() {
        translate([33, 9, 0]) rbox([66, 18, 3], r = 2, top = 0.5);
        for (i = [0 : 2]) translate([11 + i * 22, 6, 0]) cube([6.4, 4.4, 20], center = true);
    }
    for (i = [0 : 2]) translate([11 + i * 22, 14, 2.99]) label(str(snaps[i]), 2.4);
}

// cantilever hook printed flat: beam 1.6 thick, 14 long, catch = interference
module snap_hook(i) {
    translate([0, 0, 0]) {
        translate([0, 0, 0]) cube([16, 12, 3]);                 // handle
        translate([16 - 0.01, 3.9, 0]) cube([12, 6, 1.6]);      // beam (flexes)
        translate([28 - 0.01, 3.9, 0]) linear_extrude(1.6 + i)   // catch ramp
            polygon([[0, 0], [3, 0], [3, 6], [0, 6]]);
        translate([28 - 0.01, 3.9, 1.6]) rotate([90, 0, 0]) translate([0, 0, -6]) linear_extrude(6)
            polygon([[0, 0], [3, 0], [0, i]]);
    }
}
