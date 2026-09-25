// =====================================================================
//  ASSEMBLY: Hand-crank dynamo (Kit 2) on the gearbox frame
//  ratio = 1 | 2 | 4 | 8  (generator turns per crank turn)
//   1 : 1  S0 10T(B) → G 10T(B)                      G at (45,35)
//   2 : 1  S0 20T(B) → G 10T(B)                      G at (45,25)
//   4 : 1  S0 40T(B) → G 10T(B)  (3-4-5 diagonal)    G at (75,15)
//   8 : 1  S0 20T(A) → S1 10T(A) | S1 20T(M) → S2 10T(M) | S2 20T(B) → G 10T(B)
//  Gearbox coordinates: x along the plates, y across (plate A outer face
//  y = 0, plate B outer face y = 60), z up from the base-plate top.
//  Shaft positions are grid holes (x, z) of the frame plates.
//  Gear levels (y): A teeth 14..20, M teeth 27.5..33.5, B teeth 38..44.
// =====================================================================
include <../PARAMETERS/config.scad>
use <asm_lib.scad>
use <../COMMON/mounts/base_plate.scad>
use <../COMMON/mounts/vertical_support.scad>
use <../COMMON/connectors/corner_connector.scad>
use <../COMMON/connectors/motor_coupler.scad>
use <../MECHANICAL/gearbox/gearbox_frame_plate.scad>
use <../DYNAMO/hand_generator/hand_crank.scad>
use <../DYNAMO/hand_generator/crank_knob.scad>
use <../DYNAMO/hand_generator/generator_mount.scad>
use <../DYNAMO/hand_generator/dynamo_gear_guard.scad>
use <../DYNAMO/hand_generator/output_panel.scad>

ratio = 8;
crank = 0;          // crank angle (deg, world)
only = "";
guard = true;

module item(name, col = "SteelBlue") {
    echo("ITEM", name);
    if (only == "" || only == name || (is_list(only) && len([for (o = only) if (o == name) 1]) > 0)) color(col) children();
}

GY = 20;  GZ = plate_thickness;          // gearbox origin in world
S0 = [45, 55];
G  = ratio == 1 ? [45, 35] : ratio == 4 ? [75, 15] : [45, 25];
S1 = [75, 55]; S2 = [75, 25];
yA = 20; yM = 33.5; yB = 38;             // gear y0 per level (see header)
function W(p) = [p[0], p[1] + GZ];        // gearbox (x,z) -> world (x,z)
gen_holes = ratio == 1 ? [[-20, 0], [20, 0]] : ratio == 4 ? [[-20, 0], [20, 0]] : [[0, -20], [0, 20]];

item("base_plate", "Gold") base_plate_asm();
module base_plate_asm() { grid_plate(10, 10); }

translate([0, GY, GZ]) {
    // ---- frame --------------------------------------------------------
    item("plate_A", "LightSteelBlue") translate([0, plate_thickness, 0]) rotate([90, 0, 0]) gearbox_frame_plate();
    item("plate_B", "LightSteelBlue") translate([0, 2 * plate_thickness + frame_gap, 0]) rotate([90, 0, 0]) gearbox_frame_plate();
    for (p = [[5, 5], [35, 5], [5, 95], [95, 95]])
        item(str("pillar_", p[0], "_", p[1]), "SteelBlue") translate([p[0], plate_thickness, p[1]]) rotate([-90, 0, 0]) vertical_support(frame_gap);
    for (x = [10, 90]) item(str("bracket_", x), "SteelBlue") translate([x, 0, 0]) corner_connector();

    // ---- gear train ---------------------------------------------------
    w0 = crank;
    if (ratio == 8) {
        w1 = -w0 * 20 / 10; w2 = -w1 * 20 / 10; wg = -w2 * 20 / 10;
        item("S0_20T_A", "Orange") gear_on_y(20, "fixed", S0, yA, 1, ["tooth", dir_xz(S0, S1)], w0);
        item("S1_10T_A", "Tomato") gear_on_y(10, "fixed", S1, yA, 1, ["space", dir_xz(S1, S0)], w1);
        item("S1_20T_M", "Orange") gear_on_y(20, "fixed", S1, yM, 1, ["tooth", dir_xz(S1, S2)], w1);
        item("S2_10T_M", "Tomato") gear_on_y(10, "fixed", S2, yM, 1, ["space", dir_xz(S2, S1)], w2);
        item("S2_20T_B", "Orange") gear_on_y(20, "fixed", S2, yB, -1, ["tooth", dir_xz(S2, G)], w2);
        item("G_10T_B", "Tomato") gear_on_y(10, "fixed", G, yB, -1, ["space", dir_xz(G, S2)], wg);
        item("shaft_S1", "Silver") steel_shaft_y(60, S1, 0);
        item("shaft_S2", "Silver") steel_shaft_y(60, S2, 0);
        echo("MESH", "S0_20T_A", "S1_10T_A", 20, 10, W(S0), W(S1), GY + yA - 3, "y");
        echo("MESH", "S1_20T_M", "S2_10T_M", 20, 10, W(S1), W(S2), GY + yM - 3, "y");
        echo("MESH", "S2_20T_B", "G_10T_B", 20, 10, W(S2), W(G), GY + yB + 3, "y");
    } else {
        zin = ratio == 1 ? 10 : ratio == 2 ? 20 : 40;
        item(str("S0_", zin, "T_B"), "Orange") gear_on_y(zin, "fixed", S0, yB, -1, ["tooth", dir_xz(S0, G)], w0);
        item("G_10T_B", "Tomato") gear_on_y(10, "fixed", G, yB, -1, ["space", dir_xz(G, S0)], -w0 * zin / 10);
        echo("MESH", str("S0_", zin, "T_B"), "G_10T_B", zin, 10, W(S0), W(G), GY + yB + 3, "y");
    }
    item("shaft_S0", "Silver") steel_shaft_y(80, S0, -22);

    // ---- crank (outside plate A) -------------------------------------
    item("crank", "Crimson") translate([S0[0], -20.5, S0[1]]) rotate([-90, 0, 0]) rotate(-crank) hand_crank();
    kx = S0[0] + 30 * cos(crank); kz = S0[1] + 30 * sin(crank);
    item("crank_knob", "Crimson") translate([kx, -20.5 - nut_thick, kz]) rotate([90, 0, 0]) crank_knob();

    // ---- generator on plate B ----------------------------------------
    yb = 2 * plate_thickness + frame_gap;              // plate B outer face (60)
    item("generator_mount", "SteelBlue") translate([G[0], yb, G[1]]) rotate([-90, 0, 0]) rotate(ratio == 1 || ratio == 4 ? 0 : 90) generator_mount();
    item("coupler", "Crimson") translate([G[0], yb + 5, G[1]]) rotate([-90, 0, 0]) motor_coupler();
    item("generator_motor", "Silver") translate([G[0], yb + 21.5 + motor_boss_h + motor_len / 2, G[1]])
        rotate([0, ratio == 1 || ratio == 4 ? 90 : 0, 0]) rotate([0, 0, 180]) motor_130();   // flats follow the mount
    item("shaft_G", "Silver") steel_shaft_y(40, G, yb + 5 + 7.2 - 40);
    echo("ALLOW", "generator_motor", "coupler", 3.0);  // press fit
    for (h = gen_holes) item(str("gen_nut_", h[0], "_", h[1]), "Black")
        translate([G[0] + h[0], plate_thickness + frame_gap - nut_thick, G[1] + h[1]]) rotate([-90, 0, 0]) m3_nut();

    // ---- guard --------------------------------------------------------
    if (guard) item("guard", "LightGreen") dynamo_gear_guard();
}
