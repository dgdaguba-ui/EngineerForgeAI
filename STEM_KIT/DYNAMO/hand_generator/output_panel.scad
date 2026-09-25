// =====================================================================
//  PART: generator output panel — DYNAMO/hand_generator
//  Where the electricity goes: 3 x 5 mm LED holes, a Ø12 buzzer hole,
//  and rows of zip-tie slot pairs + M3 slots that hold ANY capacitor,
//  voltmeter module, battery/charger board or terminal block without
//  hard-coding their sizes. Bolts to the grid at its 4 corner holes.
//  Print: flat. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>

output_panel();

module output_panel(W = 80, D = 60, t = foot_thickness) {
    difference() {
        translate([W / 2, D / 2, 0]) rbox([W, D, t], r = 3, top = 0.8);
        // grid mounting holes (corners)
        for (x = [5, W - 5], y = [5, D - 5]) translate([x, y, 0]) vhole(grid_hole_d, 20);
        // LEDs (+ one extra hole for a bi-colour LED) and buzzer
        for (i = [0 : 2]) translate([15 + i * 10, D - 13, 0]) vhole(led_hole_d, 20);
        translate([W - 18, D - 15, 0]) vhole(buzzer_hole_d, 20);
        // two rows of zip-tie slot pairs (capacitor, battery module, meter)
        for (row = [0 : 1], k = [0 : 2]) translate([15 + k * 22, 12 + row * 14, 0])
            for (dx = [-5, 5]) translate([dx, 0, 0]) cube([1.8, 4.2, 20], center = true);
        // M3 adjustable slots for small PCBs / terminal blocks
        for (y = [12, 26]) translate([W - 12, y, 0]) rotate(90) slot_x(8, grid_hole_d, 20);
        // labels
        translate([25, D - 5.5, 0]) engrave("LED", size = 3.2, z = t);
        translate([W - 18, D - 5, 0]) engrave("BUZZ", size = 3, z = t);
        translate([W - 12, 4.5, 0]) engrave("+  -", size = 3, z = t);
    }
}
