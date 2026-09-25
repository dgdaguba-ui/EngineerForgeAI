// =====================================================================
//  ASSEMBLY: Pulley & belt lab (Kit 8, MVP subset)
//  Motor → coupler → shaft in a bearing mount (printed bushing insert)
//  + axle mount → Ø20 pulley  ==O-ring belt==>  Ø60 pulley on a shaft
//  held by two slotted belt-pulley mounts (axis 37 mm) = 3 : 1 reduction.
//  Slide the belt mounts along their slots to tension the belt.
// =====================================================================
include <../PARAMETERS/config.scad>
use <asm_lib.scad>
use <../COMMON/mounts/base_plate.scad>
use <../COMMON/mounts/motor_mount.scad>
use <../COMMON/mounts/axle_mount.scad>
use <../COMMON/bearings/bearing_mount.scad>
use <../COMMON/bearings/bearing_insert.scad>
use <../COMMON/connectors/motor_coupler.scad>
use <../MECHANICAL/pulley/pulley.scad>

driver = 20;
driven = 60;
only = "";

module item(name, col = "SteelBlue") {
    echo("ITEM", name);
    if (only == "" || only == name || (is_list(only) && len([for (o = only) if (o == name) 1]) > 0)) color(col) children();
}

T = plate_thickness;
Z1 = T + axis_height;       Z2 = T + axis_height_high;
X1 = 15;                    X2 = 75;
yb = 15 + motor_len / 2 + motor_boss_h;          // motor boss face
yc = yb + 0.5 + 16;
yp = 78;                                          // pulley front faces

item("base_plate", "Gold") grid_plate(10, 10);
item("motor_mount", "SteelBlue") translate([X1, 15, T]) motor_mount(false);
item("motor", "Silver") translate([X1, 15, Z1]) motor_130();
item("coupler", "Crimson") translate([X1, yc, Z1]) rotate([90, 0, 0]) motor_coupler();
echo("ALLOW", "motor", "coupler", 3.0);
item("bearing_mount", "SteelBlue") translate([X1, 55, T]) bearing_mount();
item("bushing", "Orange") translate([X1, 55 + 4 - bearing_size[2] - 0.1, Z1]) rotate([-90, 0, 0]) bearing_insert("bushing");
item("axle_mount", "SteelBlue") translate([X1, 85, T]) axle_mount();
item("shaft_1", "Silver") steel_shaft_y(60, [X1, Z1], yc - 7.2);
item("pulley_driver", "Tomato") translate([X1, yp, Z1]) rotate([90, 0, 0]) pulley(driver);
for (y = [25, 85]) item(str("belt_mount_", y), "SteelBlue") translate([X2, y, T]) axle_mount(axis_height_high, 2 * grid_pitch);
item("shaft_2", "Silver") steel_shaft_y(80, [X2, Z2], 15);
item("pulley_driven", "Tomato") translate([X2, yp, Z2]) rotate([90, 0, 0]) pulley(driven);
// belt centre-line length (for choosing the O-ring)
Cd = norm([X2 - X1, Z2 - Z1]);
echo("BELT_LENGTH", 2 * Cd + PI * (driver + driven) / 2 + pow(driven - driver, 2) / (4 * Cd));
