// =====================================================================
//  PART: belt pulley mount (tensioner) — MECHANICAL/pulley
//  Tall axle mount (axis at axis_height_high = 37 mm, so a Ø60 pulley
//  clears the plate) with 20 mm slots across the shaft: slide it to
//  tension the belt, lock with thumb nuts under the plate or M3 x 10.
//  Same module as the common axle mount — just different parameters.
//  Print: standing on its foot. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/mounts/axle_mount.scad>

axle_mount(axis_height_high, 2 * grid_pitch);
