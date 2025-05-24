import torch
from diffusers import StableDiffusionPipeline

# Option 1: Use original Stable Diffusion v1.5 (most common base model)
model_id = "runwayml/stable-diffusion-v1-5"

# Option 2: Alternative base models you can try:
# model_id = "stabilityai/stable-diffusion-2-1"
# model_id = "stabilityai/stable-diffusion-xl-base-1.0"  # SDXL (requires more VRAM)
# model_id = "CompVis/stable-diffusion-v1-4"

# Load the base pipeline
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    safety_checker=None,  # Disable safety checker
    requires_safety_checker=False,  # Don't require it
).to("cuda")

# Generate ER diagram with base model (removed 'sks' token)
prompt = "a diagram of sks er model for user management system"

image = pipe(
    prompt,
    num_inference_steps=50,
    guidance_scale=7.5,
    num_images_per_prompt=1,
).images[0]

image.save("base_model_er_diagram.png")
print("ER diagram generated successfully using base model!")
