// =====================================================================
//  PART: solar vehicle wheel — SOLAR/vehicle
//  Lightweight 5-spoke version of the common Ø60 wheel (same hub, same
//  O-ring tyre, same coupling holes). Low mass = less energy wasted
//  getting a weak solar motor moving.
//  Print: flat, hub up. No supports.
// =====================================================================
include <../../PARAMETERS/config.scad>
use <../../COMMON/wheels/wheel.scad>

wheel(wheel_diameter, wheel_width, "spoke");
