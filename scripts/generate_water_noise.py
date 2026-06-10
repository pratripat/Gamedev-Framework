"""
Generate tileable water noise frames and save them to data/graphics/generated_water_<ts>/frame_*.png
Usage: python3 scripts/generate_water_noise.py
"""
import os
import time
import pygame
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# ensure project root on import path so `scripts` package is importable
sys.path.insert(0, str(PROJECT_ROOT))

# Import the generator
from scripts.utils.water_animator import generate_tileable_noise_frames, generate_tileable_worley_frames

OUT_DIR = PROJECT_ROOT / 'data' / 'graphics'
TS = int(time.time())
SAVE_DIR = OUT_DIR / f'generated_water_{TS}'

os.makedirs(SAVE_DIR, exist_ok=True)

print('Initializing pygame...')
pygame.init()
# Some pygame surface ops require a display mode; use a tiny hidden surface
try:
    pygame.display.init()
    pygame.display.set_mode((1,1))
except Exception:
    pass

# Parameters (tweak as needed)
# Force tile size 32 as requested
SIZE = 32
NUM_FRAMES = 12
CELLS = 4
BASE_COLOR = (30, 140, 220)
INTENSITY = 0.7
SEED = 1234

print(f'Generating {NUM_FRAMES} frames, size={SIZE}, cells={CELLS} -> {SAVE_DIR}')
frames = generate_tileable_worley_frames(size=SIZE, num_frames=NUM_FRAMES, cells=CELLS, base_color=BASE_COLOR, intensity=INTENSITY, seed=SEED)

for i, f in enumerate(frames):
    fname = SAVE_DIR / f'frame_{i:03d}.png'
    pygame.image.save(f, str(fname))
    print('Saved', fname)

print('Done. You can slice these frames into tiles for your tilemap.')

pygame.quit()
