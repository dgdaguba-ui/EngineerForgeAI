// =====================================================================
//  PART: solar vehicle motor mount — SOLAR/vehicle
//  The common snap-in 130-motor cradle with its screw holes turned into
//  ±4 mm slots across the motor axis. On the grid the motor sits at the
//  exact gear centre distance; the slots let children deliberately make
//  the mesh too loose (gears skip) or too tight (motor stalls) and see
//  why the grid position is right. Marked "V" on the front wall.
//  Print: standing on its floor. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/mounts/motor_mount.scad>

motor_mount(slotted = true);
