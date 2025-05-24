import torch
from diffusers import StableDiffusionPipeline

# Load pipeline without safety checker
pipe = StableDiffusionPipeline.from_pretrained(
    "./dreambooth-model",  # or your model path
    torch_dtype=torch.float16,
    safety_checker=None,  # Disable safety checker
    requires_safety_checker=False,  # Don't require it
).to("cuda")

# Generate ER diagram
prompt = "a diagram of sks er model for user management system"
image = pipe(
    prompt,
    num_inference_steps=50,
    guidance_scale=7.5,
    num_images_per_prompt=1,
).images[0]

image.save("generated_er_diagram.png")
print("ER diagram generated successfully!")