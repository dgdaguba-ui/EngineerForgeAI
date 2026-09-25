// =====================================================================
//  ASSEMBLY: Wind turbine (Kit 5), direct drive
//  base plate → 2 tower segments → common motor mount (generator) →
//  motor coupler → 3 mm stub shaft → hub → 2/3/4 blades.
//  blades = 2|3|4, style = "standard"|"torque"|"speed", pitch = deg.
// =====================================================================
include <../PARAMETERS/config.scad>
use <asm_lib.scad>
use <../COMMON/mounts/base_plate.scad>
use <../COMMON/mounts/motor_mount.scad>
use <../COMMON/connectors/motor_coupler.scad>
use <../WIND/turbine/turbine_tower.scad>
use <../WIND/turbine/turbine_hub.scad>
use <../WIND/turbine/turbine_blade.scad>

blades = 3;
style = "standard";
pitch = 20;
rotor = 0;
only = "";

module item(name, col = "SteelBlue") {
    echo("ITEM", name);
    if (only == "" || only == name || (is_list(only) && len([for (o = only) if (o == name) 1]) > 0)) color(col) children();
}

T = plate_thickness;
C = [45, 45];                                   // tower centre = grid hole
H = 100;                                        // segment height
top = T + 2 * H;
AZ = top + axis_height;
yb = C[1] + motor_len / 2 + motor_boss_h;       // boss face
yc = yb + 0.5 + 16;                             // coupler 3 mm-side face
ys = yc - 7.2;                                  // stub shaft start
yh = ys + 40;                                   // hub front face = shaft end

item("base_plate", "Gold") grid_plate(10, 10);
item("tower_1", "LightSteelBlue") translate([C[0], C[1], T]) turbine_tower(H);
item("tower_2", "LightSteelBlue") translate([C[0], C[1], T + H]) turbine_tower(H);
item("motor_mount", "SteelBlue") translate([C[0], C[1], top]) motor_mount(false);
item("generator_motor", "Silver") translate([C[0], C[1], AZ]) motor_130();
item("coupler", "Crimson") translate([C[0], yc, AZ]) rotate([90, 0, 0]) motor_coupler();
item("stub_shaft", "Silver") steel_shaft_y(40, [C[0], AZ], ys);
echo("ALLOW", "generator_motor", "coupler", 3.0);
translate([C[0], yh, AZ]) rotate([90, 0, 0]) rotate(rotor) {
    item("hub", "Orange") turbine_hub(blades);
    for (k = [0 : blades - 1]) item(str("blade_", k), "White")
        rotate(k * 360 / blades) translate([10, 0, 7]) rotate([pitch, 0, 0]) translate([0, 0, -2.5]) turbine_blade(style);
}
