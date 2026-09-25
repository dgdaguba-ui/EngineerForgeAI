// =====================================================================
//  PART: motor mount (130-size DC motor, snap-in cradle) — COMMON/mounts
//  Motor axis along +Y at `axis_height`, over a grid line, so a motor
//  pinion meshes with any gear held by a bearing/axle mount on the grid.
//  The motor snaps in from above (flexing side walls), the flats stop it
//  turning, front/rear walls stop it sliding. Screws: M3 x 10 at (0, ±10)
//  — fit them BEFORE snapping the motor in.
//  slotted = true: holes become ±4 mm slots across the axis (used by the
//  solar vehicle mount to explore too-tight / too-loose gear mesh).
//  Print: standing on its floor. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../stem_core.scad>

slotted = false;
motor_mount(slotted);

// motor cross-section (flats vertical), grown by c
module motor_section(c = 0) {
    intersection() {
        circle(r = motor_d / 2 + c);
        square([motor_flat + 2 * c, motor_d + 4], center = true);
    }
}

function mm_front() = motor_len / 2 + tolerance;            // front wall inner face (Y)
function mm_front_outer() = mm_front() + min_wall;           // boss side face

module motor_mount(slotted = false, travel = 8) {
    h   = axis_height;
    c   = tolerance;
    wi  = motor_flat / 2 + c;                  // inner half width
    wo  = wi + wall_thickness;                 // outer half width
    yf  = mm_front();                          // front wall inner
    yr  = -yf;                                 // rear wall inner
    top = h + motor_d / 2 - 1.5 + 2.2;         // cradle top
    lip = 6.2;                                  // lip half-opening
    zfl = h - motor_d / 2 - c;                  // floor top (under motor)
    difference() {
        union() {
            // body: walls + floor, from rear wall to front wall
            translate([0, (yf + min_wall + yr - wall_thickness) / 2, 0])
                rbox([2 * wo, yf + min_wall - yr + wall_thickness, top], r = 1.5, top = 0.8);
        }
        // motor pocket + snap opening, through the full length between walls
        translate([0, yr, 0]) rotate([-90, 0, 0]) mirror([0, 1, 0]) linear_extrude(yf - yr)
            union() {
                translate([0, h]) motor_section(c);
                polygon([[-lip, h + 4], [lip, h + 4], [lip, top - 1.6], [lip + 2, top + 0.1],
                         [-lip - 2, top + 0.1], [-lip, top - 1.6]]);
            }
        // rear wall: keep only a low stop (below the axis) + zip-tie slot
        translate([-wo - 1, yr - wall_thickness - 1, h - 4]) cube([2 * wo + 2, wall_thickness + 1.01, top]);
        translate([-2, yr - wall_thickness - 1, zfl + 1.5]) cube([4, wall_thickness + 2, 2]);
        // front wall: U slot for the motor boss and shaft
        translate([0, yf - 1, h]) rotate([-90, 0, 0]) linear_extrude(min_wall + 2)
            hull() { circle(d = motor_boss_d + 0.6); translate([-(motor_boss_d + 0.6) / 2, -top]) square([motor_boss_d + 0.6, 1]); }
        // mounting holes / slots with counterbores under the motor
        for (y = [-grid_pitch, grid_pitch]) translate([0, y, 0]) {
            if (slotted) {
                slot_x(travel, grid_hole_d, 40);
                translate([0, 0, foot_thickness]) hull() for (x = [-travel / 2, travel / 2])
                    translate([x, 0, 0]) cylinder(d = counterbore_d, h = zfl - foot_thickness + 1);
            } else {
                vhole(grid_hole_d, 40);
                translate([0, 0, foot_thickness]) cylinder(d = counterbore_d, h = zfl - foot_thickness + 1);
            }
        }
        if (slotted) translate([0, yf + min_wall, top - 5]) rotate([-90, 0, 0])
            translate([0, 0, -0.5]) linear_extrude(1) text("V", size = 4, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
    }
}
