import bpy
import os
import sys

# Parse the arguments from the command line
try:
    args = sys.argv[sys.argv.index("--") + 1:]
    start_frame = int(args[0])
    max_animation_frames = int(args[1])
except (ValueError, IndexError):
    # Fallback defaults if something goes wrong
    start_frame = 1
    max_animation_frames = 100   

end_frame = start_frame + 9  

print(f"Rendering {bpy.data.filepath}")
print(f"Batch Range: Frame {start_frame} to {end_frame} (Total target: {max_animation_frames})")

# Performance Optimizations
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32                
scene.cycles.use_adaptive_sampling = True 
scene.cycles.adaptive_threshold = 0.05   
scene.cycles.caustics_reflective = False 
scene.cycles.caustics_refractive = False
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Execute Loop
os.makedirs("./output", exist_ok=True)
for frame in range(start_frame, end_frame + 1):
    if frame > max_animation_frames:
        print(f"Frame {frame} exceeds total animation limit of {max_animation_frames}. Stopping.")
        break
    scene.frame_set(frame)
    scene.render.filepath = os.path.abspath(f"./output/frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)

print("Batch processing complete.")
