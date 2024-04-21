from datetime import datetime
from cnc_hole_lib import get_gcode

variables = {
    'platform': 'snapmaker',
    'holes_coords': [
        {'id': 1, 'X': 1.0, 'Y': 2.0},
        {'id': 2, 'X': 3.0, 'Y': 4.0},
        {'id': 3, 'X': 5.0, 'Y': 6.0},
    ],
    'idling_h': 30.0,
    'X_max': 30.0,
    'Y_max': 30.0,
    'lift_h': 1.0,
    'lowering_iters': 4,
    'depth_material': 1.0,
    'depth_step': 0.05,
    'current_date': datetime.now().strftime("%a %b %d %Y %H:%M:%S")
}

print(get_gcode(variables))