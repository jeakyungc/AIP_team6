import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request # Import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from pydantic import BaseModel
import uvicorn
import asyncio

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in a .env file.")

client = genai.Client(api_key=api_key)

app = FastAPI()

# Define the directory for static files and mount it
# Images will be saved in 'generated_images'
# They will be accessible via URLs like http://your_server:8000/image_gen/your_image.png
STATIC_FILES_DIR = "generated_images"
STATIC_URL_PATH = "/image_gen" # The URL path to access the static files

# Create the static files directory if it doesn't exist
os.makedirs(STATIC_FILES_DIR, exist_ok=True)

# Mount the static files directory
app.mount(STATIC_URL_PATH, StaticFiles(directory=STATIC_FILES_DIR), name="static_images")


# Global variables to store the loaded models
prompter_model = None
prompter_tokenizer = None

class PromptRequest(BaseModel):
    text_prompt: str

@app.on_event("startup")
async def startup_event():
    """Load Promptist model and tokenizer when the FastAPI app starts."""
    global prompter_model, prompter_tokenizer
    print("Loading Promptist model...")
    try:
        prompter_model = AutoModelForCausalLM.from_pretrained("microsoft/Promptist")
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        prompter_tokenizer = tokenizer
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Failed to load Promptist model: {e}")
        raise HTTPException(status_code=500, detail="Failed to load AI models at startup.")

def generate_optimized_prompt(plain_text: str) -> str:
    """Generate an optimized prompt using the Promptist model."""
    if prompter_model is None or prompter_tokenizer is None:
        raise HTTPException(status_code=500, detail="Promptist model not loaded.")

    input_ids = prompter_tokenizer(plain_text.strip()+" Rephrase:", return_tensors="pt").input_ids
    eos_id = prompter_tokenizer.eos_token_id
    outputs = prompter_model.generate(input_ids, do_sample=False, max_new_tokens=75, num_beams=8, num_return_sequences=8, eos_token_id=eos_id, pad_token_id=eos_id, length_penalty=-1.0)
    output_texts = prompter_tokenizer.batch_decode(outputs, skip_special_tokens=True)
    res = output_texts[0].replace(plain_text+" Rephrase:", "").strip()
    return res

# Helper function to wrap the synchronous call
def _sync_generate_content(model, contents, config):
    """Synchronous call to generate_content."""
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )

async def generate_image_with_gemini(prompt: str, filename: str):
    """
    Generate an image using Gemini and save it to the STATIC_FILES_DIR.
    Returns the filename (e.g., 'image_When_the_stars_threw_4a8232b9.png').
    """
    full_filepath = os.path.join(STATIC_FILES_DIR, filename) # Path where the file will be saved
    try:
        print(f"🎨 Generating image for prompt: '{prompt}'")
        
        response = await asyncio.to_thread(
            _sync_generate_content,
            model="gemini-2.0-flash-exp-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        image_saved = False
        for part in response.candidates[0].content.parts:
            if getattr(part, "text", None):
                print("📝 Generated text:", part.text)
            elif getattr(part, "inline_data", None):
                image_data = part.inline_data.data
                image = Image.open(BytesIO(image_data))
                image.save(full_filepath) # Save to the full path
                print(f"Image saved as: {full_filepath}")
                image_saved = True
        
        if not image_saved:
            print("No image was generated in the response")
            raise HTTPException(status_code=500, detail="Gemini did not generate an image.")
        
        return filename # Return just the filename, not the full path
            
    except Exception as e:
        print(f"Error generating image: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")

@app.post("/generate-image/")
async def create_image(request: PromptRequest, http_request: Request): # Add http_request: Request
    """
    Receives a text prompt, optimizes it using Promptist,
    and then generates an image using Gemini.
    Returns a URL to the generated image.
    """
    user_input = request.text_prompt
    if not user_input:
        raise HTTPException(status_code=400, detail="Text prompt cannot be empty.")

    print(f"\nReceived original prompt: '{user_input}'")
    print("Generating optimized prompt...")

    try:
        optimized_prompt = generate_optimized_prompt(user_input)
        print(f"Optimized prompt: '{optimized_prompt}')")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing prompt: {e}")

    # Generate a unique filename (just the name, not the path)
    timestamp = user_input.replace(" ", "_").replace(",", "")[:20]
    filename = f"image_{timestamp}_{os.urandom(4).hex()}.png"

    try:
        # generate_image_with_gemini now saves the image and returns just the filename
        saved_filename = await generate_image_with_gemini(optimized_prompt, filename)
        
        # Construct the full URL
        # http_request.base_url will give you "http://localhost:8000/" or "http://211.211.177.45:8000/"
        # We need to remove the trailing slash if present
        base_url_str = str(http_request.base_url).rstrip('/')
        image_url = f"{base_url_str}{STATIC_URL_PATH}/{saved_filename}"
        
        # Return a JSON response with the image URL
        return JSONResponse(
            content={
                "message": "Image generated and saved successfully!",
                "original_prompt": user_input,
                "optimized_prompt": optimized_prompt,
                "image_url": image_url
            },
            status_code=200
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)