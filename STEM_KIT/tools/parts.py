"""STEM_KIT part catalogue — single source of truth for every STL.

Each entry: id (= STL file name), source .scad, -D defines, STL folder,
human name, kits it belongs to, print orientation, infill, supports,
material, quantity per kit, and a one-line purpose.
tools/build.py renders them; tools/qc.py measures + checks them and
writes DOCUMENTATION/PARTS.md from this table + the measured geometry.
"""

PLA = "PLA or PETG"
PETG = "PETG preferred (PLA ok)"

# orientation text, infill, supports
FLAT = "Flat on the largest face as modelled (z = 0 on the bed)"


def P(id, src, stl, name, purpose, orient=FLAT, infill="20 %", supports="None", material=PLA, defines=(), qty=None, kit="common"):
    return dict(id=id, src=src, stl=stl, name=name, purpose=purpose, orient=orient, infill=infill,
                supports=supports, material=material, defines=list(defines), qty=qty or {}, kit=kit)


PARTS = [
    # ------------------------------------------------------------------ COMMON
    P("STEM_TOLERANCE_TEST", "COMMON/fasteners/tolerance_test.scad", "common", "Tolerance & snap-fit test",
      "Calibrate hole, shaft, nut-pocket and snap-fit clearances for YOUR printer. Print first.",
      infill="20 %"),
    P("base_plate_100", "COMMON/mounts/base_plate.scad", "common", "Universal base plate 100x100",
      "The grid everything bolts to: 10x10 M3 holes, 10 mm pitch, nut pockets underneath.",
      orient="Flat, nut pockets DOWN", infill="20 %"),
    P("rail_10", "COMMON/connectors/rail.scad", "common", "Rail 1x10 (100 mm)",
      "Joins plates (M3x12), builds frames and chassis extensions.", defines=['holes=10']),
    P("rail_5", "COMMON/connectors/rail.scad", "common", "Rail 1x5 (50 mm)", "Short rail / plate joiner.", defines=['holes=5']),
    P("corner_connector", "COMMON/connectors/corner_connector.scad", "common", "Corner connector (90° bracket)",
      "Stands plates/rails upright on the grid; holes stay on the lattice.",
      orient="Horizontal leg on the bed", infill="40 %"),
    P("thumb_nut", "COMMON/connectors/thumb_nut.scad", "common", "Thumb nut (M3)",
      "Hand-tightened M3 nut: tool-free joints and friction locks.", orient="Flat, hex pocket UP", infill="40 %"),
    P("motor_coupler", "COMMON/connectors/motor_coupler.scad", "common", "Motor coupler 2 mm -> 3 mm",
      "Connects a 2 mm motor shaft to a 3 mm kit shaft (drive or generator).",
      orient="Standing, 3 mm bore down", infill="100 %", material=PETG),
    P("vertical_support_48", "COMMON/mounts/vertical_support.scad", "common", "Vertical support / pillar 48 mm",
      "Gearbox frame spacer and solar-panel standoff (captive nuts both ends).",
      orient="Standing on an end", infill="40 %", defines=['pillar_len=48']),
    P("vertical_support_20", "COMMON/mounts/vertical_support.scad", "common", "Vertical support / pillar 20 mm",
      "Short standoff for raised mounts.", orient="Standing on an end", infill="40 %", defines=['pillar_len=20']),
    P("shaft_printed_40", "COMMON/shafts/shaft.scad", "common", "Printed shaft Ø3 x 40",
      "Light-duty stand-in for a 3 mm steel rod.", orient="Lying flat (flat side down)",
      infill="100 %", material=PETG, defines=['length=40']),
    P("shaft_printed_60", "COMMON/shafts/shaft.scad", "common", "Printed shaft Ø3 x 60", "Light-duty stand-in for steel rod.",
      orient="Lying flat (flat side down)", infill="100 %", material=PETG, defines=['length=60']),
    P("shaft_printed_80", "COMMON/shafts/shaft.scad", "common", "Printed shaft Ø3 x 80", "Light-duty stand-in for steel rod.",
      orient="Lying flat (flat side down)", infill="100 %", material=PETG, defines=['length=80']),
    P("shaft_printed_120", "COMMON/shafts/shaft.scad", "common", "Printed shaft Ø3 x 120", "Light-duty stand-in for steel rod.",
      orient="Lying flat (flat side down)", infill="100 %", material=PETG, defines=['length=120']),
    P("shaft_collar", "COMMON/shafts/shaft_collar.scad", "common", "Shaft collar",
      "Locks a shaft axially or spaces gears (M3 grub + nut).", infill="100 %"),
    P("bearing_mount", "COMMON/bearings/bearing_mount.scad", "common", "Bearing mount (pillow block, 625)",
      "Holds a 625 bearing / 623 via adapter / printed bushing at the standard axis height.",
      orient="Standing on its foot", infill="40 %"),
    P("bearing_insert_623", "COMMON/bearings/bearing_insert.scad", "common", "Bearing insert: 623 adapter ring",
      "Fits a 623 (3x10x4) bearing into the 16 mm pocket for 3 mm shafts.", infill="100 %", defines=['type="623"']),
    P("bearing_insert_bushing", "COMMON/bearings/bearing_insert.scad", "common", "Bearing insert: printed plain bushing",
      "No-bearing option: a plain bearing for a 3 mm shaft.", infill="100 %", material=PETG, defines=['type="bushing"']),
    P("axle_mount", "COMMON/mounts/axle_mount.scad", "common", "Axle mount (plain pillow block)",
      "Cheap 3 mm axle support at the standard axis height.", orient="Standing on its foot", infill="40 %"),
    P("motor_mount", "COMMON/mounts/motor_mount.scad", "common", "Motor mount (130-size, snap-in)",
      "Holds a 130 DC motor with its axis on the grid at the standard axis height.",
      orient="Standing on its floor", infill="30 %", material=PETG),
    P("gear_10T", "COMMON/gears/spur_gear.scad", "common", "Spur gear 10T m2 (hub, set screw)",
      "Pinion. Any gear meshes any gear when both shafts sit in grid holes.", orient="Flat, hub UP", infill="60 %",
      defines=['teeth=10', 'bore="fixed"']),
    P("gear_20T", "COMMON/gears/spur_gear.scad", "common", "Spur gear 20T m2", "2:1 against a 10T.", orient="Flat, hub UP",
      infill="40 %", defines=['teeth=20', 'bore="fixed"']),
    P("gear_30T", "COMMON/gears/spur_gear.scad", "common", "Spur gear 30T m2", "3:1 against a 10T.", orient="Flat, hub UP",
      infill="40 %", defines=['teeth=30', 'bore="fixed"']),
    P("gear_40T", "COMMON/gears/spur_gear.scad", "common", "Spur gear 40T m2", "4:1 against a 10T, windows to see through.",
      orient="Flat, hub UP", infill="30 %", defines=['teeth=40', 'bore="fixed"']),
    P("gear_20T_idler", "COMMON/gears/spur_gear.scad", "common", "Spur gear 20T m2, free-spinning (idler)",
      "Idler gear: changes direction, not speed.", orient="Flat, hub UP", infill="40 %", defines=['teeth=20', 'bore="free"']),
    P("gear_10T_motor", "COMMON/gears/spur_gear.scad", "common", "Motor pinion 10T (2 mm press fit)",
      "Pushes onto a 130 motor shaft.", orient="Flat, collar UP", infill="100 %", material=PETG,
      defines=['teeth=10', 'bore="motor"']),
    P("gear_20T_motor", "COMMON/gears/spur_gear.scad", "common", "Motor gear 20T (2 mm press fit)",
      "High-speed (overdrive) motor gear.", orient="Flat, collar UP", infill="60 %", material=PETG,
      defines=['teeth=20', 'bore="motor"']),
    P("wheel_60", "COMMON/wheels/wheel.scad", "common", "Wheel Ø60 (disc)",
      "Standard wheel, O-ring tyre groove, coupling holes for gears/pulleys.", orient="Flat, hub UP", infill="30 %",
      defines=['wheel_style="disc"']),
    P("solar_panel_frame", "COMMON/mounts/solar_panel_mount.scad", "common", "Solar panel frame (fixed/hinged)",
      "Holds a bought 110x69 panel; bolts to the grid or pivots in tilt brackets.",
      orient="Back DOWN (lips up)", infill="20 %"),
    P("solar_tilt_bracket", "COMMON/mounts/solar_tilt_bracket.scad", "common", "Solar panel tilt bracket",
      "Hinged mount with an engraved angle scale (print 2).", orient="Foot on the bed", infill="40 %"),
    # ------------------------------------------------------------------ SOLAR
    P("solar_vehicle_chassis", "SOLAR/vehicle/solar_vehicle_chassis.scad", "solar", "Solar vehicle chassis 170x80",
      "Grid chassis with gear slot; all common mounts bolt on.", orient="Flat, nut pockets DOWN", infill="15 %", kit="solar"),
    P("solar_vehicle_wheel", "SOLAR/vehicle/solar_vehicle_wheel.scad", "solar", "Solar vehicle wheel Ø60 (spoked)",
      "Lightweight version of the common wheel (same hub, tyre, holes).", orient="Flat, hub UP", infill="30 %", kit="solar"),
    P("solar_vehicle_motor_mount", "SOLAR/vehicle/solar_vehicle_motor_mount.scad", "solar",
      "Solar vehicle motor mount (slotted)",
      "Common motor cradle with ±4 mm slots to explore gear-mesh distance.", orient="Standing on its floor",
      infill="30 %", material=PETG, kit="solar"),
    # ------------------------------------------------------------------ DYNAMO
    P("hand_crank", "DYNAMO/hand_generator/hand_crank.scad", "dynamo", "Hand crank arm",
      "Crank with two set screws; knob at 20 or 30 mm radius.", orient="Flat face down, hub UP", infill="60 %",
      material=PETG, kit="dynamo"),
    P("crank_knob", "DYNAMO/hand_generator/crank_knob.scad", "dynamo", "Crank knob (free-spinning)",
      "Handle that turns freely on an M3 screw (hand generator, linkage lab).", orient="Standing, recess UP",
      infill="20 %", kit="dynamo"),
    P("generator_mount", "DYNAMO/hand_generator/generator_mount.scad", "dynamo", "Generator mount (axial)",
      "Holds a 130 motor as a generator, shaft into a grid hole via the coupler.", orient="Foot on the bed",
      infill="40 %", kit="dynamo"),
    P("dynamo_gear_guard", "DYNAMO/hand_generator/dynamo_gear_guard.scad", "dynamo", "Dynamo gearbox guard",
      "See-through finger guard over the gearbox (openings < 5 mm).",
      orient="As exported: lying on one lip face (U cross-section on the bed)", infill="15 %", kit="dynamo"),
    P("output_panel", "DYNAMO/hand_generator/output_panel.scad", "dynamo", "Generator output panel",
      "LED, buzzer, capacitor/meter/battery-module mounting via slots.", infill="20 %", kit="dynamo"),
    # ------------------------------------------------------------------ MECHANICAL
    P("gearbox_frame_plate", "MECHANICAL/gearbox/gearbox_frame_plate.scad", "mechanical", "Gearbox frame plate (lattice)",
      "See-through side plate; every grid point is a shaft bushing.", infill="30 %", kit="mechanical"),
    P("pulley_20", "MECHANICAL/pulley/pulley.scad", "mechanical", "Pulley Ø20", "Round-belt (O-ring) pulley.",
      orient="Flat, hub UP", infill="40 %", defines=['size=20'], kit="mechanical"),
    P("pulley_40", "MECHANICAL/pulley/pulley.scad", "mechanical", "Pulley Ø40", "Round-belt (O-ring) pulley.",
      orient="Flat, hub UP", infill="30 %", defines=['size=40'], kit="mechanical"),
    P("pulley_60", "MECHANICAL/pulley/pulley.scad", "mechanical", "Pulley Ø60", "Round-belt (O-ring) pulley.",
      orient="Flat, hub UP", infill="30 %", defines=['size=60'], kit="mechanical"),
    P("belt_pulley_mount", "MECHANICAL/pulley/belt_pulley_mount.scad", "mechanical", "Belt pulley mount (tensioner)",
      "Tall slotted axle mount: slide to tension the belt.", orient="Standing on its foot", infill="40 %", kit="mechanical"),
    P("link_bar_3", "MECHANICAL/linkage/link_bar.scad", "mechanical", "Link bar 3 holes (20 mm)", "Crank link.",
      infill="40 %", defines=['holes=3'], kit="mechanical"),
    P("link_bar_5", "MECHANICAL/linkage/link_bar.scad", "mechanical", "Link bar 5 holes (40 mm)", "Rocker link.",
      infill="40 %", defines=['holes=5'], kit="mechanical"),
    P("link_bar_6", "MECHANICAL/linkage/link_bar.scad", "mechanical", "Link bar 6 holes (50 mm)", "Coupler link.",
      infill="40 %", defines=['holes=6'], kit="mechanical"),
    # ------------------------------------------------------------------ WIND
    P("turbine_hub_2", "WIND/turbine/turbine_hub.scad", "wind", "Turbine hub, 2 blades",
      "Adjustable-pitch hub.", orient="Flat, hub UP", infill="40 %", defines=['blades=2'], kit="wind"),
    P("turbine_hub_3", "WIND/turbine/turbine_hub.scad", "wind", "Turbine hub, 3 blades",
      "Adjustable-pitch hub.", orient="Flat, hub UP", infill="40 %", defines=['blades=3'], kit="wind"),
    P("turbine_hub_4", "WIND/turbine/turbine_hub.scad", "wind", "Turbine hub, 4 blades",
      "Adjustable-pitch hub.", orient="Flat, hub UP", infill="40 %", defines=['blades=4'], kit="wind"),
    P("turbine_blade_standard", "WIND/turbine/turbine_blade.scad", "wind", "Turbine blade, standard",
      "Flat safe-edge blade, pitch set in the hub.", infill="15 %", defines=['style="standard"'], kit="wind"),
    P("turbine_blade_torque", "WIND/turbine/turbine_blade.scad", "wind", "Turbine blade, high-torque (wide)",
      "Starts in light wind, strong but slow.", infill="15 %", defines=['style="torque"'], kit="wind"),
    P("turbine_blade_speed", "WIND/turbine/turbine_blade.scad", "wind", "Turbine blade, high-speed (narrow)",
      "Spins fast in strong wind.", infill="15 %", defines=['style="speed"'], kit="wind"),
    P("turbine_tower_segment", "WIND/turbine/turbine_tower.scad", "wind", "Turbine tower segment 100 mm",
      "Stackable C-channel tower; any common mount bolts on top.",
      orient="Standing, bottom flange on the bed (top flange bridges)", infill="20 %", kit="wind"),
]

# Quantities used by the MVP builds (for the BOM)
KIT_QTY = {
    "Solar vehicle (Kit 4, version B)": {
        "solar_vehicle_chassis": 1, "solar_vehicle_wheel": 4, "axle_mount": 4, "solar_vehicle_motor_mount": 1,
        "gear_10T_motor": 1, "gear_20T": 1, "vertical_support_48": 4, "solar_panel_frame": 1},
    "Hand-crank dynamo (Kit 2, all ratios)": {
        "base_plate_100": 1, "gearbox_frame_plate": 2, "vertical_support_48": 4, "corner_connector": 2,
        "gear_10T": 4, "gear_20T": 3, "gear_40T": 1, "hand_crank": 1, "crank_knob": 1, "generator_mount": 1,
        "motor_coupler": 1, "dynamo_gear_guard": 1, "output_panel": 1},
    "Wind turbine (Kit 5)": {
        "base_plate_100": 1, "turbine_tower_segment": 2, "motor_mount": 1, "motor_coupler": 1,
        "turbine_hub_2": 1, "turbine_hub_3": 1, "turbine_hub_4": 1,
        "turbine_blade_standard": 4, "turbine_blade_torque": 4, "turbine_blade_speed": 4},
    "Pulley lab (Kit 8 MVP)": {
        "base_plate_100": 1, "motor_mount": 1, "motor_coupler": 1, "bearing_mount": 1, "bearing_insert_bushing": 1,
        "axle_mount": 1, "belt_pulley_mount": 2, "pulley_20": 1, "pulley_40": 1, "pulley_60": 1},
    "Four-bar linkage (Kit 10 MVP)": {
        "base_plate_100": 1, "link_bar_3": 1, "link_bar_5": 1, "link_bar_6": 1, "crank_knob": 1},
    "Tilting solar panel stand": {
        "base_plate_100": 2, "rail_5": 2, "solar_panel_frame": 1, "solar_tilt_bracket": 2, "thumb_nut": 2},
}
