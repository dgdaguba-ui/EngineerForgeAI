// =====================================================================
//  ASSEMBLY: Solar vehicle (Kit 4) — versions A / B / C / D
//   A  1 : 1   motor 10T → axle 10T       (motor at x = 65, CD 20)
//   B  2 : 1   motor 10T → axle 20T       (motor at x = 75, CD 30) reduction
//   C  1 : 2   motor 20T → axle 10T       (motor at x = 75, CD 30) overdrive
//   D  2 : 1 x two motors (x = 75 and x = 15) on the same 20T axle gear
//  World: chassis corner at origin, chassis top z = 6, centre line y = 40.
//  Render one item:  openscad -D 'version="B"' -D 'only="motor1"' ...
// =====================================================================
include <../PARAMETERS/config.scad>
use <asm_lib.scad>
use <../COMMON/gears/spur_gear.scad>
use <../COMMON/mounts/axle_mount.scad>
use <../COMMON/mounts/motor_mount.scad>
use <../COMMON/mounts/vertical_support.scad>
use <../COMMON/mounts/solar_panel_mount.scad>
use <../COMMON/wheels/wheel.scad>
use <../SOLAR/vehicle/solar_vehicle_chassis.scad>

version = "B";
only = "";
wheel_rot = 0;          // animation: rear axle rotation (deg)

module item(name, col = "SteelBlue") {
    echo("ITEM", name);
    if (only == "" || only == name || (is_list(only) && len([for (o = only) if (o == name) 1]) > 0)) color(col) children();
}

T  = plate_thickness;                   // chassis top
CY = 40;                                // centre line
AZ = T + axis_height;                   // axle height (world z)
XR = 45; XF = 145;                      // axles
y_teeth = CY + 7.9;                     // gear tooth face (hub toward -Y)

m1x = version == "A" ? 65 : 75;
z_axle  = version == "B" || version == "D" ? 20 : 10;
z_motor = version == "C" ? 20 : 10;
ratio = z_axle / z_motor;               // motor turns per axle turn

item("chassis", "Gold") solar_vehicle_chassis();
for (s = [-1, 1]) {
    item(str("rear_axle_mount_", s), "SteelBlue") translate([XR, CY + s * 25, T]) axle_mount();
    item(str("front_axle_mount_", s), "SteelBlue") translate([XF, CY + s * 25, T]) axle_mount();
}
item("rear_axle", "Silver") steel_shaft_y(120, [XR, AZ], CY - 60);
item("front_axle", "Silver") steel_shaft_y(120, [XF, AZ], CY - 60);
for (x = [XR, XF]) {
    item(str("wheel_L_", x), "DimGray") translate([x, -18, AZ]) rotate([-90, 0, 0]) rotate(wheel_rot) wheel(wheel_diameter, wheel_width, "spoke");
    item(str("wheel_R_", x), "DimGray") translate([x, 98, AZ]) rotate([90, 0, 0]) rotate(wheel_rot) wheel(wheel_diameter, wheel_width, "spoke");
}
// axle gear (space toward the motor), motor gear (tooth toward the axle)
item("axle_gear", "Orange")
    gear_on_y(z_axle, "fixed", [XR, AZ], y_teeth, 1, ["space", dir_xz([XR, AZ], [m1x, AZ])], wheel_rot);
module motor_unit(mx, idx) {
    item(str("motor_mount", idx), "SteelBlue") translate([mx, CY - 15, T]) motor_mount(true);
    item(str("motor", idx), "Silver") translate([mx, CY - 15, AZ]) motor_130();
    d = dir_xz([mx, AZ], [XR, AZ]);
    item(str("pinion", idx), "Tomato")
        gear_on_y(z_motor, "motor", [mx, AZ], y_teeth, 1, ["tooth", d], -wheel_rot * ratio);
    echo("MESH", str("pinion", idx), "axle_gear", z_motor, z_axle, [mx, AZ], [XR, AZ], y_teeth - 3, "y");
    echo("ALLOW", str("motor", idx), str("pinion", idx), 3.0);   // press fit (bore 1.9 on 2.0 shaft)
}
motor_unit(m1x, 1);
if (version == "D") motor_unit(15, 2);

// solar panel on four 48 mm pillars
PZ = T + frame_gap;
pillars = [[65, 55], [125, 55], [95, 25], [125, 25]];
for (i = [0 : 3]) item(str("pillar", i), "LightSteelBlue") translate([pillars[i][0], pillars[i][1], T]) vertical_support(frame_gap);
item("panel_frame", "RoyalBlue") translate([90, CY, PZ]) solar_panel_frame();
item("solar_panel", "MidnightBlue") translate([90 - solar_panel_size[0] / 2, CY - solar_panel_size[1] / 2, PZ + 4]) solar_panel();
