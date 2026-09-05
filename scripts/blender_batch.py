import bpy
import os
import sys
import time

session_start = time.time()
CUTOFF_LIMIT = 345 * 60  # 5 hours 45 minutes safety cutoff

# Parse CLI Arguments
try:
    args = sys.argv[sys.argv.index("--") + 1:]
    start_frame = int(args[0])
    end_frame = int(args[1])
    samples = int(args[2])
    enable_denoise = args[3].lower() == 'true'
except (ValueError, IndexError):
    print("Argument parsing failed. Using defaults.")
    start_frame, end_frame, samples, enable_denoise = 1, 1, 32, True

print(f"--- Rendering Frames {start_frame} to {end_frame} ---")

scene = bpy.context.scene

# Core Render Settings
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = samples

# RAM Protections (Crucial for GitHub Actions 7GB limit)
scene.cycles.use_auto_tile = True
scene.cycles.tile_size = 256
scene.render.use_simplify = True
scene.render.simplify_child_particles = 0.5

# Enable Persistent Data if processing multiple frames in this run
if start_frame != end_frame:
    scene.render.use_persistent_data = True

# Denoising
scene.cycles.use_denoising = enable_denoise
if enable_denoise:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Ensure Output Format is correct
if hasattr(scene.render.image_settings, 'media_type'):
    scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

# Suppress missing file errors halting the render
for img in bpy.data.images:
    if img.source == 'FILE' and not img.has_data:
        img.source = 'GENERATED'

os.makedirs("./output", exist_ok=True)

# Render Loop
for frame in range(start_frame, end_frame + 1):
    if (time.time() - session_start) > CUTOFF_LIMIT:
        print("⚠️ Safety trigger hit: Time limit approaching. Halting job.")
        break
        
    frame_start_time = time.time()
    
    scene.frame_set(frame)
    scene.render.filepath = os.path.abspath(f"./output/frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    
    print(f"Frame {frame:04d} completed in {time.time() - frame_start_time:.1f}s")

print("Chunk processing finished successfully.")
