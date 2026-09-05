import bpy
import os
import sys
import time

# Start the clock the exact second the script initializes
session_start = time.time()

# Hard cutoff at 5 hours and 50 minutes (350 minutes) to leave a strict 10-minute export window
CUTOFF_LIMIT = 350 * 60 

# Parse command line inputs correctly by accessing individual list indexes
try:
    # Look for the '--' flag which separates Blender args from script args
    args = sys.argv[sys.argv.index("--") + 1:]
    start_frame = int(args[0])              # FIX: Get the first item in the list
    max_animation_frames = int(args[1])     # FIX: Get the second item in the list
except (ValueError, IndexError, TypeError):
    # Fallback defaults if the arguments are missing or malformed
    start_frame = 1
    max_animation_frames = 100

# Set a large theoretical boundary for this specific run
end_frame = start_frame + 1000 

print(f"Starting predictive time batch from frame {start_frame}")

# Render Engine Performance Settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.05
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Force the top-level property structure out of Video mode into Image mode first
scene.render.image_settings.file_format = 'PNG'
try:
    scene.render.image_settings.color_mode = 'RGBA'
except TypeError:
    scene.render.image_settings.color_mode = 'RGB'

os.makedirs("./output", exist_ok=True)
last_rendered_frame = start_frame - 1

# Performance tracking variables
total_render_time = 0
frames_rendered_this_session = 0
avg_frame_time = 0

# Execute Loop
for frame in range(start_frame, end_frame + 1):
    # Condition A: We reached the target animation length
    if frame > max_animation_frames:
        print("Reached the end of the total animation length!")
        break
        
    # Condition B: Predictive Time Check
    elapsed_time = time.time() - session_start
    
    predicted_next_frame_cost = avg_frame_time if frames_rendered_this_session > 0 else (5 * 60)
    
    if (elapsed_time + predicted_next_frame_cost) > CUTOFF_LIMIT:
        print(f"\n⚠️ PREDICTIVE SAFETY TRIGGER:")
        print(f"Elapsed Time: {elapsed_time/60:.2f} mins. Avg Frame Time: {avg_frame_time/60:.2f} mins.")
        print(f"Next frame would likely finish at {(elapsed_time + predicted_next_frame_cost)/60:.2f} mins.")
        print(f"Stopping render now to guarantee a 10+ minute file export window.")
        print(f"Next start frame will be: {frame}")
        break

    # Execute the individual frame render and time it
    frame_start = time.time()
    
    scene.frame_set(frame)
    scene.render.filepath = os.path.abspath(f"./output/frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
    
    frame_end = time.time()
    
    # Update running render averages
    frame_duration = frame_end - frame_start
    total_render_time += frame_duration
    frames_rendered_this_session += 1
    avg_frame_time = total_render_time / frames_rendered_this_session
    
    last_rendered_frame = frame
    print(f"Frame {frame:04d} done in {frame_duration:.1f}s (Avg: {avg_frame_time:.1f}s)")

# Write the precise next frame to a text file for GitHub Actions to read
with open("next_frame.txt", "w") as f:
    f.write(str(last_rendered_frame + 1))

print("Batch cycle safely completed.")
