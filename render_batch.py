import bpy
import os
import sys
import time

# Start the clock the exact second the script initializes
start_time = time.time()

# 5.5 hours in seconds (330 minutes). Gives a 30-minute safety buffer before the 6-hour limit.
MAX_ALLOWED_TIME = 330 * 60 

# Parse command line inputs
try:
    args = sys.argv[sys.argv.index("--") + 1:]
    start_frame = int(args[0])
    max_animation_frames = int(args[1])
except (ValueError, IndexError):
    start_frame = 1
    max_animation_frames = 100

# Calculate an large end frame boundary for the individual runner cycle
end_frame = start_frame + 1000 

print(f"Starting adaptive time batch from frame {start_frame}")

# Render Engine Performance Settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.05
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# FIX: Force the file output layout to an image type so write_still=True won't crash
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'

os.makedirs("./output", exist_ok=True)
last_rendered_frame = start_frame - 1

# Execute Loop
for frame in range(start_frame, end_frame + 1):
    # Condition A: We reached the end of your actual animation
    if frame > max_animation_frames:
        print("Reached the end of the total animation length!")
        break
        
    # Condition B: Check the clock BEFORE rendering the next frame
    elapsed_time = time.time() - start_time
    if elapsed_time > MAX_ALLOWED_TIME:
        print(f"⚠️ SAFETY TRIGGER: Script has run for {elapsed_time/60:.1f} minutes.")
        print(f"Stopping render early to prevent GitHub timeout. Next start frame needs to be: {frame}")
        break

    # Execute the individual frame render
    scene.frame_set(frame)
    scene.render.filepath = os.path.abspath(f"./output/frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    last_rendered_frame = frame

# Write the next starting frame to a temporary text file so GitHub Actions can read it
with open("next_frame.txt", "w") as f:
    f.write(str(last_rendered_frame + 1))

print("Batch cycle safely completed.")
