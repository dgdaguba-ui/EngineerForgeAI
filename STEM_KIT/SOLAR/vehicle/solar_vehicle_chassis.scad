// =====================================================================
//  PART: solar vehicle chassis — SOLAR/vehicle
//  170 x 80 x 6 mm grid plate (17 x 8 holes, nut pockets under every
//  hole) — a stretched base plate, so every common mount bolts on.
//  A centre gear slot lets Ø44 (20T) gears on the axle/motor pass
//  below the deck. Reference layout (see ASSEMBLIES/solar_vehicle.scad):
//    rear axle x = 45, front axle x = 145, motor at x = 75 (CD 30) or
//    x = 65 (CD 20); second motor (version D) at x = 15.
//  Print: flat, pockets down. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/stem_core.scad>
use <../../COMMON/mounts/base_plate.scad>

chassis_nx = 17;
chassis_ny = 8;
slot_x = [20, 100];                 // gear slot along the chassis (X)
slot_y = [-1, 10.5];                // relative to chassis centre line

solar_vehicle_chassis();

module solar_vehicle_chassis() {
    W = chassis_ny * grid_pitch;
    difference() {
        grid_plate(chassis_nx, chassis_ny, skip = [for (i = [0 : chassis_nx - 1]) let(x = 5 + 10 * i)
                     if (x > slot_x[0] - 4 && x < slot_x[1] + 4) [i, chassis_ny / 2]]);
        translate([slot_x[0], W / 2 + slot_y[0], -1]) linear_extrude(plate_thickness + 2)
            offset(r = 2) offset(delta = -2) square([slot_x[1] - slot_x[0], slot_y[1] - slot_y[0]]);
        // direction arrow + axle markers engraved on the deck
        translate([160, W / 2, plate_thickness]) engrave_arrow();
        for (x = [45, 145]) translate([x, 2, plate_thickness - 0.6]) cylinder(d = 2, h = 1, $fn = 12);
    }
}
module engrave_arrow() {
    translate([0, 0, -0.6]) linear_extrude(1) polygon([[4, 0], [-3, 4], [-1.5, 0], [-3, -4]]);
}
