// =====================================================================
//  STEM_KIT — CENTRAL PARAMETER FILE  ("ForgeGrid" mechanical standard)
// ---------------------------------------------------------------------
//  Every part in the library includes this file. Change a value here,
//  run `python3 tools/build.py`, and the whole library regenerates.
//  All dimensions in millimetres.
// =====================================================================

// ---------------------------------------------------------------------
// 1. PRINTER / PROCESS
// ---------------------------------------------------------------------
nozzle          = 0.4;
layer_height    = 0.2;
tolerance       = 0.2;    // sliding clearance per side (tune with STEM_TOLERANCE_TEST)
press_allow     = 0.05;   // extra for press fits (bores that should grip)
min_wall        = 1.6;    // never go below this
wall_thickness  = 2.4;    // preferred wall (6 perimeters @ 0.4)
edge_r          = 1.0;    // rounding of exposed edges (child safety)
chamfer         = 0.6;    // bottom-edge chamfer (elephant-foot relief)

$fa = 6;                  // facet angle
$fs = 0.4;                // facet size

// ---------------------------------------------------------------------
// 2. GRID  (the heart of the ecosystem)
// ---------------------------------------------------------------------
//  Holes sit on a 10 mm lattice, 5 mm in from every plate edge, so
//  plates placed side by side keep one continuous lattice.
grid_pitch            = 10;
plate_size            = 100;   // universal base plate (square)
plate_thickness       = 6;     // base plates, rails, chassis
foot_thickness        = 4;     // flange / foot of every mount
//  => standard joint: 4 mm foot + 6 mm plate = M3 x 10 screw, nut in
//     the hex pocket under the plate. One screw length does 90 % of joints.

// ---------------------------------------------------------------------
// 3. FASTENERS (M3 everywhere: one screwdriver, one nut)
// ---------------------------------------------------------------------
screw_size            = 3;
screw_clear_d         = 3.4;   // clearance hole (also the grid hole)
grid_hole_d           = screw_clear_d;
screw_tap_d           = 2.6;   // hole a screw self-taps into
screw_head_d          = 5.7;   // ISO 7380 BUTTON head = kit standard (low, rounded, child-safe)
screw_head_h          = 1.65;
counterbore_d         = 6.4;
nut_af                = 5.5;   // M3 nut across flats
nut_thick             = 2.4;
nut_pocket_af         = nut_af + 0.35;
nut_pocket_depth      = 3.0;   // pocket under plates (nut sits flush)
nut_slot_t            = nut_thick + 0.4;  // side-entry slot thickness
set_screw_len         = 6;     // M3 x 6 grub screw for hubs

// ---------------------------------------------------------------------
// 4. SHAFTS
// ---------------------------------------------------------------------
//  Default: 3 mm steel rod (silver steel / stainless). Printed shafts
//  are provided for light-duty use. Alternative systems: set
//  shaft_diameter = 4 or 5 and rebuild.
shaft_diameter        = 3;
shaft_flat            = 0;     // >0 : D-shaft, flat depth (e.g. 0.5)
shaft_fixed_bore      = shaft_diameter + 0.15;  // hub bore (set-screw locked)
shaft_free_bore       = shaft_diameter + 0.4;   // free-spinning bore / bushing
shaft_lengths         = [40, 60, 80, 100, 120];

//  Horizontal shafts: all pillow blocks, motor mounts and axle mounts
//  put their axis at this height above the surface they are bolted to,
//  so any two of them on the grid are automatically coaxial/parallel.
axis_height           = 17;
axis_height_high      = 37;    // = axis_height + 2 pitches (pulleys, big wheels)

// ---------------------------------------------------------------------
// 5. BEARINGS
// ---------------------------------------------------------------------
bearing_size          = [5, 16, 5];   // 625 : bore, OD, width (default housing)
bearing_small         = [3, 10, 4];   // 623 : fits 3 mm shafts via adapter ring
bearing_pocket_d      = bearing_size[1] + 0.15;

// ---------------------------------------------------------------------
// 6. GEARS
// ---------------------------------------------------------------------
//  Module 2 + tooth counts that are multiples of 10  =>  centre distance
//  = (z1+z2) mm is ALWAYS a multiple of 10  =>  ANY two gears mesh when
//  their shafts sit in grid holes. (3-4-5 diagonals also work: 50 mm.)
gear_module           = 2;
gear_pressure_angle   = 20;
gear_width            = 6;
gear_backlash         = 0.30;  // total circular backlash per mesh
gear_clearance_k      = 0.25;  // root clearance = k * module
gear_teeth_set        = [10, 20, 30, 40];
//  Gearbox frame: two frame plates, outer faces 60 mm apart (on grid),
//  48 mm gap = three gear levels (A, M, B).
frame_gap             = 48;
hub_d                 = 14;
hub_h                 = 7;

// ---------------------------------------------------------------------
// 7. WHEELS / PULLEYS
// ---------------------------------------------------------------------
wheel_diameter        = 60;
wheel_width           = 10;
axle_diameter         = shaft_diameter;
oring_cs              = 3.0;    // O-ring cross-section used as tyre / belt
belt_cs               = 2.5;    // O-ring / round-belt cord for pulleys
pulley_sizes          = [20, 40, 60];  // effective (belt-line) diameters

// ---------------------------------------------------------------------
// 8. MOTORS (130-size toy / solar motor is the default)
// ---------------------------------------------------------------------
motor_size            = [20.2, 15.2, 25.2]; // body dia, across-flats, length
motor_d               = motor_size[0];
motor_flat            = motor_size[1];
motor_len             = motor_size[2];
motor_boss_d          = 6.2;
motor_boss_h          = 1.6;
motor_shaft_d         = 2.0;
motor_shaft_len       = 8.5;   // beyond boss
motor_shaft_bore      = 1.9;   // press fit onto 2 mm motor shaft

// ---------------------------------------------------------------------
// 9. SOLAR PANEL (bought, not printed) — frame is parametric
// ---------------------------------------------------------------------
solar_panel_size      = [110, 69, 3.0];  // 5 V 1 W epoxy panel (common)
solar_panel_clear     = 0.6;

// ---------------------------------------------------------------------
// 10. ELECTRONICS
// ---------------------------------------------------------------------
mounting_hole_spacing = grid_pitch;   // everything bolts to the grid
electronics_slot_w    = screw_clear_d;
led_hole_d            = 5.1;
buzzer_hole_d         = 12.2;

// ---------------------------------------------------------------------
// 11. SAFETY LIMITS (checked by tools/qc.py)
// ---------------------------------------------------------------------
max_part_voltage      = 12;    // nothing in this kit uses more
min_rim_thickness     = 2.0;   // blades/links: no edge thinner than this
finger_gap_max        = 6;     // guard openings smaller than a child's finger
