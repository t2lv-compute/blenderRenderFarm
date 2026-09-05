import bpy
import os
import sys
import time

# Start clock tracking
session_start = time.time()
CUTOFF_LIMIT = 350 * 60  # 5 hours 50 minutes safety limit

# Parse Command Line Arguments
# Syntax: blender -b file.blend -P render_batch.py -- <start> <end> <samples> <max_bounces> <enable_denoise>
try:
    args = sys.argv[sys.argv.index("--") + 1:]
    start_frame = int(args[0])
    max_animation_frames = int(args[1])
    samples = int(args[2]) if len(args) > 2 else 32
    max_bounces = int(args[3]) if len(args) > 3 else 4
    enable_denoise = args[4].lower() == 'true' if len(args) > 4 else True
except (ValueError, IndexError, TypeError):
    start_frame, max_animation_frames = 1, 100
    samples, max_bounces, enable_denoise = 32, 4, True

print(f"--- Starting Render Batch ---")
print(f"Frames: {start_frame} to {max_animation_frames} | Samples: {samples} | Max Bounces: {max_bounces} | Denoise: {enable_denoise}")

scene = bpy.context.scene

# Configure Cycles Engine
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.05

# Speed Optimization: Cap Ray Bounces
scene.cycles.max_bounces = max_bounces
scene.cycles.diffuse_bounces = min(2, max_bounces)
scene.cycles.glossy_bounces = min(2, max_bounces)
scene.cycles.transmission_bounces = min(2, max_bounces)

# Speed Optimization: Cache Data in RAM across frames
scene.render.use_persistent_data = True

# Denoising Settings
if enable_denoise:
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
else:
    scene.cycles.use_denoising = False

# Fix Image Format Lockouts
try:
    scene.render.image_settings.file_format = 'PNG'
except TypeError:
    bpy.context.scene.render.image_settings.file_format = 'PNG'

scene.render.image_settings.color_mode = 'RGBA'

# Texture Caching & Missing Image Handling (Prevents per-frame disk searching)
try:
    bpy.ops.file.pack_all()
except Exception:
    pass

for img in bpy.data.images:
    if img.source == 'FILE' and not img.has_data:
        # Prevent Blender from repeatedly probing missing disk paths per frame
        img.source = 'GENERATED'

os.makedirs("./output", exist_ok=True)
last_rendered_frame = start_frame - 1

total_render_time = 0
frames_rendered_this_session = 0
avg_frame_time = 0

# Execution Loop
for frame in range(start_frame, max_animation_frames + 1):
    elapsed_time = time.time() - session_start
    predicted_next_frame_cost = avg_frame_time if frames_rendered_this_session > 0 else (5 * 60)
    
    if (elapsed_time + predicted_next_frame_cost) > CUTOFF_LIMIT:
        print(f"\n⚠️ PREDICTIVE SAFETY TRIGGER: Halting run to preserve export window.")
        break

    frame_start = time.time()
    
    scene.frame_set(frame)
    scene.render.filepath = os.path.abspath(f"./output/frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    
    frame_end = time.time()
    
    frame_duration = frame_end - frame_start
    total_render_time += frame_duration
    frames_rendered_this_session += 1
    avg_frame_time = total_render_time / frames_rendered_this_session
    
    last_rendered_frame = frame
    print(f"Frame {frame:04d} done in {frame_duration:.1f}s (Avg: {avg_frame_time:.1f}s)")

with open("next_frame.txt", "w") as f:
    f.write(str(last_rendered_frame + 1))

print("Batch chunk completed.")
# Add this right after the 'for frame in range(...)' loop ends:
if frames_rendered_this_session > 0:
    print(f"\n--- Chunk Summary ---")
    print(f"Total Frames Rendered: {frames_rendered_this_session}")
    print(f"Average Secs Per Frame: {avg_frame_time:.2f}s")
