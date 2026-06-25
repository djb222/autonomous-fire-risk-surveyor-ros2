import os
import re
import math
import time
import random
import sys

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORLD_PATH = os.path.join(SCRIPT_DIR, "large_demo.sdf")

# Hotspot parameters
HOTSPOT_RADIUS = 0.2
HOTSPOT_HEIGHT = 0.005
MIN_DISTANCE = 1.0
WORLD_BOUNDS_X = (-6, 6)
WORLD_BOUNDS_Y = (-6, 6)
SPAWN_Z = HOTSPOT_HEIGHT / 2  

random.seed(time.time())

# Translucent-to-opaque red scale
COLOUR_MAP = {
    1: (1.00, 0.00, 0.06, 0.50),
    2: (1.00, 0.00, 0.06, 0.55),
    3: (1.00, 0.00, 0.06, 0.60),
    4: (1.00, 0.00, 0.06, 0.65),
    5: (1.00, 0.00, 0.06, 0.70),
    6: (1.00, 0.00, 0.06, 0.75),
    7: (1.00, 0.00, 0.06, 0.80),
    8: (1.00, 0.00, 0.06, 0.85),
    9: (1.00, 0.00, 0.06, 0.90),
    10: (1.00, 0.00, 0.06, 1.00),
}

# Utility functions
def intensity_to_colour(intensity):
    r, g, b, a = COLOUR_MAP[intensity]
    return f"{r:.2f} {g:.2f} {b:.2f} {a:.2f}"

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def is_valid_position(new_pos, existing_positions):
    return all(distance(new_pos, pos) >= MIN_DISTANCE for pos in existing_positions)

# Read number of hotspots from stdin (GUI sends this)
try:
    num_hotspots = int(sys.stdin.readline().strip())
    if not (1 <= num_hotspots <= 10):
        raise ValueError
except (ValueError, EOFError):
    raise RuntimeError("Invalid number of hotspots received from GUI")

# Generate random positions
hotspots = []
used_intensities = set()
attempts = 0

while len(hotspots) < num_hotspots and attempts < 5000:
    x = random.uniform(*WORLD_BOUNDS_X)
    y = random.uniform(*WORLD_BOUNDS_Y)
    available = [i for i in range(1, 11) if i not in used_intensities]

    if not available:
        break

    intensity = random.choice(available)
    if is_valid_position((x, y), [(h[0], h[1]) for h in hotspots]):
        hotspots.append((x, y, intensity))
        used_intensities.add(intensity)
    attempts += 1

if len(hotspots) < num_hotspots:
    raise RuntimeError("Could not find enough valid positions for hotspots.")

# PRINT hotspot info for GUI
for i, (x, y, intensity) in enumerate(hotspots, 1):
    print(f"Hotspot {i}: ({x:.2f}, {y:.2f}) intensity {intensity}/10")

# Modify world file (replace previous hotspot_* models)
with open(WORLD_PATH, "r", encoding="utf-8") as f:
    world_text = f.read()

world_text = re.sub(
    r"\s*<model name='hotspot_\d+'>.*?</model>\s*",
    "",
    world_text,
    flags=re.DOTALL,
)

insert_index = world_text.find("</world>")
if insert_index == -1:
    raise RuntimeError("Could not find </world> tag in SDF file.")

sdf_models = ""
for i, (x, y, intensity) in enumerate(hotspots, 1):
    colour = intensity_to_colour(intensity)
    sdf_models += f"""
    <model name='hotspot_{i}'>
      <pose>{x:.2f} {y:.2f} {SPAWN_Z:.3f} 0 0 0</pose>
      <static>true</static>
      <link name='link'>
        <visual name='visual'>
          <geometry>
            <cylinder>
              <radius>{HOTSPOT_RADIUS}</radius>
              <length>{HOTSPOT_HEIGHT}</length>
            </cylinder>
          </geometry>
          <material>
            <ambient>{colour}</ambient>
            <diffuse>{colour}</diffuse>
          </material>
        </visual>
        <collision name='collision'>
          <geometry>
            <cylinder>
              <radius>{HOTSPOT_RADIUS}</radius>
              <length>{HOTSPOT_HEIGHT}</length>
            </cylinder>
          </geometry>
        </collision>
      </link>
    </model>
    """

updated_world = world_text[:insert_index] + sdf_models + "\n" + world_text[insert_index:]

with open(WORLD_PATH, "w", encoding="utf-8") as f:
    f.write(updated_world)
